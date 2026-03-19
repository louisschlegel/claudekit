#!/usr/bin/env python3
"""
self-improve.py — Observation engine for template self-improvement.

Called by stop.sh at the end of every session to log friction events.
Called by template-improver agent to read and process observations.

Usage:
    python3 scripts/self-improve.py --log '{"type": "agent_gap", "detail": "..."}'
    python3 scripts/self-improve.py --read [--last N]
    python3 scripts/self-improve.py --stats
    python3 scripts/self-improve.py --clear-processed
    python3 scripts/self-improve.py --check-threshold
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = ROOT / ".template"
LOG_FILE = TEMPLATE_DIR / "improvements.log"
PATTERNS_FILE = TEMPLATE_DIR / "known-patterns.json"
VERSION_FILE = TEMPLATE_DIR / "version.json"

VALID_TYPES = [
    "hook_friction",       # hook blocked legitimate action or missed dangerous one
    "agent_gap",           # task requested with no matching agent
    "workflow_gap",        # repeated task sequence without dedicated workflow
    "manifest_gap",        # desired config not supported by schema
    "detection_miss",      # stack not detected during setup
    "permission_error",    # command blocked by whitelist illegitimately
    "user_correction",     # user corrected Claude's approach
    "user_validation",     # user confirmed a non-obvious approach worked
]

AUTO_IMPROVE_THRESHOLD = 5  # number of sessions before suggesting self-improvement


def ensure_dirs():
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    if not PATTERNS_FILE.exists():
        PATTERNS_FILE.write_text(json.dumps({"patterns": [], "last_updated": None}, indent=2))
    if not LOG_FILE.exists():
        LOG_FILE.write_text("")


def log_event(event_data: dict):
    """Append a friction event to the JSONL log."""
    ensure_dirs()

    if "type" not in event_data:
        print("ERROR: event must have a 'type' field", file=sys.stderr)
        sys.exit(1)

    if event_data["type"] not in VALID_TYPES:
        print(f"ERROR: unknown type '{event_data['type']}'. Valid: {VALID_TYPES}", file=sys.stderr)
        sys.exit(1)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processed": False,
        **event_data,
    }

    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"Logged: {entry['type']} — {entry.get('detail', '')[:80]}")


def read_log(last_n: int = 0) -> list[dict]:
    """Read all or last N events from the log."""
    ensure_dirs()
    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        return []

    entries = []
    for line in LOG_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if last_n > 0:
        return entries[-last_n:]
    return entries


def print_stats():
    """Print statistics about logged observations."""
    entries = read_log()
    if not entries:
        print("No observations logged yet.")
        return

    unprocessed = [e for e in entries if not e.get("processed", False)]

    counts: dict[str, int] = {}
    for entry in unprocessed:
        t = entry.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1

    print(f"\n=== Template Observations ===")
    print(f"Total entries: {len(entries)}")
    print(f"Unprocessed: {len(unprocessed)}")
    print(f"\nBy type:")
    for t, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    # Show patterns ready for action (observed 2+ times)
    ready = {t: c for t, c in counts.items() if c >= 2}
    if ready:
        print(f"\nPatterns ready for improvement (2+ observations):")
        for t, count in ready.items():
            print(f"  {t}: {count} times — consider adding to known-patterns.json")

    # Check threshold
    session_count = _get_session_count()
    print(f"\nSession count since last self-improve: {session_count}/{AUTO_IMPROVE_THRESHOLD}")
    if session_count >= AUTO_IMPROVE_THRESHOLD:
        print(">>> THRESHOLD REACHED — self-improve workflow recommended <<<")


def check_threshold() -> bool:
    """Return True if self-improvement threshold is reached."""
    session_count = _get_session_count()
    return session_count >= AUTO_IMPROVE_THRESHOLD


def _get_session_count() -> int:
    """Count sessions since last self-improvement by counting unique session days."""
    entries = read_log()
    session_entries = [e for e in entries if not e.get("processed", False)]
    # Count unique days — more reliable than dividing by avg events per session
    return len(set(e.get("timestamp", "")[:10] for e in session_entries if e.get("timestamp")))


def clear_processed():
    """Mark all current entries as processed."""
    ensure_dirs()
    entries = read_log()
    if not entries:
        print("Nothing to clear.")
        return

    updated = []
    count = 0
    for entry in entries:
        if not entry.get("processed", False):
            entry["processed"] = True
            entry["processed_at"] = datetime.now(timezone.utc).isoformat()
            count += 1
        updated.append(entry)

    LOG_FILE.write_text("\n".join(json.dumps(e) for e in updated) + "\n")
    print(f"Marked {count} entries as processed.")


def add_known_pattern(pattern: dict):
    """Add or update a pattern in known-patterns.json."""
    ensure_dirs()
    data = json.loads(PATTERNS_FILE.read_text())
    patterns = data.get("patterns", [])

    # Check if pattern already exists
    existing = next((p for p in patterns if p.get("type") == pattern.get("type")
                     and p.get("description") == pattern.get("description")), None)

    if existing:
        existing["observed_count"] = existing.get("observed_count", 1) + 1
        existing["last_seen"] = datetime.now(timezone.utc).isoformat()
        print(f"Updated pattern count: {existing['observed_count']}")
    else:
        pattern["observed_count"] = 1
        pattern["added"] = datetime.now(timezone.utc).isoformat()
        pattern["last_seen"] = pattern["added"]
        patterns.append(pattern)
        print(f"Added new pattern: {pattern.get('type')}")

    data["patterns"] = patterns
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    PATTERNS_FILE.write_text(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Template observation engine")
    parser.add_argument("--log", type=str, help="JSON event to log")
    parser.add_argument("--read", action="store_true", help="Read log entries")
    parser.add_argument("--last", type=int, default=20, help="Number of entries to read")
    parser.add_argument("--stats", action="store_true", help="Print statistics")
    parser.add_argument("--clear-processed", action="store_true", help="Mark entries as processed")
    parser.add_argument("--check-threshold", action="store_true", help="Check if threshold reached")
    parser.add_argument("--add-pattern", type=str, help="JSON pattern to add to known-patterns.json")

    args = parser.parse_args()

    if args.log:
        try:
            event = json.loads(args.log)
            log_event(event)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.read:
        entries = read_log(last_n=args.last)
        for entry in entries:
            status = "✓" if entry.get("processed") else "·"
            ts = entry.get("timestamp", "")[:16]
            t = entry.get("type", "unknown")
            detail = entry.get("detail", "")[:60]
            print(f"{status} {ts} [{t}] {detail}")
        print(f"\nTotal: {len(entries)} entries")

    elif args.stats:
        print_stats()

    elif args.clear_processed:
        clear_processed()

    elif args.check_threshold:
        reached = check_threshold()
        print("THRESHOLD_REACHED" if reached else "THRESHOLD_NOT_REACHED")
        sys.exit(0 if reached else 1)

    elif args.add_pattern:
        try:
            pattern = json.loads(args.add_pattern)
            add_known_pattern(pattern)
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
