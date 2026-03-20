#!/bin/bash
# Hook: PreToolUse(Bash) — Block dangerous commands
# Case-insensitive, detects chaining, covers more patterns

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

[ -z "$COMMAND" ] && exit 0

python3 - "$COMMAND" << 'PYEOF'
import json, sys, re

cmd = sys.argv[1] if len(sys.argv) > 1 else ""
if not cmd.strip():
    sys.exit(0)

# Strip heredoc content and quoted strings to avoid false positives on commit messages
import shlex
# Only check the command part, not heredoc content or quoted strings
cmd_check = cmd.split("<<")[0] if "<<" in cmd else cmd
# Also strip content inside $() to avoid matching on git commit message text
cmd_check = re.sub(r'\$\(cat\s+<<.*', '', cmd_check, flags=re.DOTALL)
cmd_lower = cmd_check.lower()

# Category 1: Destructive file operations
DESTRUCTIVE = [
    r"\brm\s+-rf\s+/",
    r"\brm\s+-rf\s+~",
    r"\brm\s+-rf\s+\$HOME",
    r"\bmkfs\s",
    r"\bdd\s+if=.*/dev/",
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\s+.*\s+/",
]

# Category 2: Database destruction (case-insensitive)
DB_DESTROY = [
    r"drop\s+database",
    r"drop\s+table",
    r"drop\s+schema",
    r"truncate\s+table",
    r"delete\s+from\s+\w+\s*;?\s*$",  # DELETE without WHERE
]

# Category 3: Git destructive
GIT_DESTROY = [
    r"git\s+push\s+(-f|--force)\s",
    r"git\s+push\s+.*\s+(-f|--force)",
    r"git\s+push\s+--force\b",
    r"git\s+reset\s+--hard\b",
    r"git\s+clean\s+-fd",
    r"git\s+checkout\s+--\s+\.",
    r"git\s+branch\s+-D\s+(main|master)",
]

# Category 4: Code execution of untrusted input
EXEC_DANGER = [
    r"\beval\s*\(",
    r"\beval\s+\"",
    r"\bexec\s*\(",
    r"base64\s+(-d|--decode).*\|\s*(bash|sh|python|eval)",
    r"curl.*\|\s*(bash|sh|python)",
    r"wget.*\|\s*(bash|sh|python)",
]

# Category 5: System-level danger
SYSTEM = [
    r"shutdown\b",
    r"reboot\b",
    r"init\s+0",
    r"kill\s+-9\s+-1",
    r"killall\b",
    r"pkill\s+-9",
]

ALL_PATTERNS = [
    ("destructive_file", DESTRUCTIVE),
    ("database_destroy", DB_DESTROY),
    ("git_destructive", GIT_DESTROY),
    ("code_execution", EXEC_DANGER),
    ("system_danger", SYSTEM),
]

for category, patterns in ALL_PATTERNS:
    for p in patterns:
        if re.search(p, cmd_lower if category != "destructive_file" else cmd):
            result = {
                "decision": "block",
                "reason": f"Dangerous command blocked [{category}]: pattern '{p}' matched in: {cmd[:100]}"
            }
            print(json.dumps(result))
            sys.exit(2)

sys.exit(0)
PYEOF

EXIT_CODE=$?
[ $EXIT_CODE -eq 2 ] && exit 2
exit 0
