#!/usr/bin/env python3
"""
discovery-scan.py — Veille automatique claudekit
Fetche les sources, détecte les nouveautés, génère un rapport.

Usage:
    python3 scripts/discovery-scan.py [--dry-run] [--output PATH]

Env vars:
    ANTHROPIC_API_KEY — requis pour l'analyse Claude
    GITHUB_TOKEN — optionnel, augmente la rate limit GitHub
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SEEN_FILE = REPO_ROOT / ".template" / "discovery-seen.json"
PENDING_FILE = REPO_ROOT / "pending-features.md"

SOURCES = {
    "claude-code-changelog": "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md",
    "awesome-claude-code": "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/main/README.md",
    "github-trending-mcp": "https://api.github.com/search/repositories?q=topic:claude-code+topic:mcp&sort=updated&per_page=20",
    "claude-code-releases": "https://api.github.com/repos/anthropics/claude-code/releases?per_page=5",
    "awesome-mcp-servers": "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md",
}

FETCH_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _build_request(url: str) -> urllib.request.Request:
    """Build a request with optional GitHub auth header."""
    headers = {"User-Agent": "claudekit-discovery/1.0"}
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {github_token}"
    return urllib.request.Request(url, headers=headers)


def fetch_sources() -> dict:
    """Fetch all configured sources. Returns {source_name: content_str}."""
    results = {}
    for name, url in SOURCES.items():
        try:
            req = _build_request(url)
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
                raw = resp.read()
                # GitHub API returns JSON; raw text sources return plain text
                content_type = resp.headers.get("Content-Type", "")
                if "json" in content_type or url.endswith(".json") or "api.github.com" in url:
                    data = json.loads(raw)
                    # Flatten JSON to readable text for Claude
                    results[name] = _flatten_json(name, data)
                else:
                    results[name] = raw.decode("utf-8", errors="replace")
            print(f"[discovery] fetched {name} ({len(results[name])} chars)")
        except urllib.error.HTTPError as exc:
            print(f"[discovery] HTTP {exc.code} fetching {name} ({url}) — skipping")
        except urllib.error.URLError as exc:
            print(f"[discovery] URLError fetching {name}: {exc.reason} — skipping")
        except Exception as exc:  # noqa: BLE001
            print(f"[discovery] Error fetching {name}: {exc} — skipping")
    return results


def _flatten_json(source_name: str, data) -> str:
    """Convert GitHub API JSON into readable text summaries."""
    lines = [f"=== {source_name} ==="]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key in ("name", "full_name", "description", "tag_name", "body", "html_url"):
                    if item.get(key):
                        lines.append(f"{key}: {item[key]}")
                lines.append("---")
    elif isinstance(data, dict):
        lines.append(json.dumps(data, indent=2)[:3000])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Seen-items persistence
# ---------------------------------------------------------------------------

def load_seen_items() -> set:
    """Load already-processed item IDs from .template/discovery-seen.json."""
    if not SEEN_FILE.exists():
        return set()
    try:
        data = json.loads(SEEN_FILE.read_text())
        return set(data.get("seen_ids", []))
    except Exception as exc:  # noqa: BLE001
        print(f"[discovery] Could not read seen file: {exc}")
        return set()


def save_seen_items(items: set) -> None:
    """Persist seen item IDs to .template/discovery-seen.json."""
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing: set = load_seen_items()
    merged = existing | items
    payload = {
        "seen_ids": sorted(merged),
        "last_scan": datetime.now(timezone.utc).isoformat(),
    }
    SEEN_FILE.write_text(json.dumps(payload, indent=2))
    print(f"[discovery] saved {len(merged)} seen IDs to {SEEN_FILE}")


# ---------------------------------------------------------------------------
# Claude API analysis
# ---------------------------------------------------------------------------

def analyze_with_claude(content: str) -> list:
    """
    Send aggregated source content to Claude Haiku for analysis.
    Returns a list of discovery dicts.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("[discovery] ANTHROPIC_API_KEY manquant, skip analyse Claude")
        return []

    payload = {
        "model": "claude-opus-4-6",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Tu es un expert Claude Code. Analyse ces sources et identifie les 5-10 "
                    "nouveautés les plus impactantes pour améliorer un template Claude Code "
                    "universel (claudekit).\n\n"
                    f"SOURCES:\n{content[:15000]}\n\n"
                    "Réponds UNIQUEMENT avec un JSON valide, tableau d'objets:\n"
                    "[\n"
                    "  {\n"
                    '    "id": "slug-court-unique",\n'
                    '    "title": "Titre court",\n'
                    '    "source": "nom de la source",\n'
                    '    "category": "hook|mcp|workflow|agent|skill|cli|security|other",\n'
                    '    "impact": "high|medium|low",\n'
                    '    "implementation_effort": "small|medium|large",\n'
                    '    "description": "Description en 1-2 phrases de ce que c\'est et pourquoi '
                    "c'est utile pour claudekit\",\n"
                    '    "implementation_hint": "Comment l\'intégrer concrètement (1 phrase)"\n'
                    "  }\n"
                    "]\n\n"
                    "Filtre : seulement ce qui n'est PAS déjà dans un template Claude Code standard. "
                    "Priorise ce qui est actionnable immédiatement."
                ),
            }
        ],
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            text = result["content"][0]["text"]
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                discoveries = json.loads(match.group())
                print(f"[discovery] Claude identified {len(discoveries)} items")
                return discoveries
            else:
                print("[discovery] Claude response contained no JSON array")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[discovery] Claude API HTTP {exc.code}: {body[:300]}")
    except Exception as exc:  # noqa: BLE001
        print(f"[discovery] Claude API error: {exc}")
    return []


# ---------------------------------------------------------------------------
# pending-features.md update
# ---------------------------------------------------------------------------

_SECTION_HEADER = "## En attente de review"
_PLACEHOLDER = "<!-- Les nouvelles découvertes apparaissent ici automatiquement -->"


def _format_item(item: dict) -> str:
    """Format a discovery dict as a pending-features.md checkbox line."""
    category = item.get("category", "other").upper()
    impact = item.get("impact", "medium").upper()
    title = item.get("title", "Untitled")
    description = item.get("description", "")
    source = item.get("source", "unknown")
    effort = item.get("implementation_effort", "medium")
    slug = item.get("id", "unknown")
    return (
        f"- [ ] **[{category}/{impact}]** {title} — {description} "
        f"*Source: {source}. Effort: {effort}.* `id:{slug}`"
    )


def update_pending_features(discoveries: list, dry_run: bool = False) -> int:
    """
    Prepend new discovery items to the 'En attente de review' section.
    Skips items whose ID is already in seen_ids.
    Returns the count of items actually added.
    """
    if not discoveries:
        print("[discovery] No discoveries to add")
        return 0

    seen = load_seen_items()
    new_items = [d for d in discoveries if d.get("id") and d["id"] not in seen]

    if not new_items:
        print("[discovery] All discoveries already seen — nothing to add")
        return 0

    # Read or initialise pending-features.md
    if PENDING_FILE.exists():
        content = PENDING_FILE.read_text()
    else:
        content = _initial_pending_features()

    # Build lines to insert
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    new_lines = [f"\n<!-- scan: {date_str} -->"]
    for item in new_items:
        new_lines.append(_format_item(item))
    insert_block = "\n".join(new_lines) + "\n"

    # Insert after the placeholder comment (or after the section header)
    if _PLACEHOLDER in content:
        content = content.replace(_PLACEHOLDER, _PLACEHOLDER + insert_block)
    elif _SECTION_HEADER in content:
        content = content.replace(
            _SECTION_HEADER, _SECTION_HEADER + "\n" + insert_block
        )
    else:
        # Append a new section at the end
        content += f"\n\n{_SECTION_HEADER}\n{insert_block}"

    if dry_run:
        print("[discovery] --dry-run: would write the following to pending-features.md:")
        print(insert_block)
    else:
        PENDING_FILE.write_text(content)
        print(f"[discovery] added {len(new_items)} items to {PENDING_FILE}")
        # Persist the new IDs
        save_seen_items({d["id"] for d in new_items})

    return len(new_items)


def _initial_pending_features() -> str:
    return """\
# Pending Features — claudekit

> Découvertes automatiques par `scripts/discovery-scan.py` (scan hebdomadaire).
> Cocher une box = accepté pour implémentation → lancer `/implement-discovery <id>`.
> Supprimer une ligne = rejeté.

## En attente de review

<!-- Les nouvelles découvertes apparaissent ici automatiquement -->

## Accepté — à implémenter

<!-- Déplacer ici les items cochés, ou laisser Claude le faire via /implement-discovery -->

## Implémenté

<!-- Archive des features intégrées -->
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    dry_run = "--dry-run" in sys.argv
    output_path: str | None = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    if dry_run:
        print("[discovery] DRY RUN — no files will be modified")

    print(f"[discovery] starting scan at {datetime.now(timezone.utc).isoformat()}")

    # 1. Fetch all sources
    sources = fetch_sources()
    if not sources:
        print("[discovery] no sources could be fetched — aborting")
        sys.exit(1)

    # 2. Aggregate content for Claude
    aggregated = "\n\n".join(
        f"### SOURCE: {name} ###\n{body}" for name, body in sources.items()
    )

    # Optionally save aggregated content for inspection
    if output_path:
        Path(output_path).write_text(aggregated)
        print(f"[discovery] raw aggregated content written to {output_path}")

    # 3. Analyse with Claude
    discoveries = analyze_with_claude(aggregated)

    # 4. Filter already-seen and update pending-features.md
    added = update_pending_features(discoveries, dry_run=dry_run)

    print(
        f"[discovery] done — {len(sources)} sources fetched, "
        f"{len(discoveries)} items identified, {added} new items added"
    )


if __name__ == "__main__":
    main()
