#!/usr/bin/env python3
"""
changelog-gen.py — Generate CHANGELOG.md entries from git log.

Follows Keep a Changelog format (https://keepachangelog.com).
Parses Conventional Commits (https://www.conventionalcommits.org).

Usage:
    python3 scripts/changelog-gen.py                    # since last tag
    python3 scripts/changelog-gen.py --since v1.2.3    # since specific tag
    python3 scripts/changelog-gen.py --version 1.3.0   # set release version
    python3 scripts/changelog-gen.py --append           # append to CHANGELOG.md
    python3 scripts/changelog-gen.py --unreleased       # mark as [Unreleased]
"""

import subprocess
import sys
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"

# Conventional commits → changelog sections
TYPE_MAP = {
    "feat":     "Added",
    "feature":  "Added",
    "fix":      "Fixed",
    "bugfix":   "Fixed",
    "hotfix":   "Fixed",
    "refactor": "Changed",
    "perf":     "Changed",
    "change":   "Changed",
    "update":   "Changed",
    "remove":   "Removed",
    "delete":   "Removed",
    "security": "Security",
    "sec":      "Security",
    "docs":     "Documentation",
    "doc":      "Documentation",
    "deprecate": "Deprecated",
    "dep":      "Deprecated",
}

SECTION_ORDER = ["Added", "Changed", "Fixed", "Removed", "Security", "Deprecated", "Documentation"]


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    return result.stdout.strip()


def get_last_tag() -> str | None:
    tag = run("git describe --tags --abbrev=0 2>/dev/null")
    return tag if tag else None


def get_commits_since(since: str | None) -> list[dict]:
    """Get commits since tag or from beginning."""
    if since:
        range_spec = f"{since}..HEAD"
    else:
        range_spec = "HEAD"

    # Format: hash|type(scope): description|full subject
    log = run(f'git log {range_spec} --pretty=format:"%H|%s|%b---COMMIT_END---"')

    if not log:
        return []

    commits = []
    for raw in log.split("---COMMIT_END---"):
        raw = raw.strip()
        if not raw:
            continue

        parts = raw.split("|", 2)
        if len(parts) < 2:
            continue

        commit_hash = parts[0].strip()
        subject = parts[1].strip()
        body = parts[2].strip() if len(parts) > 2 else ""

        commits.append({
            "hash": commit_hash[:8],
            "subject": subject,
            "body": body,
        })

    return commits


def parse_conventional_commit(commit: dict) -> dict:
    """Parse conventional commit format: type(scope)!: description"""
    subject = commit["subject"]

    # Match: type(scope)!: description  OR  type!: description  OR  type: description
    pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?\s*:\s*(.+)$'
    match = re.match(pattern, subject)

    if not match:
        return {
            "type": "other",
            "scope": None,
            "breaking": False,
            "description": subject,
            "section": None,
            "hash": commit["hash"],
        }

    commit_type = match.group(1).lower()
    scope = match.group(2)
    breaking = match.group(3) == "!" or "BREAKING CHANGE" in commit.get("body", "")
    description = match.group(4)

    section = TYPE_MAP.get(commit_type)

    if breaking:
        section = "Breaking Changes"

    return {
        "type": commit_type,
        "scope": scope,
        "breaking": breaking,
        "description": description,
        "section": section,
        "hash": commit["hash"],
    }


def format_entry(parsed: dict) -> str:
    """Format a single changelog entry."""
    scope_part = f"**{parsed['scope']}**: " if parsed["scope"] else ""
    return f"- {scope_part}{parsed['description']} ({parsed['hash']})"


def generate_changelog_entry(version: str, commits: list[dict], unreleased: bool = False) -> str:
    """Generate a CHANGELOG.md section."""
    parsed_commits = [parse_conventional_commit(c) for c in commits]

    # Group by section
    sections: dict[str, list[str]] = {}
    for parsed in parsed_commits:
        section = parsed["section"]
        if section is None:
            continue  # skip chore, ci, test, style commits
        if section not in sections:
            sections[section] = []
        sections[section].append(format_entry(parsed))

    if not sections:
        return ""

    # Build header
    if unreleased:
        header = "## [Unreleased]"
    else:
        today = date.today().isoformat()
        header = f"## [{version}] - {today}"

    lines = [header, ""]

    # Breaking changes first
    if "Breaking Changes" in sections:
        lines.append("### Breaking Changes")
        lines.extend(sections["Breaking Changes"])
        lines.append("")

    # Then in canonical order
    for section_name in SECTION_ORDER:
        if section_name in sections:
            lines.append(f"### {section_name}")
            lines.extend(sections[section_name])
            lines.append("")

    return "\n".join(lines)


def append_to_changelog(entry: str):
    """Insert entry after the first line (# Changelog header)."""
    if not CHANGELOG.exists():
        CHANGELOG.write_text("# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n")

    content = CHANGELOG.read_text()
    lines = content.split("\n")

    # Find position after the header and description
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            # Find the next non-empty line after the header
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or not lines[j].startswith("## ")):
                j += 1
            insert_pos = j
            break

    new_lines = lines[:insert_pos] + [""] + entry.strip().split("\n") + [""] + lines[insert_pos:]
    CHANGELOG.write_text("\n".join(new_lines))
    print(f"Appended to {CHANGELOG}")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    # Parse flags
    since = None
    version = None
    should_append = "--append" in args
    unreleased = "--unreleased" in args

    for i, arg in enumerate(args):
        if arg == "--since" and i + 1 < len(args):
            since = args[i + 1]
        elif arg == "--version" and i + 1 < len(args):
            version = args[i + 1]

    # Default: since last tag
    if since is None:
        since = get_last_tag()
        if since:
            print(f"Generating changelog since {since}...")
        else:
            print("No previous tag found, generating from all commits...")

    # Get commits
    commits = get_commits_since(since)
    if not commits:
        print("No commits found in range.")
        sys.exit(0)

    print(f"Found {len(commits)} commits")

    # Determine version
    if version is None and not unreleased:
        # Try to get from manifest
        manifest = ROOT / "project.manifest.json"
        if manifest.exists():
            import json
            data = json.loads(manifest.read_text())
            version = data.get("project", {}).get("version", "Unreleased")
        else:
            version = "Unreleased"
            unreleased = True

    # Generate entry
    entry = generate_changelog_entry(version or "Unreleased", commits, unreleased)

    if not entry:
        print("No conventional commits found (feat/fix/refactor/etc). Nothing to add.")
        sys.exit(0)

    print("\n" + "=" * 60)
    print(entry)
    print("=" * 60)

    if should_append:
        append_to_changelog(entry)
    else:
        print("\nUse --append to add this to CHANGELOG.md")


if __name__ == "__main__":
    main()
