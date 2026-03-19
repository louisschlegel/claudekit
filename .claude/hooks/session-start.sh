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
lines += ["", "⚡ ACTION IMMÉDIATE : Lance le SETUP INTERVIEW maintenant, sans attendre de message utilisateur.", ""]
if legacy:
    lines += [legacy, ""]
lines += ["Stack detecte :", stack, ""]
lines += ["Deroulement :"]
lines += ["1. Presente le recap de detection (stack)"]
lines += ["2. Si legacy : explore le codebase (Glob/Grep) pour valider"]
lines += ["3. Lance le SETUP INTERVIEW (CLAUDE.md) question par question"]
lines += ["4. Ecris project.manifest.json"]
lines += ["5. python3 scripts/gen.py --diff  →  montre les changements"]
lines += ["6. python3 scripts/gen.py"]
lines += ["7. Demande a l'utilisateur de redemarrer Claude Code"]
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

# ─── Signal 1 — Coverage de tests ────────────────────────────────────────────
COVERAGE=""
# Python : coverage.xml
if [ -f "$PROJECT_ROOT/coverage.xml" ]; then
  COV_PCT=$(python3 -c "
import xml.etree.ElementTree as ET, sys
try:
    tree = ET.parse('$PROJECT_ROOT/coverage.xml')
    root = tree.getroot()
    line_rate = root.get('line-rate') or root.find('.').get('line-rate','')
    if line_rate:
        print(str(round(float(line_rate)*100)) + '%')
except:
    pass
" 2>/dev/null || echo "")
  [ -n "$COV_PCT" ] && COVERAGE="Coverage: $COV_PCT"
fi
# Node : coverage/coverage-summary.json
if [ -z "$COVERAGE" ] && [ -f "$PROJECT_ROOT/coverage/coverage-summary.json" ]; then
  COV_PCT=$(python3 -c "
import json, sys
try:
    d = json.load(open('$PROJECT_ROOT/coverage/coverage-summary.json'))
    total = d.get('total', {})
    lines = total.get('lines', {})
    pct = lines.get('pct')
    if pct is not None:
        print(str(pct) + '%')
except:
    pass
" 2>/dev/null || echo "")
  [ -n "$COV_PCT" ] && COVERAGE="Coverage: $COV_PCT"
fi
# Node : coverage/lcov-report/index.html (dernier recours)
if [ -z "$COVERAGE" ] && [ -f "$PROJECT_ROOT/coverage/lcov-report/index.html" ]; then
  COV_PCT=$(python3 -c "
import re
try:
    content = open('$PROJECT_ROOT/coverage/lcov-report/index.html').read()
    m = re.search(r'(\d+\.?\d*)\s*%\s*<[^>]*>Lines', content)
    if not m:
        m = re.search(r'strong[^>]*>(\d+\.?\d*)%</strong>', content)
    if m:
        print(m.group(1) + '%')
except:
    pass
" 2>/dev/null || echo "")
  [ -n "$COV_PCT" ] && COVERAGE="Coverage: $COV_PCT"
fi
[ -z "$COVERAGE" ] && COVERAGE="Coverage: non mesuré"

# ─── Signal 2 — Migrations en attente (Django) ───────────────────────────────
PENDING_MIGRATIONS=""
DJANGO_IN_MANIFEST=$(echo "$MANIFEST" | python3 -c "
import json,sys
d=json.load(sys.stdin)
frameworks=d.get('stack',{}).get('frameworks',[])
print('yes' if any('django' in str(f).lower() for f in frameworks) else '')
" 2>/dev/null || echo "")
if [ -n "$DJANGO_IN_MANIFEST" ]; then
  if [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ]; then
    PENDING_MIGRATIONS=$(timeout 3 bash -c "cd '$PROJECT_ROOT' && python3 manage.py showmigrations --plan 2>/dev/null | grep -c '\[ \]'" 2>/dev/null || echo "")
    [ -n "$PENDING_MIGRATIONS" ] && [ "$PENDING_MIGRATIONS" -gt 0 ] 2>/dev/null && PENDING_MIGRATIONS="${PENDING_MIGRATIONS} migrations non appliquées" || PENDING_MIGRATIONS=""
  fi
fi

# ─── Signal 3 — Dépendances vulnérables ──────────────────────────────────────
DEPS_ALERT=""
# Python : pip-audit
if [ -f "$PROJECT_ROOT/requirements.txt" ] || [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
  VULN_COUNT=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && pip-audit --format=json 2>/dev/null | python3 -c \"
import json,sys
try:
    data=json.load(sys.stdin)
    vulns=data.get('vulnerabilities',[]) if isinstance(data,dict) else data
    count=len([v for v in vulns if isinstance(v,dict)])
    print(count if count>0 else '')
except:
    pass
\"" 2>/dev/null || echo "")
  [ -n "$VULN_COUNT" ] && DEPS_ALERT="$VULN_COUNT vulnérabilités détectées dans les deps Python"
fi
# Node : npm audit
if [ -z "$DEPS_ALERT" ] && [ -f "$PROJECT_ROOT/package.json" ]; then
  VULN_COUNT=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && npm audit --json 2>/dev/null | python3 -c \"
import json,sys
try:
    data=json.load(sys.stdin)
    meta=data.get('metadata',{})
    vulns=meta.get('vulnerabilities',{})
    high=vulns.get('high',0)+vulns.get('critical',0)
    print(high if high>0 else '')
except:
    pass
\"" 2>/dev/null || echo "")
  [ -n "$VULN_COUNT" ] && DEPS_ALERT="$VULN_COUNT vulnérabilités HIGH/CRITICAL dans les deps Node"
fi

# ─── Signal 4 — Branches feature vieilles (> 14 jours) ──────────────────────
OLD_BRANCHES=""
OLD_BRANCHES_RAW=$(cd "$PROJECT_ROOT" && git for-each-ref \
  --sort=committerdate \
  --format='%(refname:short)|%(committerdate:relative)|%(committerdate:unix)' \
  refs/heads/ 2>/dev/null \
  | grep -v "^main\|^master\|^develop\|^staging\|^production" \
  | python3 -c "
import sys, time
threshold = time.time() - 14*24*3600
alerts = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split('|')
    if len(parts) < 3:
        continue
    name, rel, ts = parts[0], parts[1], parts[2]
    try:
        if int(ts) < threshold:
            alerts.append(f'{name} (dernière activité : {rel})')
    except:
        pass
print('\n'.join(alerts[:5]))
" 2>/dev/null || echo "")
[ -n "$OLD_BRANCHES_RAW" ] && OLD_BRANCHES="$OLD_BRANCHES_RAW"

# ─── Signal 5 — État CI/CD ────────────────────────────────────────────────────
CI_STATUS=""
if [ -d "$PROJECT_ROOT/.github/workflows" ]; then
  WF_COUNT=$(ls "$PROJECT_ROOT/.github/workflows/"*.yml "$PROJECT_ROOT/.github/workflows/"*.yaml 2>/dev/null | wc -l | tr -d ' ')
  GH_RUN=$(timeout 5 bash -c "cd '$PROJECT_ROOT' && gh run list --limit 1 --json status,conclusion,name 2>/dev/null | python3 -c \"
import json,sys
try:
    runs=json.load(sys.stdin)
    if runs:
        r=runs[0]
        name=r.get('name','')
        status=r.get('status','')
        conclusion=r.get('conclusion','')
        label=conclusion if conclusion else status
        print(f'{name}: {label}')
except:
    pass
\"" 2>/dev/null || echo "")
  if [ -n "$GH_RUN" ]; then
    CI_STATUS="$WF_COUNT workflow(s) GitHub Actions — dernier run: $GH_RUN"
  else
    CI_STATUS="$WF_COUNT workflow(s) GitHub Actions configuré(s) — status non disponible sans GitHub MCP"
  fi
elif [ -f "$PROJECT_ROOT/.gitlab-ci.yml" ]; then
  CI_STATUS="GitLab CI configuré — status non disponible localement"
elif [ -f "$PROJECT_ROOT/Jenkinsfile" ]; then
  CI_STATUS="Jenkins configuré — status non disponible localement"
fi

# ─── Signal 6 — Fichiers souvent modifiés sans tests (friction detector) ─────
HOT_FILES=""
HOT_FILES_RAW=$(cd "$PROJECT_ROOT" && git log --oneline -20 --name-only 2>/dev/null \
  | grep -v "^[a-f0-9]\{7,\} " \
  | grep -v "^\s*$" \
  | grep -v "test_\|\.test\.\|_test\.\|\.spec\.\|__tests__" \
  | sort | uniq -c | sort -rn \
  | python3 -c "
import sys, os
alerts = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split(None, 1)
    if len(parts) < 2:
        continue
    count, filepath = parts
    try:
        count = int(count)
    except:
        continue
    if count < 3:
        break
    basename = os.path.basename(filepath)
    dirname = os.path.dirname(filepath)
    name_no_ext = os.path.splitext(basename)[0]
    test_patterns = [
        f'test_{name_no_ext}', f'{name_no_ext}_test',
        f'{name_no_ext}.test', f'{name_no_ext}.spec',
    ]
    alerts.append(f'{filepath} modifié {count}x récemment (pas de test détecté dans le nom)')
print('\n'.join(alerts[:3]))
" 2>/dev/null || echo "")
[ -n "$HOT_FILES_RAW" ] && HOT_FILES="$HOT_FILES_RAW"

# ─── Signal 7 — Dette technique visible ──────────────────────────────────────
TECH_DEBT=""
DEBT_COUNT=$(grep -r "TODO\|FIXME\|HACK\|XXX" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.js" --include="*.jsx" --include="*.go" \
  --include="*.rs" --include="*.rb" --include="*.java" \
  -l "$PROJECT_ROOT" 2>/dev/null \
  | grep -v "node_modules\|\.git\|vendor\|dist\|build\|\.next\|coverage" \
  | wc -l | tr -d ' ')
[ -n "$DEBT_COUNT" ] && [ "$DEBT_COUNT" -gt 0 ] 2>/dev/null && TECH_DEBT="$DEBT_COUNT fichier(s) contiennent des TODO/FIXME/HACK" || TECH_DEBT=""

# ─── Signal 8 — Documentation disponible (Option A: auto-detect) ──────────────
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

# ─── Signal 9 — Docs content injection (Option B: manifest.context.docs_paths) ─
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
        preview = lines[:100]
        content = '\n'.join(preview)
        if len(lines) > 100:
            content += f'\n... ({len(lines) - 100} lignes supplémentaires — utilisez Read pour la suite)'
        sections.append(f'--- {p} ---\n{content}')
    except Exception as e:
        sections.append(f'[{p}] → erreur lecture: {e}')
print('\n\n'.join(sections))
" 2>/dev/null || echo "")

# ─── Signal 10 — Compact focus (manifest.context.compact_focus) ───────────────
COMPACT_FOCUS=$(echo "$MANIFEST" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('context',{}).get('compact_focus',''))
" 2>/dev/null || echo "")

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" "$COVERAGE" "$DEPS_ALERT" "$CI_STATUS" "$TECH_DEBT" "$OLD_BRANCHES" "$HOT_FILES" "$PENDING_MIGRATIONS" "$DOCS_LIST" "$DOCS_CONTENT" "$COMPACT_FOCUS" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
coverage, deps_alert, ci_status, tech_debt = sys.argv[9:13]
old_branches, hot_files, pending_migrations = sys.argv[13:16]
docs_list, docs_content = sys.argv[16:18]
compact_focus = sys.argv[18] if len(sys.argv) > 18 else ""

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

# Section état opérationnel
op_lines = ["", "=== ETAT OPERATIONNEL ===", ""]
op_lines.append(f"Tests: {coverage}")
op_lines.append(f"Securite: {'⚠️  ' + deps_alert if deps_alert else 'deps OK'}")
op_lines.append(f"CI/CD: {ci_status if ci_status else 'non configuré'}")
op_lines.append(f"Dette: {tech_debt if tech_debt else 'aucun TODO/FIXME détecté'}")

alerts = []
if old_branches:
    for line in old_branches.strip().splitlines():
        if line.strip():
            alerts.append(f"  Branch ancienne : {line.strip()}")
if hot_files:
    for line in hot_files.strip().splitlines():
        if line.strip():
            alerts.append(f"  Fichier chaud : {line.strip()}")
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
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
