#!/bin/bash
# Hook: manifest-regen — re-runs gen.py when project.manifest.json is edited

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Only trigger when project.manifest.json was the file edited
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

if ! echo "$FILE" | grep -q "project\.manifest\.json$"; then
  exit 0
fi

# Validate JSON before regenerating
python3 -c "import json; json.load(open('$PROJECT_ROOT/project.manifest.json'))" 2>/dev/null || {
  echo '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "⚠️  project.manifest.json: JSON invalide — corrige la syntaxe avant que gen.py puisse régénérer la config."}}'
  exit 0
}

# Run gen.py silently
cd "$PROJECT_ROOT" && (python3 scripts/gen.py --quiet 2>/dev/null || python3 scripts/gen.py 2>/dev/null) && \
  echo '{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "✓ project.manifest.json modifié — config régénérée automatiquement (settings.local.json, .mcp.json, hooks)."}}'

exit 0
