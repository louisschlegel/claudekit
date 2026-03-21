#!/bin/bash
# Hook: ConfigChange — intercept and audit configuration changes
# Decision control hook: can block changes to protected config keys (exit 2)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)

python3 - <<PYEOF
import json, time, sys
from pathlib import Path

data = json.loads("""$INPUT""") if """$INPUT""".strip() else {}

config_key = data.get("config_key", "")
old_value = data.get("old_value")
new_value = data.get("new_value")

# Protected keys — changes to these are blocked
PROTECTED_KEYS = {
    "permissions.deny",
    "sandbox.enabled",
    "disableBypassPermissionsMode",
    "permissions.disableBypassPermissionsMode",
}

# Log all changes to audit trail
history_path = Path("$PROJECT_ROOT/.template/config-history.jsonl")
history_path.parent.mkdir(exist_ok=True)

entry = {
    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    "event": "ConfigChange",
    "config_key": config_key,
    "old_value": old_value,
    "new_value": new_value,
    "blocked": config_key in PROTECTED_KEYS,
}
with open(history_path, "a") as f:
    f.write(json.dumps(entry) + "\n")

# Block protected key modifications
if config_key in PROTECTED_KEYS:
    print(json.dumps({
        "decision": "block",
        "reason": f"Config key '{config_key}' is protected and cannot be modified via hook. Edit settings.local.json directly."
    }))
    sys.exit(2)

sys.exit(0)
PYEOF

exit $?
