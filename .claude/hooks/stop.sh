#!/bin/bash
# Hook: Stop — Rappel de mise à jour + logging d'observations
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LEARNING_FILE="learning.md"
PROJECT_NAME="claudekit"

# Vérifie si des fichiers ont été modifiés cette session
CHANGED=$(cd "$PROJECT_ROOT" && git status --short 2>/dev/null | wc -l | tr -d ' ')

# Logger une observation de session pour le self-improve engine
if command -v python3 &>/dev/null && [ -f "$PROJECT_ROOT/scripts/self-improve.py" ]; then
  python3 "$PROJECT_ROOT/scripts/self-improve.py" --log     '{"type": "user_validation", "detail": "session completed, claudekit"}'     2>/dev/null &
fi

if [ "$CHANGED" -gt "0" ]; then
  python3 -c "
import json
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'Stop',
        'additionalContext': '💾 Session terminée avec $CHANGED fichier(s) modifié(s). Si tu as découvert des patterns importants, des bugs ou des décisions d\'architecture, mets à jour \`learning.md\` pour $PROJECT_NAME.'
    }
}))
"
fi

exit 0
