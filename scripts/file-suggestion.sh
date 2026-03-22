#!/bin/bash
# claudekit file suggestion — fast @ autocomplete using rg
# Respects .gitignore, sorts by recent git modification
# Configure: "fileSuggestion": {"type": "command", "command": "bash scripts/file-suggestion.sh"}

QUERY=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('query',''))" 2>/dev/null || echo "")
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"

if [ -z "$QUERY" ]; then
  # No query — show recently modified files
  cd "$PROJECT_DIR" && git log --diff-filter=M --name-only --pretty=format: -20 2>/dev/null | grep -v "^$" | sort -u | head -15
else
  # Query — fuzzy match with rg
  cd "$PROJECT_DIR" && rg --files 2>/dev/null | grep -i "$QUERY" | head -15
fi
