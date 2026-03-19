#!/bin/bash
# Hook: SessionStart — Auto-portable, gere setup + injection de contexte
# Se localise via BASH_SOURCE — fonctionne depuis n'importe quel projet

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_NAME="claudekit"
LEARNING_FILE="learning.md"
COMPACT_FOCUS="architecture decisions, API contracts, current task context"

# ─── Cas 1 : manifest vide → guide le setup ──────────────────────────────────
MANIFEST_CONTENT=$(cat "$PROJECT_ROOT/project.manifest.json" 2>/dev/null | tr -d '[:space:]')

if [ "$MANIFEST_CONTENT" = "{}" ] || [ -z "$MANIFEST_CONTENT" ]; then

  DETECTED=""
  find_file() {
    find "$PROJECT_ROOT" -maxdepth 2 -name "$1" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | head -1
  }

  PKG_JSON=$(find_file "package.json")
  REQUIREMENTS=$(find_file "requirements.txt")
  PYPROJECT=$(find_file "pyproject.toml")
  GO_MOD=$(find_file "go.mod")
  CARGO=$(find_file "Cargo.toml")
  GEMFILE=$(find_file "Gemfile")

  [ -n "$PKG_JSON" ]      && DETECTED="$DETECTED\n- package.json ($(dirname "$PKG_JSON" | sed "s|$PROJECT_ROOT/||")) -> Node/TypeScript"
  [ -n "$REQUIREMENTS" ]  && DETECTED="$DETECTED\n- requirements.txt ($(dirname "$REQUIREMENTS" | sed "s|$PROJECT_ROOT/||")) -> Python"
  [ -n "$PYPROJECT" ]     && DETECTED="$DETECTED\n- pyproject.toml -> Python moderne"
  [ -n "$GO_MOD" ]        && DETECTED="$DETECTED\n- go.mod -> Go"
  [ -n "$CARGO" ]         && DETECTED="$DETECTED\n- Cargo.toml -> Rust"
  [ -n "$GEMFILE" ]       && DETECTED="$DETECTED\n- Gemfile -> Ruby"

  if [ -n "$PKG_JSON" ]; then
    grep -q '"react-native"' "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n- react-native -> React Native/Expo"
    grep -q '"next"'         "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n- next -> Next.js"
    grep -q '"vue"'          "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n- vue -> Vue.js"
  fi
  if [ -n "$REQUIREMENTS" ]; then
    grep -qi "django"  "$REQUIREMENTS" 2>/dev/null && DETECTED="$DETECTED\n- Django"
    grep -qi "fastapi" "$REQUIREMENTS" 2>/dev/null && DETECTED="$DETECTED\n- FastAPI"
    grep -qi "flask"   "$REQUIREMENTS" 2>/dev/null && DETECTED="$DETECTED\n- Flask"
    grep -qi "celery"  "$REQUIREMENTS" 2>/dev/null && DETECTED="$DETECTED\n- Celery"
  fi
  [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ] && DETECTED="$DETECTED\n- docker-compose -> Docker"
  [ -d "$PROJECT_ROOT/.github/workflows" ]  && DETECTED="$DETECTED\n- .github/workflows -> GitHub Actions"
  [ -f "$PROJECT_ROOT/vercel.json" ]        && DETECTED="$DETECTED\n- vercel.json -> Vercel"
  [ -f "$PROJECT_ROOT/fly.toml" ]           && DETECTED="$DETECTED\n- fly.toml -> Fly.io"
  grep -r "postgresql\|postgres" "$PROJECT_ROOT" --include="*.yml" --include="*.yaml" --include=".env.example" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- PostgreSQL detecte"
  grep -r "redis" "$PROJECT_ROOT" --include="*.yml" --include="*.yaml" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- Redis detecte"

  GIT_FILES=$(cd "$PROJECT_ROOT" && git ls-files 2>/dev/null | wc -l | tr -d ' ')
  LEGACY_NOTE=""
  [ "$GIT_FILES" -gt "10" ] 2>/dev/null && LEGACY_NOTE="PROJET LEGACY ($GIT_FILES fichiers git) - explore le codebase avant de remplir le manifest."

  DETECTED_CLEAN=$(printf "%b" "$DETECTED")
  STACK_SECTION="${DETECTED_CLEAN:-Projet vide ou nouveau.}"

  # ── Audit config Claude existante ──────────────────────────────────────────
  EXISTING_CLAUDE=""
  SETTINGS_FILE="$PROJECT_ROOT/.claude/settings.local.json"
  MCP_FILE="$PROJECT_ROOT/.mcp.json"
  HOOKS_DIR="$PROJECT_ROOT/.claude/hooks"
  KNOWN_HOOKS="session-start.sh user-prompt-submit.sh pre-bash-guard.sh post-edit.sh stop.sh pre-push.sh"

  if [ -f "$SETTINGS_FILE" ]; then
    PERM_COUNT=$(python3 -c "import json; d=json.load(open('$SETTINGS_FILE')); print(len(d.get('permissions',{}).get('allow',[])))" 2>/dev/null || echo "?")
    EXISTING_CLAUDE="$EXISTING_CLAUDE\n- .claude/settings.local.json ($PERM_COUNT permissions)"
  fi
  if [ -f "$MCP_FILE" ]; then
    MCP_SERVERS=$(python3 -c "import json; d=json.load(open('$MCP_FILE')); print(', '.join(d.get('mcpServers',{}).keys()))" 2>/dev/null || echo "?")
    EXISTING_CLAUDE="$EXISTING_CLAUDE\n- .mcp.json (serveurs: $MCP_SERVERS)"
  fi
  if [ -d "$HOOKS_DIR" ]; then
    CUSTOM_HOOKS=""
    for hook in "$HOOKS_DIR"/*.sh; do
      [ -f "$hook" ] || continue
      hname=$(basename "$hook")
      is_known=0
      for known in $KNOWN_HOOKS; do [ "$hname" = "$known" ] && is_known=1 && break; done
      [ "$is_known" -eq 0 ] && CUSTOM_HOOKS="$CUSTOM_HOOKS $hname"
    done
    [ -n "$CUSTOM_HOOKS" ] && EXISTING_CLAUDE="$EXISTING_CLAUDE\n- hooks custom (seront conservés) :$CUSTOM_HOOKS"
    [ -d "$HOOKS_DIR" ] && ls "$HOOKS_DIR"/*.sh &>/dev/null && EXISTING_CLAUDE="$EXISTING_CLAUDE\n- hooks claudekit existants (seront remplacés par gen.py)"
  fi

  EXISTING_CLAUDE_CLEAN=$(printf "%b" "$EXISTING_CLAUDE")

  python3 - "$LEGACY_NOTE" "$STACK_SECTION" "$EXISTING_CLAUDE_CLEAN" <<'PYEOF'
import json, sys
legacy = sys.argv[1]
stack = sys.argv[2]
existing_claude = sys.argv[3]
lines = ["=== SETUP REQUIS ==="]
if legacy:
    lines += ["", legacy]
lines += ["", "Stack detecte :", stack, ""]
if existing_claude.strip():
    lines += ["Config Claude existante detectee :"]
    lines += [existing_claude, ""]
    lines += ["IMPORTANT : Presente cette config a l'utilisateur avant de lancer gen.py."]
    lines += ["Demande ce qu'il veut conserver. Utilise --preserve-custom pour fusionner."]
    lines += [""]
lines += ["Instructions :"]
lines += ["1. Si legacy : explore d'abord (Glob/Grep) pour valider le stack"]
lines += ["2. Lance le SETUP INTERVIEW (CLAUDE.md) - questions une par une"]
lines += ["3. Pre-remplis depuis la detection ci-dessus, confirme avec l'utilisateur"]
lines += ["4. Ecris project.manifest.json"]
lines += ["5. Lance python3 scripts/gen.py --diff pour apercu des changements"]
lines += ["6. Si config existante a preserver : python3 scripts/gen.py --preserve-custom"]
lines += ["   Sinon : python3 scripts/gen.py"]
msg = "\n".join(lines)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
PYEOF
  exit 0
fi

# ─── Cas 2 : manifest rempli → injecter le contexte ──────────────────────────
MANIFEST=$(cat "$PROJECT_ROOT/project.manifest.json" 2>/dev/null || echo "{}")
CUSTOM_RULES=$(echo "$MANIFEST" | python3 -c "
import json,sys
d=json.load(sys.stdin)
rules=d.get('context',{}).get('custom_rules',[])
print('\n'.join(f'- {r}' for r in rules))
" 2>/dev/null || echo "")

GIT_STATUS=$(cd "$PROJECT_ROOT" && git status --short 2>/dev/null | head -20 || echo "pas de repo git")
GIT_BRANCH=$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo "inconnu")
GIT_LOG=$(cd "$PROJECT_ROOT" && git log --oneline -5 2>/dev/null || echo "")

LEARNING=""
if [ -f "$PROJECT_ROOT/$LEARNING_FILE" ]; then
  LEARNING=$(tail -60 "$PROJECT_ROOT/$LEARNING_FILE" 2>/dev/null || echo "")
fi

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" "$COMPACT_FOCUS" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
compact_focus = sys.argv[9] if len(sys.argv) > 9 else ""
ctx = f"=== {name} - SESSION START ===\n\nBranch: {branch}\nGit status:\n{status}\n\nCommits recents:\n{log}\n\nManifest:\n{manifest}\n\nRegles custom:\n{rules}\n\n{lfile} (dernieres 60 lignes):\n{learning}"
if compact_focus:
    ctx += f"\n\nContexte compact (focus) : {compact_focus}"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
