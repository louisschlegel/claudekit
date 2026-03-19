#!/bin/bash
# Hook: PostToolUse(Edit|Write) — Guards qualité
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

ERRORS=''
WARNINGS=''

# ── Python: ruff lint ──────────────────────────────────
if echo "$FILE" | grep -q "\.py$"; then
  if command -v ruff &>/dev/null; then
    RUFF_OUT=$(ruff check "$FILE" 2>&1)
    if [ -n "$RUFF_OUT" ]; then
      ERRORS="$ERRORS\n[ruff] $RUFF_OUT"
    fi
  fi
fi

# ── Output ───────────────────────────────────────────────────
if [ -n "$ERRORS" ]; then
  python3 -c "
import json, sys
msg = sys.argv[1]
print(json.dumps({
    'decision': 'block',
    'reason': f'Guards qualité ont détecté des erreurs :\n{msg}'
}))
" "$ERRORS"
  exit 0
fi

if [ -n "$WARNINGS" ]; then
  python3 -c "
import json, sys
msg = sys.argv[1]
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': f'⚠️  Avertissements qualité :\n{msg}'
    }
}))
" "$WARNINGS"
fi

exit 0
