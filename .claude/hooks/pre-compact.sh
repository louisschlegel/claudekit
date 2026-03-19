#!/bin/bash
# Hook: PreCompact — Sauvegarde plan + décisions clés avant compaction auto
# Evite de perdre le contexte critique lors de la compaction

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
SUMMARY=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('summary',''))" 2>/dev/null || echo "")

mkdir -p "$PROJECT_ROOT/.template"
BACKUP="$PROJECT_ROOT/.template/session-backup.md"

python3 -c "
from datetime import datetime
import sys
summary = sys.argv[1] if len(sys.argv) > 1 else ''
ts = datetime.now().strftime('%Y-%m-%d %H:%M')
content = f'# Session backup — {ts}\n\n'
if summary:
    content += f'## Resume pre-compaction\n{summary}\n\n'
content += '_Sauvegarde automatiquement avant compaction du contexte._\n'
with open('$BACKUP', 'w') as f:
    f.write(content)
print(f'[pre-compact] Backup sauvegarde : $BACKUP')
" "$SUMMARY" 2>/dev/null

exit 0
