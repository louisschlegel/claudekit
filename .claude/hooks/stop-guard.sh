#!/bin/bash
# Hook: Stop — Guard against incomplete work
# Warns if there are uncommitted changes when stopping.
# Non-blocking (informational).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT" || exit 0

# Check for uncommitted changes
CHANGES=$(git diff --stat 2>/dev/null | tail -1)
STAGED=$(git diff --cached --stat 2>/dev/null | tail -1)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -5 | wc -l | tr -d ' ')

WARNINGS=""
[ -n "$CHANGES" ] && WARNINGS="$WARNINGS\n⚠️  Unstaged changes: $CHANGES"
[ -n "$STAGED" ] && WARNINGS="$WARNINGS\n⚠️  Staged but not committed: $STAGED"
[ "$UNTRACKED" -gt 0 ] 2>/dev/null && WARNINGS="$WARNINGS\n⚠️  $UNTRACKED untracked file(s)"

# Check for session files tracker
SESSION_FILES="$PROJECT_ROOT/.template/session-files.txt"
if [ -f "$SESSION_FILES" ]; then
  FILE_COUNT=$(wc -l < "$SESSION_FILES" | tr -d ' ')
  [ "$FILE_COUNT" -gt 0 ] 2>/dev/null && WARNINGS="$WARNINGS\n📝 $FILE_COUNT file(s) modified this session"
  # Clean up tracker
  rm -f "$SESSION_FILES"
fi

if [ -n "$WARNINGS" ]; then
  printf "%b" "$WARNINGS"
fi

exit 0
