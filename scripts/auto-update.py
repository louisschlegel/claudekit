#!/usr/bin/env python3
"""
auto-update.py — Mise à jour silencieuse de claudekit depuis GitHub.

Usage:
    python3 scripts/auto-update.py [--dry-run] [--force] [--quiet]

Options:
    --dry-run  Montre ce qui serait mis à jour sans rien écrire
    --force    Ignore le cooldown 24h et le check de version identique
    --quiet    Pas de stdout (pour usage depuis hooks)
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

UPDATABLE_PATHS = [
    "scripts/gen.py",
    "scripts/auto-learn.py",
    "scripts/self-improve.py",
    "scripts/instinct-loop.py",
    "scripts/evolve.sh",
    "scripts/discovery-scan.py",
    "scripts/auto-update.py",
]

UPDATABLE_DIRS = [
    ".claude/agents",
    ".claude/docs",
    ".claude/rules",
    "workflows",
]

GENERATED_HOOKS = {
    "session-start.sh", "user-prompt-submit.sh", "pre-bash-guard.sh",
    "post-edit.sh", "stop.sh", "pre-push.sh", "pre-compact.sh",
    "notification.sh", "subagent-stop.sh", "observability.sh",
    "injection-defender.sh", "context-monitor.sh", "live-handoff.sh",
    "stop-guard.sh", "session-end.sh", "permission-auto.sh", "manifest-regen.sh",
    "tool-failure.sh", "test-filter.sh",
    "worktree-create.sh", "worktree-remove.sh", "teammate-idle.sh",
    "config-change.sh", "elicitation.sh", "elicitation-result.sh",
}

# Fichiers à ne jamais toucher, quoi qu'il arrive
PROTECTED_PATHS = {
    ".claude/settings.local.json",
    "project.manifest.json",
    "learning.md",
    ".mcp.json",
    ".template/version.json",
    ".template/instincts.json",
    "pending-features.md",
}

COOLDOWN_HOURS = 24

# ─── Helpers ──────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


def parse_version(v: str) -> tuple:
    """Parse a semver string into a comparable tuple."""
    v = v.strip().lstrip("v")
    parts = re.split(r"[.\-]", v)
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def is_newer(remote: str, local: str) -> bool:
    return parse_version(remote) > parse_version(local)


def append_log(log_path: Path, entry: dict) -> None:
    """Append a JSONL entry to the update log."""
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def fetch_raw(owner: str, repo: str, path: str, token: str = None) -> str:
    """Fetch raw file content from GitHub."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
    headers = {"User-Agent": "claudekit-autoupdate/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def list_github_dir(owner: str, repo: str, path: str, token: str = None) -> list:
    """List files in a GitHub repo directory via the contents API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "User-Agent": "claudekit-autoupdate/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def git_is_clean(project_root: Path, rel_path: str) -> bool:
    """Return True if the given path has no local modifications."""
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", rel_path],
            cwd=str(project_root),
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return True  # assume clean if git not available


def write_file(path: Path, content: str, dry_run: bool) -> bool:
    """Write content to path, creating parent dirs as needed. Returns True on success."""
    if dry_run:
        return True
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if path.suffix == ".sh":
            path.chmod(path.stat().st_mode | 0o111)
        return True
    except Exception as e:
        return False


# ─── Core update logic ────────────────────────────────────────────────────────

def should_check(last_check_file: Path, force: bool) -> bool:
    """Return True if we should run a check now."""
    if force:
        return True
    if not last_check_file.exists():
        return True
    try:
        ts_str = last_check_file.read_text().strip()
        last_ts = datetime.fromisoformat(ts_str)
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        elapsed_hours = (datetime.now(timezone.utc) - last_ts).total_seconds() / 3600
        return elapsed_hours >= COOLDOWN_HOURS
    except Exception:
        return True


def collect_files_to_update(
    owner: str,
    repo: str,
    project_root: Path,
    token: str,
    dry_run: bool,
    quiet: bool,
) -> list:
    """Build the list of (local_path, remote_path) pairs to update."""
    files = []

    # Individual files
    for rel in UPDATABLE_PATHS:
        local = project_root / rel
        if not local.exists():
            # Only update files that exist locally (no surprise new files)
            continue
        # CLAUDE.md: only if no local modifications
        if rel == "CLAUDE.md" and not git_is_clean(project_root, rel):
            log(f"  skip {rel} (local modifications)", quiet)
            continue
        files.append((local, rel))

    # Directories — fetch all .md and .sh files listed by GitHub API
    for dir_rel in UPDATABLE_DIRS:
        try:
            entries = list_github_dir(owner, repo, dir_rel, token)
        except Exception:
            log(f"  skip dir {dir_rel} (API unavailable)", quiet)
            continue
        for entry in entries:
            if entry.get("type") != "file":
                continue
            name = entry.get("name", "")
            if not (name.endswith(".md") or name.endswith(".sh")):
                continue
            rel = f"{dir_rel}/{name}"
            local = project_root / rel
            if not local.exists():
                continue  # only update existing files
            files.append((local, rel))

    # Generated hooks only
    hooks_dir_local = project_root / ".claude" / "hooks"
    hooks_dir_remote = ".claude/hooks"
    if hooks_dir_local.is_dir():
        try:
            entries = list_github_dir(owner, repo, hooks_dir_remote, token)
        except Exception:
            entries = []
        for entry in entries:
            if entry.get("type") != "file":
                continue
            name = entry.get("name", "")
            if name not in GENERATED_HOOKS:
                continue
            local = hooks_dir_local / name
            if not local.exists():
                continue
            files.append((local, f"{hooks_dir_remote}/{name}"))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in files:
        key = str(item[0])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def run_gen_py(project_root: Path, dry_run: bool, quiet: bool) -> bool:
    """Run gen.py --preserve-custom after update."""
    gen_py = project_root / "scripts" / "gen.py"
    if not gen_py.exists():
        return False
    if dry_run:
        log("  [dry-run] would run: python3 scripts/gen.py --preserve-custom", quiet)
        return True
    try:
        result = subprocess.run(
            [sys.executable, str(gen_py), "--preserve-custom"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except Exception:
        return False


def build_summary(version_data: dict, from_v: str, to_v: str) -> str:
    """Extract changelog summary for the update range."""
    history = version_data.get("improvement_history", [])
    entries = []
    for entry in history:
        entry_from = entry.get("from", "")
        summary = entry.get("summary", "")
        if summary and parse_version(entry_from) >= parse_version(from_v):
            entries.append(summary)
    return "; ".join(entries) if entries else f"Update from {from_v} to {to_v}"


def main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    force = "--force" in args
    quiet = "--quiet" in args

    # Locate project root (2 levels up from this script)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    template_dir = project_root / ".template"
    version_file = template_dir / "version.json"
    last_check_file = template_dir / "last-update-check.txt"
    log_file = template_dir / "update-log.jsonl"
    applied_file = template_dir / "update-applied.json"

    # ── Read local version ────────────────────────────────────────────────────
    try:
        local_data = json.loads(version_file.read_text())
        local_version = local_data.get("version", "0.0.0")
        source_url = local_data.get("source", "")
    except Exception:
        # No version file — silently exit
        return 0

    # ── Parse owner/repo from source URL ─────────────────────────────────────
    match = re.search(r"github\.com/([^/]+)/([^/\s]+)", source_url)
    if not match:
        return 0
    owner, repo = match.group(1), match.group(2).rstrip("/").rstrip(".git")

    # ── Cooldown check ────────────────────────────────────────────────────────
    if not should_check(last_check_file, force):
        return 0

    # Write timestamp immediately to avoid concurrent checks
    if not dry_run:
        try:
            template_dir.mkdir(parents=True, exist_ok=True)
            last_check_file.write_text(now_iso())
        except Exception:
            pass

    # ── Fetch remote version ──────────────────────────────────────────────────
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    try:
        raw = fetch_raw(owner, repo, ".template/version.json", token)
        remote_data = json.loads(raw)
        remote_version = remote_data.get("version", "0.0.0")
    except urllib.error.URLError:
        # GitHub unreachable — exit silently
        append_log(log_file, {
            "ts": now_iso(), "event": "update_check",
            "local": local_version, "remote": "?",
            "action": "error", "files_count": 0,
            "error": "network_unavailable",
        })
        return 0
    except Exception as e:
        append_log(log_file, {
            "ts": now_iso(), "event": "update_check",
            "local": local_version, "remote": "?",
            "action": "error", "files_count": 0,
            "error": str(e)[:120],
        })
        return 0

    # ── Compare versions ──────────────────────────────────────────────────────
    if not is_newer(remote_version, local_version) and not force:
        log(f"claudekit is up to date ({local_version})", quiet)
        append_log(log_file, {
            "ts": now_iso(), "event": "update_check",
            "local": local_version, "remote": remote_version,
            "action": "skipped", "files_count": 0,
        })
        return 0

    log(f"claudekit update available: {local_version} → {remote_version}", quiet)

    # ── Collect files to update ───────────────────────────────────────────────
    try:
        files_to_update = collect_files_to_update(
            owner, repo, project_root, token, dry_run, quiet
        )
    except Exception as e:
        append_log(log_file, {
            "ts": now_iso(), "event": "update_check",
            "local": local_version, "remote": remote_version,
            "action": "error", "files_count": 0,
            "error": f"collect_failed: {str(e)[:120]}",
        })
        return 0

    updated_files = []
    failed_files = []

    for local_path, remote_rel in files_to_update:
        # Safety: never touch protected files
        if remote_rel in PROTECTED_PATHS:
            continue
        try:
            content = fetch_raw(owner, repo, remote_rel, token)
        except Exception:
            failed_files.append(remote_rel)
            continue

        if dry_run:
            log(f"  [dry-run] would update: {remote_rel}", quiet)
            updated_files.append(remote_rel)
            continue

        ok = write_file(local_path, content, dry_run=False)
        if ok:
            log(f"  updated: {remote_rel}", quiet)
            updated_files.append(remote_rel)
        else:
            failed_files.append(remote_rel)

    if failed_files:
        log(f"  failed to update {len(failed_files)} file(s): {', '.join(failed_files[:5])}", quiet)

    # ── Run gen.py --preserve-custom ─────────────────────────────────────────
    gen_ok = run_gen_py(project_root, dry_run, quiet)
    if not gen_ok:
        log("  warning: gen.py --preserve-custom failed or not found", quiet)

    # ── Update .template/version.json ────────────────────────────────────────
    if not dry_run and updated_files:
        try:
            local_data["version"] = remote_version
            version_file.write_text(json.dumps(local_data, indent=2, ensure_ascii=False))
        except Exception:
            pass

    # ── Write update-applied.json (read once by session-start, then deleted) ─
    summary = build_summary(remote_data, local_version, remote_version)
    applied_payload = {
        "from_version": local_version,
        "to_version": remote_version,
        "timestamp": now_iso(),
        "files_updated": updated_files,
        "summary": summary,
    }
    if not dry_run and updated_files:
        try:
            applied_file.write_text(json.dumps(applied_payload, indent=2, ensure_ascii=False))
        except Exception:
            pass

    # ── Append to update-log.jsonl ────────────────────────────────────────────
    action = "dry-run" if dry_run else ("updated" if updated_files else "skipped")
    append_log(log_file, {
        "ts": now_iso(), "event": "update_check",
        "local": local_version, "remote": remote_version,
        "action": action, "files_count": len(updated_files),
    })

    if dry_run:
        log(f"\n[dry-run] {len(updated_files)} file(s) would be updated.", quiet)
    elif updated_files:
        log(f"claudekit updated to {remote_version} ({len(updated_files)} files).", quiet)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never crash the parent process
        sys.exit(0)
