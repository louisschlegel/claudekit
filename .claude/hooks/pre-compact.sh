#!/bin/bash
# Hook: PreCompact — Sauvegarde plan + décisions clés avant compaction auto
# Evite de perdre le contexte critique (plan en cours, décisions architecture)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
SUMMARY=$(echo "$INPUT" | python3 -c "
import json,sys
d=json.load(sys.stdin)
# PreCompact reçoit un objet avec 'summary' (résumé de la session)
print(d.get('summary',''))
" 2>/dev/null || echo "")

mkdir -p "$PROJECT_ROOT/.template"
BACKUP="$PROJECT_ROOT/.template/session-backup.md"
TS=$(date '+%Y-%m-%d %H:%M')

python3 -c "
import sys
from pathlib import Path
summary = sys.argv[1]
ts = sys.argv[2]
backup = Path(sys.argv[3])

lines = [f'# Session backup — {ts}', '']
if summary.strip():
    lines += ['## Résumé avant compaction', '', summary.strip(), '']
lines += ['---', '_Sauvegardé automatiquement par claudekit pre-compact hook._']

backup.write_text('\n'.join(lines))
" "$SUMMARY" "$TS" "$BACKUP" 2>/dev/null

# Output context so Claude knows the backup exists
python3 -c "
import json
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'PreCompact',
        'additionalContext': 'Contexte sauvegardé dans .template/session-backup.md avant compaction. Consulte ce fichier si tu perds le fil.'
    }
}))
" 2>/dev/null

exit 0
