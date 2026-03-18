#!/bin/bash
# claudekit — Quick local validation script
# Run before pushing to catch issues without waiting for CI
# Usage: bash scripts/check.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

ok() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }
section() { echo -e "\n${YELLOW}$1${NC}"; }

section "Python scripts"
for f in gen.py auto-learn.py self-improve.py version-bump.py changelog-gen.py; do
    python3 -m py_compile "$ROOT/scripts/$f" && ok "$f" || fail "$f"
done

section "Bash hooks"
for f in session-start.sh user-prompt-submit.sh; do
    bash -n "$ROOT/.claude/hooks/$f" && ok "$f" || fail "$f"
done

section "JSON files"
for f in "project.manifest.EXAMPLE.json" ".template/version.json" ".template/known-patterns.json"; do
    python3 -c "import json; json.load(open('$ROOT/$f'))" && ok "$f" || fail "$f"
done

section "HANDOFF JSON coverage (agents)"
missing=0
for f in "$ROOT"/.claude/agents/*.md; do
    name=$(basename "$f")
    if ! grep -q "HANDOFF JSON" "$f"; then
        echo -e "${RED}  Missing HANDOFF JSON: $name${NC}"
        missing=1
    fi
done
[ $missing -eq 0 ] && ok "All agents have HANDOFF JSON" || exit 1

section "SPÉCIALISATIONS coverage (agents)"
missing=0
for f in "$ROOT"/.claude/agents/*.md; do
    name=$(basename "$f")
    if ! grep -q "SPÉCIALISATIONS" "$f"; then
        echo -e "${RED}  Missing SPÉCIALISATIONS: $name${NC}"
        missing=1
    fi
done
[ $missing -eq 0 ] && ok "All agents have SPÉCIALISATIONS" || exit 1

section "Routing table coverage"
python3 - "$ROOT" <<'EOF'
import re, sys

root = sys.argv[1]
hook = open(f"{root}/.claude/hooks/user-prompt-submit.sh").read()
hook_intents = set(re.findall(r'\("(\w[\w-]*)"\s*,', hook))

claude = open(f"{root}/CLAUDE.md").read()
claude_intents = set(re.findall(r'`(\w[\w-]*)`\s*\|.*workflows/', claude))

special = {'question', 'other', 'improve-template'}
uncovered = hook_intents - claude_intents - special
if uncovered:
    print(f"  Intents missing from routing table: {uncovered}")
    sys.exit(1)
print(f"  All {len(hook_intents)} intents covered in routing table")
EOF
ok "Routing table"

section "Examples JSON"
for f in "$ROOT"/examples/*.json; do
    name=$(basename "$f")
    python3 -c "import json; json.load(open('$f'))" && ok "$name" || fail "$name"
done

echo ""
echo -e "${GREEN}All checks passed.${NC}"
