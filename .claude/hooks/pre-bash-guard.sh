#!/bin/bash
# Hook: PreToolUse(Bash) — Bloque les commandes dangereuses
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Commandes destructives interdites sans confirmation explicite
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf $HOME"
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE"
  "git push --force origin main"
  "git push --force origin master"
  "git reset --hard HEAD~"
  "> /etc/"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qF "$pattern"; then
    BLOCKED_PATTERN="$pattern"
    python3 -c "
import json, sys
pattern = sys.argv[1]
print(json.dumps({
    'decision': 'block',
    'reason': f'Commande potentiellement destructive détectée : {repr(pattern)}. Confirme explicitement si tu veux vraiment exécuter ça.'
}))
" "$BLOCKED_PATTERN"
    exit 0
  fi
done

# Laisser passer
exit 0
