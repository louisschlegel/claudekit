#!/usr/bin/env bash
# pre-push.sh — Validation locale avant git push
# Installé comme git hook : .git/hooks/pre-push → .claude/hooks/pre-push.sh
# Usage : bash .claude/hooks/pre-push.sh [ref] [remote]
#
# Exécute (dans l'ordre, stop au premier échec) :
#   1. Secret scan — jamais pusher de credentials
#   2. Lint — code valide
#   3. Tests rapides — pas de régression
#   4. Guard anti push --force sur main

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
MANIFEST="$PROJECT_ROOT/project.manifest.json"

# ─── Helpers ──────────────────────────────────────────────────────────────────

pass()  { echo "  ✅ $1"; }
fail()  { echo "  ❌ $1" >&2; exit 1; }
warn()  { echo "  ⚠️  $1"; }
skip()  { echo "  ⏭️  $1 (skipped)"; }
info()  { echo "  ℹ️  $1"; }

read_manifest_field() {
    local field="$1"
    if command -v python3 >/dev/null 2>&1 && [ -f "$MANIFEST" ]; then
        python3 -c "
import json, sys
try:
    with open('$MANIFEST') as f:
        m = json.load(f)
    keys = '$field'.split('.')
    val = m
    for k in keys:
        val = val.get(k, '')
    print(val if isinstance(val, str) else json.dumps(val))
except: print('')
" 2>/dev/null
    fi
}

echo ""
echo "🔒 claudekit pre-push guard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT"

# ─── Lire les guards depuis le manifest ───────────────────────────────────────

LINT_GUARD=$(read_manifest_field "guards.lint")
SECRET_GUARD=$(read_manifest_field "guards.secret_scan")
TEST_GUARD=$(read_manifest_field "guards.test_on_edit")
LANGUAGES=$(read_manifest_field "stack.languages")

# ─── 1. Anti-force-push sur main ──────────────────────────────────────────────

echo ""
echo "1/4 — Branch protection"

CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "HEAD")
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    # Vérifier si le push est un force push (rewrite d'historique)
    while read local_ref local_sha remote_ref remote_sha; do
        if [ "$remote_sha" != "0000000000000000000000000000000000000000" ]; then
            # La branche distante existe — vérifier qu'on n'a pas réécrit l'historique
            if ! git merge-base --is-ancestor "$remote_sha" "$local_sha" 2>/dev/null; then
                fail "Force push on main/master is not allowed. Use a feature branch."
            fi
        fi
    done
    pass "Branch: $CURRENT_BRANCH (no force-push detected)"
else
    pass "Branch: $CURRENT_BRANCH (feature branch)"
fi

# ─── 2. Secret scan ───────────────────────────────────────────────────────────

echo ""
echo "2/4 — Secret scan"

if [[ "$SECRET_GUARD" == "true" || "$SECRET_GUARD" == "True" ]]; then
    # Patterns de secrets à détecter dans le diff
    SECRET_PATTERNS=(
        'sk-[a-zA-Z0-9]{20,}'          # Anthropic / OpenAI keys
        'AKIA[0-9A-Z]{16}'             # AWS Access Key
        'ghp_[a-zA-Z0-9]{36}'          # GitHub Personal Token
        'xoxb-[0-9-a-zA-Z]+'           # Slack Bot Token
        'xoxp-[0-9-a-zA-Z]+'           # Slack User Token
        'eyJ[a-zA-Z0-9+/=]{20,}'       # JWT tokens
        'pk_live_[a-zA-Z0-9]+'         # Stripe live key
        'sk_live_[a-zA-Z0-9]+'         # Stripe secret key
        'AIza[0-9A-Za-z-_]{35}'        # Google API key
        'password\s*=\s*["\x27][^"\x27]{4,}["\x27]'  # Hardcoded passwords
        'secret\s*=\s*["\x27][^"\x27]{8,}["\x27]'    # Hardcoded secrets
        'api[_-]?key\s*=\s*["\x27][^"\x27]{8,}["\x27]'  # API keys
    )

    STAGED_DIFF=$(git diff --cached 2>/dev/null || true)
    PUSH_DIFF=$(git diff HEAD~1 HEAD 2>/dev/null || true)
    DIFF_TO_CHECK="${STAGED_DIFF}${PUSH_DIFF}"

    SECRET_FOUND=false
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if echo "$DIFF_TO_CHECK" | grep -qE "$pattern" 2>/dev/null; then
            warn "Potential secret detected matching: $pattern"
            SECRET_FOUND=true
        fi
    done

    # Vérifier aussi les fichiers .env et credentials
    DANGEROUS_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | \
        grep -E '\.env$|\.env\.|credentials|secret|private_key|id_rsa|id_ed25519' || true)

    if [ -n "$DANGEROUS_FILES" ]; then
        warn "Sensitive files in commit:"
        echo "$DANGEROUS_FILES" | while read f; do warn "  $f"; done
        fail "Remove sensitive files before pushing."
    fi

    if [ "$SECRET_FOUND" = true ]; then
        fail "Potential secrets detected. Review the diff before pushing."
    fi

    pass "No secrets detected"
else
    skip "Secret scan (disabled in manifest)"
fi

# ─── 3. Lint ──────────────────────────────────────────────────────────────────

echo ""
echo "3/4 — Lint"

if [[ "$LINT_GUARD" == "true" || "$LINT_GUARD" == "True" ]]; then
    LINT_FAILED=false

    # Python — ruff
    if echo "$LANGUAGES" | grep -q "python" && command -v ruff >/dev/null 2>&1; then
        if ! ruff check . --quiet 2>/dev/null; then
            warn "ruff found lint errors"
            LINT_FAILED=true
        else
            pass "ruff: OK"
        fi
    fi

    # TypeScript/JavaScript — eslint
    if echo "$LANGUAGES" | grep -qE "typescript|javascript" && [ -f ".eslintrc*" -o -f "eslint.config*" ]; then
        if command -v npx >/dev/null 2>&1; then
            if ! npx eslint . --quiet 2>/dev/null; then
                warn "eslint found lint errors"
                LINT_FAILED=true
            else
                pass "eslint: OK"
            fi
        fi
    fi

    # Go — go vet
    if echo "$LANGUAGES" | grep -q '"go"' && command -v go >/dev/null 2>&1; then
        if ! go vet ./... 2>/dev/null; then
            warn "go vet found issues"
            LINT_FAILED=true
        else
            pass "go vet: OK"
        fi
    fi

    # Rust — clippy
    if echo "$LANGUAGES" | grep -q "rust" && command -v cargo >/dev/null 2>&1; then
        if ! cargo clippy --quiet 2>/dev/null; then
            warn "cargo clippy found issues"
            LINT_FAILED=true
        else
            pass "clippy: OK"
        fi
    fi

    # Terraform — tflint
    if echo "$LANGUAGES" | grep -q "hcl" && command -v tflint >/dev/null 2>&1; then
        if ! tflint --quiet 2>/dev/null; then
            warn "tflint found issues"
            LINT_FAILED=true
        else
            pass "tflint: OK"
        fi
    fi

    if [ "$LINT_FAILED" = true ]; then
        fail "Lint errors found. Run the linter and fix before pushing."
    fi
else
    skip "Lint (disabled in manifest)"
fi

# ─── 4. Tests rapides ─────────────────────────────────────────────────────────

echo ""
echo "4/4 — Quick tests"

if [[ "$TEST_GUARD" == "true" || "$TEST_GUARD" == "True" ]]; then
    TEST_FAILED=false

    # Python — pytest (rapide, exclure les tests d'intégration)
    if echo "$LANGUAGES" | grep -q "python" && command -v pytest >/dev/null 2>&1; then
        if ! pytest -x -q --tb=short -m "not integration and not slow" 2>/dev/null; then
            warn "pytest: some tests failed"
            TEST_FAILED=true
        else
            pass "pytest: OK"
        fi
    fi

    # Node.js — vitest / jest
    if echo "$LANGUAGES" | grep -qE "typescript|javascript"; then
        if [ -f "package.json" ]; then
            TEST_CMD=$(python3 -c "
import json
with open('package.json') as f:
    p = json.load(f)
scripts = p.get('scripts', {})
print(scripts.get('test:unit', scripts.get('test', '')))
" 2>/dev/null || echo "")
            if [ -n "$TEST_CMD" ] && command -v npm >/dev/null 2>&1; then
                if ! npm test --silent 2>/dev/null; then
                    warn "npm test: some tests failed"
                    TEST_FAILED=true
                else
                    pass "npm test: OK"
                fi
            fi
        fi
    fi

    # Go
    if echo "$LANGUAGES" | grep -q '"go"' && command -v go >/dev/null 2>&1; then
        if ! go test ./... -short -count=1 2>/dev/null; then
            warn "go test: some tests failed"
            TEST_FAILED=true
        else
            pass "go test: OK"
        fi
    fi

    if [ "$TEST_FAILED" = true ]; then
        fail "Tests failed. Fix before pushing."
    fi
else
    skip "Tests (test_on_edit disabled in manifest)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All checks passed — push allowed"
echo ""
