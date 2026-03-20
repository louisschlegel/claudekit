#!/bin/bash
# Hook: PermissionRequest — auto-approve safe patterns, block sensitive ones
INPUT=$(cat)
python3 - "$INPUT" << 'PYEOF'
import json, sys, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip(): sys.exit(0)
try:
    event = json.loads(raw)
except json.JSONDecodeError: sys.exit(0)

tool_name = event.get("tool_name", "")
tool_input = event.get("tool_input", {})

# Dangerous patterns — NEVER auto-approve
DANGEROUS = [
    r"/etc/shadow", r"/etc/passwd", r"\.env\b", r"\.env\.", r"credentials",
    r"\.ssh/", r"\.aws/", r"\.gnupg/", r"secret", r"password", r"token",
    r"\.pem$", r"\.key$", r"private", r"/etc/", r"~/"
]

if tool_name == "Bash":
    cmd = tool_input.get("command", "")
    # Check for dangerous patterns first
    for pat in DANGEROUS:
        if re.search(pat, cmd, re.IGNORECASE):
            sys.exit(0)  # Let user decide

    # Safe read-only bash patterns
    SAFE_BASH = [
        "git status", "git diff", "git log", "git branch", "git show",
        "ls ", "wc ", "which ", "type ",
        "python3 -m pytest", "pytest ", "npm test", "npm run test",
        "python3 -m py_compile", "python3 -c \"import",
        "make validate", "make check", "make test",
        "ruff check", "ruff format", "eslint", "prettier",
    ]
    for safe in SAFE_BASH:
        if cmd.strip().startswith(safe):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "permissionDecision": "allow"}}))
            sys.exit(0)

# Read/Glob/Grep — safe but check path for sensitive files
if tool_name in ("Read", "Glob", "Grep"):
    path = tool_input.get("file_path", "") or tool_input.get("path", "") or ""
    for pat in DANGEROUS:
        if re.search(pat, path, re.IGNORECASE):
            sys.exit(0)  # Let user decide
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PermissionRequest", "permissionDecision": "allow"}}))
    sys.exit(0)

sys.exit(0)
PYEOF
exit 0
