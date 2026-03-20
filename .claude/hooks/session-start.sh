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
  KNOWN_HOOKS="session-start.sh user-prompt-submit.sh pre-bash-guard.sh post-edit.sh stop.sh pre-push.sh pre-compact.sh notification.sh subagent-stop.sh observability.sh injection-defender.sh context-monitor.sh live-handoff.sh stop-guard.sh session-end.sh permission-auto.sh tool-failure.sh test-filter.sh manifest-regen.sh"

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

  # Show a visible message to the user in the terminal
  echo "" >&2
  echo -e "\033[1;33m╔══════════════════════════════════════════════════════════╗\033[0m" >&2
  echo -e "\033[1;33m║  claudekit — Setup requis                               ║\033[0m" >&2
  echo -e "\033[1;33m║  Claude va te poser quelques questions pour configurer.  ║\033[0m" >&2
  echo -e "\033[1;33m║  Tape juste Enter ou attends — il démarre tout seul.    ║\033[0m" >&2
  echo -e "\033[1;33m╚══════════════════════════════════════════════════════════╝\033[0m" >&2
  echo "" >&2

  python3 - "$LEGACY_NOTE" "$STACK_SECTION" "$EXISTING_CLAUDE_CLEAN" <<'PYEOF'
import json, sys
legacy = sys.argv[1]
stack = sys.argv[2]
existing_claude = sys.argv[3]
lines = ["=== SETUP REQUIS ==="]
lines += ["", "⚡ ACTION IMMÉDIATE : Lance le SETUP INTERVIEW maintenant, sans attendre de message utilisateur. Ne reste pas silencieux — l'utilisateur voit un prompt vide et attend que tu parles.", ""]
if legacy:
    lines += [legacy, ""]
lines += ["Stack detecte :", stack, ""]
if existing_claude.strip():
    lines += ["Config Claude existante detectee :"]
    lines += [existing_claude, ""]
    lines += ["→ Presente cette config a l'utilisateur AVANT de lancer gen.py."]
    lines += ["→ Demande ce qu'il veut conserver. Utilise --preserve-custom pour fusionner.", ""]
lines += ["Deroulement :"]
lines += ["1. Presente le recap de detection (stack + config existante)"]
lines += ["2. Si legacy : explore le codebase (Glob/Grep) pour valider"]
lines += ["3. Lance le SETUP INTERVIEW (CLAUDE.md) question par question"]
lines += ["4. Ecris project.manifest.json"]
lines += ["5. python3 scripts/gen.py --diff  →  montre les changements"]
lines += ["6. python3 scripts/gen.py --preserve-custom  (si config existante)"]
lines += ["   ou  python3 scripts/gen.py  (sinon)"]
lines += ["7. Demande a l'utilisateur de redemarrer Claude Code"]
msg = "\n".join(lines)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}}))
PYEOF
  exit 0
fi

# ─── Auto-regen si manifest a changé depuis dernière gen ─────────────────────
HASH_FILE="$PROJECT_ROOT/.template/manifest.hash"
MANIFEST_FILE="$PROJECT_ROOT/project.manifest.json"
CURRENT_HASH=$(python3 -c "import hashlib; print(hashlib.md5(open('$MANIFEST_FILE','rb').read()).hexdigest())" 2>/dev/null || echo "")
STORED_HASH=$(cat "$HASH_FILE" 2>/dev/null || echo "")

if [ -n "$CURRENT_HASH" ] && [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
  # Try --quiet first, fall back to without it (older gen.py versions)
  (python3 "$PROJECT_ROOT/scripts/gen.py" --quiet 2>/dev/null || python3 "$PROJECT_ROOT/scripts/gen.py" 2>/dev/null) && \
    echo "$CURRENT_HASH" > "$HASH_FILE" && \
    REGEN_NOTE="⚡ project.manifest.json modifié — config régénérée automatiquement." || \
    REGEN_NOTE=""
fi

# ─── Check claudekit updates (daily, cached) ─────────────────────────────────
UPDATE_NOTE=""
UPDATE_CACHE="$PROJECT_ROOT/.template/update-check.json"
VERSION_FILE="$PROJECT_ROOT/.template/version.json"
if [ -f "$VERSION_FILE" ]; then
  UPDATE_NOTE=$(python3 - "$VERSION_FILE" "$UPDATE_CACHE" << 'PYUPDATE'
import json, sys, os, time
from pathlib import Path

version_file = Path(sys.argv[1])
cache_file = Path(sys.argv[2])

# Only check once per day
if cache_file.exists():
    try:
        cache = json.loads(cache_file.read_text())
        if time.time() - cache.get("checked_at", 0) < 86400:
            if cache.get("update_available"):
                print(f"📦 claudekit {cache['latest']} disponible (actuel: {cache['current']}). Utilise /update-claudekit pour mettre à jour.")
            sys.exit(0)
    except:
        pass

current = json.loads(version_file.read_text()).get("version", "0.0.0")

# Try to fetch latest version (non-blocking, 3s timeout)
try:
    import urllib.request
    req = urllib.request.Request(
        "https://api.github.com/repos/louisschlegel/claudekit/releases/latest",
        headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "claudekit"}
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read())
        latest = data.get("tag_name", "").lstrip("v")
except:
    latest = current

cache_data = {
    "checked_at": time.time(),
    "current": current,
    "latest": latest,
    "update_available": latest != current and latest > current
}
cache_file.parent.mkdir(parents=True, exist_ok=True)
cache_file.write_text(json.dumps(cache_data))

if cache_data["update_available"]:
    # Fetch release notes to detect new configurable features
    new_features = []
    try:
        body = data.get("body", "")
        # Detect new configurable items in release notes
        config_keywords = ["toggle", "flag", "automation.", "manifest", "configurable", "setting", "enable", "disable"]
        for line in body.split("\n"):
            if any(kw in line.lower() for kw in config_keywords):
                clean = line.strip().lstrip("-* ")
                if clean and len(clean) < 120:
                    new_features.append(clean)
    except:
        pass

    msg = f"📦 claudekit {latest} disponible (actuel: {current})."
    if new_features:
        msg += f"\n\n🆕 Nouvelles options configurables dans {latest} :"
        for f in new_features[:5]:
            msg += f"\n  • {f}"
        msg += "\n\n→ Utilise /update-claudekit pour mettre à jour, puis Claude te proposera de configurer les nouvelles options."
    else:
        msg += " Utilise /update-claudekit pour mettre à jour."
    print(msg)
PYUPDATE
2>/dev/null || echo "")
fi

# ─── Check dépendances recommandées ──────────────────────────────────────────
MISSING_DEPS=""
if [[ "$(uname)" == "Darwin" ]]; then
  command -v terminal-notifier &>/dev/null || MISSING_DEPS="${MISSING_DEPS}\n- terminal-notifier (brew install terminal-notifier) — évite que les notifs ouvrent Script Editor"
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

# ─── Signal 1 — Coverage de tests ────────────────────────────────────────────
COVERAGE=""
if [ -f "$PROJECT_ROOT/coverage.xml" ]; then
  COV_PCT=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    root = ET.parse('$PROJECT_ROOT/coverage.xml').getroot()
    lr = root.get('line-rate','')
    if lr: print(str(round(float(lr)*100)) + '%')
except: pass
" 2>/dev/null || echo "")
  [ -n "$COV_PCT" ] && COVERAGE="Coverage: $COV_PCT"
fi
if [ -z "$COVERAGE" ] && [ -f "$PROJECT_ROOT/coverage/coverage-summary.json" ]; then
  COV_PCT=$(python3 -c "
import json
try:
    d=json.load(open('$PROJECT_ROOT/coverage/coverage-summary.json'))
    pct=d.get('total',{}).get('lines',{}).get('pct')
    if pct is not None: print(str(pct)+'%')
except: pass
" 2>/dev/null || echo "")
  [ -n "$COV_PCT" ] && COVERAGE="Coverage: $COV_PCT"
fi
[ -z "$COVERAGE" ] && COVERAGE="Coverage: non mesuré"

# ─── Signal 2 — Dépendances vulnérables ──────────────────────────────────────
DEPS_ALERT=""
if [ -f "$PROJECT_ROOT/requirements.txt" ] || [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
  VULN_COUNT=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && pip-audit --format=json 2>/dev/null | python3 -c \"
import json,sys
try:
    data=json.load(sys.stdin)
    vulns=data.get('vulnerabilities',[]) if isinstance(data,dict) else data
    count=len([v for v in vulns if isinstance(v,dict)])
    print(count if count>0 else '')
except: pass
\"" 2>/dev/null || echo "")
  [ -n "$VULN_COUNT" ] && DEPS_ALERT="$VULN_COUNT vulnérabilités dans les deps Python"
fi
if [ -z "$DEPS_ALERT" ] && [ -f "$PROJECT_ROOT/package.json" ]; then
  VULN_COUNT=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && npm audit --json 2>/dev/null | python3 -c \"
import json,sys
try:
    data=json.load(sys.stdin)
    v=data.get('metadata',{}).get('vulnerabilities',{})
    high=v.get('high',0)+v.get('critical',0)
    print(high if high>0 else '')
except: pass
\"" 2>/dev/null || echo "")
  [ -n "$VULN_COUNT" ] && DEPS_ALERT="$VULN_COUNT vulnérabilités HIGH/CRITICAL dans les deps Node"
fi

# ─── Signal 3 — CI/CD ────────────────────────────────────────────────────────
CI_STATUS=""
if [ -d "$PROJECT_ROOT/.github/workflows" ]; then
  WF_COUNT=$(ls "$PROJECT_ROOT/.github/workflows/"*.yml "$PROJECT_ROOT/.github/workflows/"*.yaml 2>/dev/null | wc -l | tr -d ' ')
  GH_RUN=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && gh run list --limit 1 --json status,conclusion,name 2>/dev/null | python3 -c \"
import json,sys
try:
    runs=json.load(sys.stdin)
    if runs:
        r=runs[0]; label=r.get('conclusion') or r.get('status','')
        print(f\\\"{r.get('name','')}: {label}\\\")
except: pass
\"" 2>/dev/null || echo "")
  CI_STATUS="$WF_COUNT workflow(s) GitHub Actions${GH_RUN:+ — dernier run: $GH_RUN}"
fi

# ─── Signal 4 — Dette technique ──────────────────────────────────────────────
TECH_DEBT=""
DEBT_COUNT=$(grep -r "TODO\|FIXME\|HACK\|XXX" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.js" --include="*.go" --include="*.rs" --include="*.rb" \
  -l "$PROJECT_ROOT" 2>/dev/null \
  | grep -v "node_modules\|\.git\|vendor\|dist\|build" \
  | wc -l | tr -d ' ')
[ -n "$DEBT_COUNT" ] && [ "$DEBT_COUNT" -gt 0 ] 2>/dev/null && TECH_DEBT="$DEBT_COUNT fichier(s) contiennent des TODO/FIXME/HACK" || TECH_DEBT=""

# ─── Signal 5 — Branches anciennes ───────────────────────────────────────────
OLD_BRANCHES=$(cd "$PROJECT_ROOT" && git for-each-ref \
  --sort=committerdate \
  --format='%(refname:short)|%(committerdate:relative)|%(committerdate:unix)' \
  refs/heads/ 2>/dev/null \
  | grep -v "^main\|^master\|^develop\|^staging" \
  | python3 -c "
import sys, time
threshold = time.time() - 14*24*3600
alerts = []
for line in sys.stdin:
    parts = line.strip().split('|')
    if len(parts) < 3: continue
    name, rel, ts = parts
    try:
        if int(ts) < threshold:
            alerts.append(f'{name} (dernière activité : {rel})')
    except: pass
print('\n'.join(alerts[:5]))
" 2>/dev/null || echo "")

# ─── Signal 6 — Fichiers chauds sans tests ───────────────────────────────────
HOT_FILES=$(cd "$PROJECT_ROOT" && git log --oneline -20 --name-only 2>/dev/null \
  | grep -v "^[a-f0-9]\{7,\} " | grep -v "^\s*$" \
  | grep -v "test_\|\.test\.\|_test\.\|\.spec\." \
  | sort | uniq -c | sort -rn \
  | python3 -c "
import sys, os
alerts = []
for line in sys.stdin:
    parts = line.strip().split(None, 1)
    if len(parts) < 2: continue
    try:
        count = int(parts[0])
    except: continue
    if count < 3: break
    alerts.append(f'{parts[1]} modifié {count}x récemment (pas de test détecté dans le nom)')
print('\n'.join(alerts[:3]))
" 2>/dev/null || echo "")

# ─── Signal 7 — Migrations en attente ────────────────────────────────────────
PENDING_MIGRATIONS=""
DJANGO_IN_MANIFEST=$(echo "$MANIFEST" | python3 -c "
import json,sys
d=json.load(sys.stdin)
fw=d.get('stack',{}).get('frameworks',[])
print('yes' if any('django' in str(f).lower() for f in fw) else '')
" 2>/dev/null || echo "")
if [ -n "$DJANGO_IN_MANIFEST" ]; then
  PENDING_MIGRATIONS=$(timeout 3 bash -c "cd '$PROJECT_ROOT' && python3 manage.py showmigrations --plan 2>/dev/null | grep -c '\[ \]'" 2>/dev/null || echo "")
  [ -n "$PENDING_MIGRATIONS" ] && [ "$PENDING_MIGRATIONS" -gt 0 ] 2>/dev/null && PENDING_MIGRATIONS="${PENDING_MIGRATIONS} migrations non appliquées" || PENDING_MIGRATIONS=""
fi

# ─── Signal 8 — Documentation disponible (auto-detect) ───────────────────────
DOCS_LIST=$(python3 - "$PROJECT_ROOT" <<'PYDOCS'
import sys
from pathlib import Path
root = Path(sys.argv[1])
docs = []
for name in ['README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'ARCHITECTURE.md', 'ROADMAP.md', 'SECURITY.md']:
    if (root / name).exists():
        docs.append(name)
for f in sorted(root.glob('*.pdf')):
    docs.append(f.name + ' (PDF)')
for folder in ['docs', 'doc', 'spec', 'specs', 'adr', 'ADR', 'architecture', 'design', 'wiki', 'documentation']:
    d = root / folder
    if d.is_dir():
        for f in sorted(d.rglob('*')):
            if f.suffix.lower() in ('.md', '.pdf', '.rst'):
                rel = str(f.relative_to(root))
                if not any(x in rel for x in ('.git', 'node_modules', 'vendor')):
                    docs.append(rel + (' (PDF)' if f.suffix.lower() == '.pdf' else ''))
print('\n'.join(docs[:30]))
PYDOCS
2>/dev/null || echo "")

# ─── Signal 9 — Docs content injection (manifest.context.docs_paths) ─────────
DOCS_CONTENT=$(echo "$MANIFEST" | python3 -c "
import json, sys
from pathlib import Path
root = Path('$PROJECT_ROOT')
manifest = json.load(sys.stdin)
paths = manifest.get('context', {}).get('docs_paths', [])
sections = []
for p in paths:
    f = root / p
    if not f.exists():
        sections.append(f'[{p}] → fichier non trouvé')
        continue
    if f.suffix.lower() == '.pdf':
        sections.append(f'[{p}] → PDF (utilisez le tool Read pour accéder au contenu)')
        continue
    try:
        lines = f.read_text(encoding='utf-8', errors='replace').splitlines()
        content = '\n'.join(lines[:100])
        if len(lines) > 100:
            content += f'\n... ({len(lines) - 100} lignes supplémentaires — utilisez Read pour la suite)'
        sections.append(f'--- {p} ---\n{content}')
    except Exception as e:
        sections.append(f'[{p}] → erreur lecture: {e}')
print('\n\n'.join(sections))
" 2>/dev/null || echo "")

# ─── Signal 10 — Compact focus (manifest.context.compact_focus) ──────────────
COMPACT_FOCUS=$(echo "$MANIFEST" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('context',{}).get('compact_focus',''))
" 2>/dev/null || echo "")

# ─── Signal 11 — Agent mode (manifest.automation.agent_mode) ─────────────────
AGENT_MODE=$(echo "$MANIFEST" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('automation',{}).get('agent_mode','mono'))" 2>/dev/null || echo "mono")

# ─── Signal 12 — Token usage from last session ────────────────────────────────
LAST_USAGE=""
USAGE_FILE="$PROJECT_ROOT/.template/usage.jsonl"
if [ -f "$USAGE_FILE" ]; then
  LAST_USAGE=$(tail -5 "$USAGE_FILE" 2>/dev/null | python3 -c "
import json, sys
lines = [l for l in sys.stdin if l.strip()]
if not lines: exit()
total_input = sum(json.loads(l).get('input_tokens', 0) for l in lines if l.strip())
total_output = sum(json.loads(l).get('output_tokens', 0) for l in lines if l.strip())
# Approximate cost: Sonnet input=\$3/Mtok, output=\$15/Mtok
cost = (total_input * 3 + total_output * 15) / 1_000_000
print(f'~\${cost:.3f} (last 5 sessions: {total_input:,} in + {total_output:,} out tokens)')
" 2>/dev/null || echo "")
fi

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" "$COVERAGE" "$DEPS_ALERT" "$CI_STATUS" "$TECH_DEBT" "$OLD_BRANCHES" "$HOT_FILES" "$PENDING_MIGRATIONS" "$DOCS_LIST" "$DOCS_CONTENT" "$COMPACT_FOCUS" "$AGENT_MODE" "$LAST_USAGE" "${REGEN_NOTE:-}" "${MISSING_DEPS:-}" "${UPDATE_NOTE:-}" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
coverage, deps_alert, ci_status, tech_debt = sys.argv[9:13]
old_branches, hot_files, pending_migrations = sys.argv[13:16]
docs_list, docs_content = sys.argv[16:18]
compact_focus = sys.argv[18] if len(sys.argv) > 18 else ""
agent_mode = sys.argv[19] if len(sys.argv) > 19 else "mono"
last_usage = sys.argv[20] if len(sys.argv) > 20 else ""
regen_note = sys.argv[21] if len(sys.argv) > 21 else ""
missing_deps = sys.argv[22] if len(sys.argv) > 22 else ""
update_note = sys.argv[23] if len(sys.argv) > 23 else ""

ctx = "\n".join([
    f"=== {name} - SESSION START ===",
    "",
    f"Branch: {branch}",
    f"Git status:\n{status}",
    "",
    f"Commits recents:\n{log}",
    "",
    f"Manifest:\n{manifest}",
])

op_lines = ["", "=== ETAT OPERATIONNEL ===", ""]
op_lines.append(f"Tests: {coverage}")
op_lines.append(f"Securite: {'⚠️  ' + deps_alert if deps_alert else 'deps OK'}")
op_lines.append(f"CI/CD: {ci_status if ci_status else 'non configuré'}")
op_lines.append(f"Dette: {tech_debt if tech_debt else 'aucun TODO/FIXME détecté'}")
op_lines.append(f"Agent mode: {agent_mode} ({'parallel worktrees recommended for large tasks' if agent_mode == 'team' else 'single agent'})")
if last_usage:
    op_lines.append(f"Token cost: {last_usage}")

alerts = []
if old_branches:
    for line in old_branches.strip().splitlines():
        if line.strip(): alerts.append(f"  Branch ancienne : {line.strip()}")
if hot_files:
    for line in hot_files.strip().splitlines():
        if line.strip(): alerts.append(f"  Fichier chaud : {line.strip()}")
if pending_migrations:
    alerts.append(f"  Migrations : {pending_migrations}")

if alerts:
    op_lines.append("")
    op_lines.append("Points d'attention:")
    op_lines.extend(alerts)

ctx += "\n".join(op_lines)

if docs_list.strip():
    ctx += f"\n\n=== DOCUMENTATION DISPONIBLE ===\n{docs_list}"
if docs_content.strip():
    ctx += f"\n\n=== CONTENU DOCS (context.docs_paths) ===\n{docs_content}"
if rules:
    ctx += f"\n\nRegles custom:\n{rules}"
ctx += f"\n\n{lfile} (dernieres 60 lignes):\n{learning}"
if compact_focus:
    ctx += f"\n\nContexte compact (focus) : {compact_focus}"
ctx += f"\nAgent mode: {agent_mode} ({'parallel worktrees for large tasks' if agent_mode == 'team' else 'single agent'})"
if last_usage:
    ctx += f"\nCost estimate: {last_usage}"
if regen_note:
    ctx += f"\n\n{regen_note}"
if missing_deps.strip():
    import re
    deps = [d.strip() for d in re.split(r'\\n', missing_deps) if d.strip()]
    ctx += f"\n\n=== DÉPENDANCES RECOMMANDÉES MANQUANTES ===\n" + "\n".join(deps)
if update_note:
    ctx += f"\n\n{update_note}"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
