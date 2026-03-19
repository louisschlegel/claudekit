#!/bin/bash
# Hook: Notification — Claude needs attention (input required or task complete)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

PROJECT_NAME=$(python3 -c "
import json
from pathlib import Path
manifest = Path('$PROJECT_ROOT/project.manifest.json')
if manifest.exists():
    d = json.loads(manifest.read_text())
    print(d.get('project', {}).get('name', 'claudekit'))
else:
    print('claudekit')
" 2>/dev/null || echo "claudekit")

INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('message','Claude needs your attention'))" 2>/dev/null || echo "Claude needs your attention")

# macOS
if command -v osascript &>/dev/null; then
  osascript -e "display notification \"$MESSAGE\" with title \"$PROJECT_NAME\"" 2>/dev/null &
# Linux
elif command -v notify-send &>/dev/null; then
  notify-send "$PROJECT_NAME" "$MESSAGE" 2>/dev/null &
fi

# Audio (macOS)
if command -v afplay &>/dev/null; then
  afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
elif command -v paplay &>/dev/null; then
  paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null &
fi

exit 0
