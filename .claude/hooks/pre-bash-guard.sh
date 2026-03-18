#!/bin/bash
# Hook: PreToolUse (Bash) — Guard against destructive commands
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

if [ "$TOOL" != "Bash" ]; then
    exit 0
fi

COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

python3 - "$COMMAND" <<'PYEOF'
import sys, json, re

command = sys.argv[1] if len(sys.argv) > 1 else ""

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-rf\s+/', "rm -rf on root path"),
    (r'\brm\s+-rf\s+\*', "rm -rf with wildcard"),
    (r'\brm\s+-rf\s+~', "rm -rf on home directory"),
    (r'DROP\s+DATABASE', "DROP DATABASE"),
    (r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', "DROP TABLE without IF EXISTS"),
    (r'TRUNCATE\s+TABLE', "TRUNCATE TABLE"),
    (r'git\s+push\s+--force\s+origin\s+(main|master)', "force push to main/master"),
    (r'git\s+push\s+-f\s+origin\s+(main|master)', "force push to main/master"),
    (r'chmod\s+777', "chmod 777 (world-writable)"),
    (r'>\s*/etc/', "overwrite system config file"),
    (r'\brm\b.*\.env\b', "delete .env file"),
    (r'git\s+reset\s+--hard\s+HEAD~[2-9]', "reset multiple commits"),
    (r'pkill\s+-9\s+-f', "kill all matching processes"),
    (r'dd\s+if=.*of=/dev/', "dd to block device"),
]

for pattern, description in DESTRUCTIVE_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        print(json.dumps({
            "decision": "block",
            "reason": f"Blocked: {description}. Confirm explicitly if intentional."
        }))
        sys.exit(0)

sys.exit(0)
PYEOF

exit 0
