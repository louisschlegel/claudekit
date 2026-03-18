#!/bin/bash
# Hook: Stop — Auto-learning observation + learning.md reminder
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Log observation for self-improvement engine
if [ -f "$PROJECT_ROOT/scripts/self-improve.py" ]; then
    python3 "$PROJECT_ROOT/scripts/self-improve.py" \
        --log \
        --type "session_end" \
        --note "Session completed" \
        2>/dev/null &
fi

# Check if any source files were modified this session
MODIFIED=$(git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null | grep -v "^$" | wc -l)

if [ "$MODIFIED" -gt 0 ]; then
    python3 -c "
import json
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'Stop',
        'additionalContext': 'Session ended with $MODIFIED file(s) modified. Consider updating learning.md if patterns or decisions worth remembering were discovered.'
    }
}))
"
fi

exit 0
