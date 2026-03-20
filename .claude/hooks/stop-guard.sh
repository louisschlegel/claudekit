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

# Documentation reminders based on what was changed
DOC_REMINDERS=""
if [ -f "$SESSION_FILES" ] || [ -n "$CHANGES" ] || [ -n "$STAGED" ]; then
  # Check if key files were modified without corresponding doc updates
  CHANGED_FILES=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)

  HAS_SRC_CHANGES=$(echo "$CHANGED_FILES" | grep -cE "^(src/|lib/|app/|scripts/)" || true)
  HAS_CHANGELOG=$(echo "$CHANGED_FILES" | grep -c "CHANGELOG" || true)
  HAS_README=$(echo "$CHANGED_FILES" | grep -c "README" || true)

  [ "$HAS_SRC_CHANGES" -gt 3 ] 2>/dev/null && [ "$HAS_CHANGELOG" -eq 0 ] 2>/dev/null && \
    DOC_REMINDERS="$DOC_REMINDERS\n📖 Significant code changes without CHANGELOG update — consider adding an entry"

  # Check for architecture-level changes without ADR
  HAS_ARCH_CHANGES=$(echo "$CHANGED_FILES" | grep -cE "(docker|terraform|\.github/workflows|infra/|deploy/)" || true)
  [ "$HAS_ARCH_CHANGES" -gt 0 ] 2>/dev/null && \
    DOC_REMINDERS="$DOC_REMINDERS\n📖 Infrastructure/architecture changes detected — consider /generate-adr"
fi

if [ -n "$WARNINGS" ] || [ -n "$DOC_REMINDERS" ]; then
  printf "%b%b" "$WARNINGS" "$DOC_REMINDERS"
fi

exit 0
