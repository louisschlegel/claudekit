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

# ── Sécurité: bloquer commit de fichiers .env ─────────────────────────────
if echo "$FILE" | grep -qE "(^|/)\.env$|\.env\.(local|production|staging|test)$"; then
  python3 -c "
import json
print(json.dumps({
    'decision': 'block',
    'reason': 'Fichier .env détecté — ne jamais committer des credentials. Utilise .env.example à la place.'
}))
"
  exit 0
fi

# Python files: ruff lint (auto-fix)
if [[ "$FILE" == *.py ]]; then
    if command -v ruff >/dev/null 2>&1; then
        ruff check "$FILE" --fix --quiet 2>/dev/null || true
    fi
fi

# ── Python: complexité cyclomatique (radon) ──────────────────────────────
if echo "$FILE" | grep -q "\.py$"; then
  if command -v radon &>/dev/null; then
    CC_OUT=$(radon cc "$FILE" --min C -s 2>&1 | grep -v "^$")
    if [ -n "$CC_OUT" ]; then
      WARNINGS="$WARNINGS\n[radon] Complexité élevée :\n$CC_OUT"
    fi
  fi
fi

# Shell scripts: bash syntax check
if [[ "$FILE" == *.sh ]]; then
    if ! bash -n "$FILE" 2>/tmp/bash_syntax_err; then
        ERRORS="$ERRORS\n[bash -n] Syntax error in $FILE: $(cat /tmp/bash_syntax_err)"
    fi
fi

# Secret scan: warn on patterns that look like credentials
if [[ "$FILE" == *.py || "$FILE" == *.sh || "$FILE" == *.json || "$FILE" == *.yml || "$FILE" == *.yaml ]]; then
    python3 - "$FILE" <<'PYEOF' 2>/dev/null || true
import re, sys

filepath = sys.argv[1]
try:
    content = open(filepath).read()
except:
    sys.exit(0)

SECRET_PATTERNS = [
    (r'(?i)(api_key|apikey|secret_key|private_key)\s*=\s*["\'][A-Za-z0-9+/]{20,}', "potential API key"),
    (r'(?i)password\s*=\s*["\'][^"\']{6,}["\']', "hardcoded password"),
    (r'(?i)(aws_access_key_id|aws_secret_access_key)\s*=\s*["\'][A-Z0-9/+]{16,}', "AWS credential"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub token"),
    (r'sk-[A-Za-z0-9]{48}', "OpenAI API key"),
]

for pattern, description in SECRET_PATTERNS:
    if re.search(pattern, content):
        print(f"WARNING: {description} detected in {filepath} — do not commit secrets")
        break
PYEOF
fi

# ── Scan: prompt injection / secrets hardcodés ────────────────────────────
INJECTION_PATTERNS=(
  "ignore previous instructions"
  "ignore all instructions"
  "you are now"
  "AKIA[0-9A-Z]{16}"
  "sk-[a-zA-Z0-9]{48}"
  "ghp_[a-zA-Z0-9]{36}"
  "xoxb-[0-9]"
)

FILE_CONTENT=$(cat "$FILE" 2>/dev/null || echo "")
for pattern in "${INJECTION_PATTERNS[@]}"; do
  if echo "$FILE_CONTENT" | grep -qiE "$pattern" 2>/dev/null; then
    ERRORS="$ERRORS\n[security] Pattern suspect détecté dans $FILE : '$pattern'"
  fi
done

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
