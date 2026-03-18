#!/usr/bin/env python3
"""
gen.py — Générateur de config Claude Code depuis project.manifest.json

Usage:
    python3 scripts/gen.py

Génère:
    .claude/settings.local.json   (permissions + hooks)
    .mcp.json                     (MCP servers, si définis)
    .claude/hooks/*.sh             (mise à jour des hooks existants)
"""

import json
import os
import sys
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
MANIFEST_PATH = ROOT / "project.manifest.json"
SETTINGS_PATH = ROOT / ".claude" / "settings.local.json"
MCP_PATH = ROOT / ".mcp.json"
HOOKS_DIR = ROOT / ".claude" / "hooks"


# ─── Permissions base (toujours incluses) ────────────────────────────────────
BASE_PERMISSIONS = [
    "Bash(git:*)",
    "Bash(ls:*)",
    "Bash(find:*)",
    "Bash(cat:*)",
    "Bash(head:*)",
    "Bash(tail:*)",
    "Bash(grep:*)",
    "Bash(sed:*)",
    "Bash(awk:*)",
    "Bash(wc:*)",
    "Bash(sort:*)",
    "Bash(diff:*)",
    "Bash(echo:*)",
    "Bash(xargs:*)",
    "Bash(mkdir:*)",
    "Bash(cp:*)",
    "Bash(mv:*)",
    "Bash(touch:*)",
    "Bash(chmod:*)",
    "Bash(which:*)",
    "Bash(pwd:*)",
    "Bash(date:*)",
    "Bash(test:*)",
    "Bash(curl:*)",
    "Bash(jq:*)",
    "Bash(tree:*)",
    "Bash(python3:*)",
    "Bash(timeout:*)",
    "Bash(for:*)",
    "Bash(while:*)",
    "WebFetch(domain:localhost)",
    "WebFetch(domain:github.com)",
    "Skill(update-config)",
]

# ─── Permissions par langage/framework ───────────────────────────────────────
STACK_PERMISSIONS = {
    # Web / Backend
    "python": ["Bash(python:*)", "Bash(pip:*)", "Bash(pip3:*)", "Bash(uv:*)", "Bash(poetry:*)", "Bash(ruff:*)", "Bash(mypy:*)", "Bash(pytest:*)", "Bash(uvicorn:*)", "Bash(gunicorn:*)", "Bash(celery:*)", "Bash(alembic:*)"],
    "typescript": ["Bash(npm:*)", "Bash(npx:*)", "Bash(node:*)", "Bash(tsc:*)", "Bash(eslint:*)", "Bash(biome:*)", "Bash(vitest:*)", "Bash(pnpm:*)"],
    "javascript": ["Bash(npm:*)", "Bash(npx:*)", "Bash(node:*)", "Bash(eslint:*)", "Bash(biome:*)", "Bash(pnpm:*)"],
    "go": ["Bash(go:*)", "Bash(golangci-lint:*)", "Bash(govulncheck:*)"],
    "rust": ["Bash(cargo:*)", "Bash(rustc:*)", "Bash(rustfmt:*)", "Bash(clippy:*)"],
    "ruby": ["Bash(ruby:*)", "Bash(bundle:*)", "Bash(rails:*)", "Bash(rake:*)", "Bash(rspec:*)", "Bash(rubocop:*)"],
    "php": ["Bash(php:*)", "Bash(composer:*)", "Bash(artisan:*)", "Bash(phpunit:*)", "Bash(php-cs-fixer:*)"],
    "java": ["Bash(java:*)", "Bash(javac:*)", "Bash(mvn:*)", "Bash(gradle:*)", "Bash(gradlew:*)", "Bash(./gradlew:*)"],
    "elixir": ["Bash(mix:*)", "Bash(iex:*)", "Bash(elixir:*)"],
    "swift": ["Bash(swift:*)", "Bash(xcodebuild:*)", "Bash(xcrun:*)", "Bash(pod:*)", "Bash(swift-format:*)"],
    "kotlin": ["Bash(kotlin:*)", "Bash(gradle:*)", "Bash(gradlew:*)", "Bash(./gradlew:*)", "Bash(ktlint:*)"],
    # Systems / Compiled
    "c": ["Bash(gcc:*)", "Bash(clang:*)", "Bash(clang++:*)", "Bash(cmake:*)", "Bash(make:*)", "Bash(ninja:*)", "Bash(valgrind:*)", "Bash(gdb:*)", "Bash(ctest:*)", "Bash(bear:*)"],
    "c++": ["Bash(g++:*)", "Bash(clang++:*)", "Bash(cmake:*)", "Bash(make:*)", "Bash(ninja:*)", "Bash(valgrind:*)", "Bash(gdb:*)", "Bash(ctest:*)", "Bash(conan:*)"],
    "cpp": ["Bash(g++:*)", "Bash(clang++:*)", "Bash(cmake:*)", "Bash(make:*)", "Bash(ninja:*)", "Bash(valgrind:*)", "Bash(gdb:*)", "Bash(ctest:*)", "Bash(conan:*)"],
    # .NET ecosystem
    "csharp": ["Bash(dotnet:*)", "Bash(nuget:*)", "Bash(msbuild:*)"],
    "dotnet": ["Bash(dotnet:*)", "Bash(nuget:*)", "Bash(msbuild:*)"],
    "fsharp": ["Bash(dotnet:*)", "Bash(nuget:*)"],
    # Mobile
    "dart": ["Bash(dart:*)", "Bash(flutter:*)", "Bash(pub:*)"],
    "flutter": ["Bash(flutter:*)", "Bash(dart:*)", "Bash(pub:*)"],
    # JVM extras
    "scala": ["Bash(scala:*)", "Bash(scalac:*)", "Bash(sbt:*)", "Bash(gradle:*)"],
    "clojure": ["Bash(clj:*)", "Bash(clojure:*)", "Bash(lein:*)"],
    "groovy": ["Bash(groovy:*)", "Bash(gradle:*)"],
    # Data / ML
    "r": ["Bash(R:*)", "Bash(Rscript:*)", "Bash(r:*)"],
    # Scripts
    "bash": ["Bash(bash:*)", "Bash(sh:*)", "Bash(shellcheck:*)"],
    "shell": ["Bash(bash:*)", "Bash(sh:*)", "Bash(shellcheck:*)"],
    "lua": ["Bash(lua:*)", "Bash(luarocks:*)"],
    "perl": ["Bash(perl:*)", "Bash(cpan:*)"],
    "haskell": ["Bash(ghc:*)", "Bash(cabal:*)", "Bash(stack:*)", "Bash(hlint:*)"],
    "nim": ["Bash(nim:*)", "Bash(nimble:*)"],
    "zig": ["Bash(zig:*)"],
    "ocaml": ["Bash(ocaml:*)", "Bash(opam:*)", "Bash(dune:*)"],
}

# ─── Package managers (monorepo / alternatives) ───────────────────────────────
PACKAGE_MANAGER_PERMISSIONS = {
    "pnpm": ["Bash(pnpm:*)"],
    "yarn": ["Bash(yarn:*)"],
    "bun": ["Bash(bun:*)", "Bash(bunx:*)"],
    "deno": ["Bash(deno:*)"],
    "uv": ["Bash(uv:*)"],
    "poetry": ["Bash(poetry:*)"],
    "conda": ["Bash(conda:*)", "Bash(mamba:*)"],
    "nix": ["Bash(nix:*)", "Bash(nix-shell:*)", "Bash(nix-env:*)"],
}

# ─── Monorepo tools ────────────────────────────────────────────────────────────
MONOREPO_PERMISSIONS = {
    "turborepo": ["Bash(turbo:*)"],
    "nx": ["Bash(nx:*)", "Bash(npx:*)"],
    "lerna": ["Bash(lerna:*)", "Bash(npx:*)"],
    "bazel": ["Bash(bazel:*)", "Bash(buildozer:*)"],
    "buck": ["Bash(buck:*)"],
    "pants": ["Bash(pants:*)"],
}

# ─── Data / ML / AI tools ──────────────────────────────────────────────────────
DATA_PERMISSIONS = {
    # Data engineering
    "jupyter": ["Bash(jupyter:*)", "Bash(ipython:*)"],
    "dbt": ["Bash(dbt:*)"],
    "airflow": ["Bash(airflow:*)"],
    "prefect": ["Bash(prefect:*)"],
    "dagster": ["Bash(dagster:*)", "Bash(dagit:*)"],
    "spark": ["Bash(spark-submit:*)", "Bash(pyspark:*)"],
    "ray": ["Bash(ray:*)"],
    "kafka": ["Bash(kafka-topics:*)", "Bash(kafka-console-producer:*)", "Bash(kafka-console-consumer:*)"],
    # ML / MLOps
    "mlflow": ["Bash(mlflow:*)"],
    "wandb": ["Bash(wandb:*)"],
    "dvc": ["Bash(dvc:*)"],
    "bentoml": ["Bash(bentoml:*)"],
    "seldon": [],
    "triton": [],
    # LLM / Vector
    "ollama": ["Bash(ollama:*)"],
    "vllm": [],
    "llamacpp": ["Bash(llama-cpp-python:*)"],
}

# ─── Serverless / edge ────────────────────────────────────────────────────────
SERVERLESS_PERMISSIONS = {
    "serverless": ["Bash(serverless:*)", "Bash(sls:*)"],
    "sam": ["Bash(sam:*)"],
    "cdk": ["Bash(cdk:*)"],
    "firebase": ["Bash(firebase:*)"],
    "wrangler": ["Bash(wrangler:*)"],
    "netlify": ["Bash(netlify:*)"],
}

# ─── Desktop / Electron / Tauri ───────────────────────────────────────────────
DESKTOP_PERMISSIONS = {
    "electron": ["Bash(electron:*)", "Bash(electron-builder:*)"],
    "tauri": ["Bash(tauri:*)"],
}

INFRA_PERMISSIONS = {
    "docker": ["Bash(docker:*)", "Bash(docker-compose:*)", "Bash(docker compose:*)", "Bash(podman:*)"],
    "kubernetes": ["Bash(kubectl:*)", "Bash(helm:*)", "Bash(k9s:*)", "Bash(kustomize:*)", "Bash(k3s:*)"],
    "terraform": ["Bash(terraform:*)", "Bash(terragrunt:*)", "Bash(tofu:*)"],
    "opentofu": ["Bash(tofu:*)"],
    "pulumi": ["Bash(pulumi:*)"],
    "ansible": ["Bash(ansible:*)", "Bash(ansible-playbook:*)", "Bash(ansible-lint:*)"],
    "vercel": ["Bash(vercel:*)"],
    "railway": [],
    "heroku": ["Bash(heroku:*)"],
    "aws": ["Bash(aws:*)", "Bash(cdk:*)", "Bash(sam:*)"],
    "gcloud": ["Bash(gcloud:*)", "Bash(gsutil:*)"],
    "azure": ["Bash(az:*)"],
    "fly": ["Bash(flyctl:*)", "Bash(fly:*)"],
    "ssh": ["Bash(ssh:*)", "Bash(scp:*)", "Bash(rsync:*)"],
    "vagrant": ["Bash(vagrant:*)"],
}

DB_PERMISSIONS = {
    "postgresql": ["Bash(psql:*)", "Bash(pg_dump:*)", "Bash(pg_restore:*)"],
    "mysql": ["Bash(mysql:*)", "Bash(mysqldump:*)"],
    "mariadb": ["Bash(mysql:*)", "Bash(mysqldump:*)"],
    "redis": ["Bash(redis-cli:*)"],
    "mongodb": ["Bash(mongosh:*)", "Bash(mongodump:*)", "Bash(mongorestore:*)"],
    "sqlite": ["Bash(sqlite3:*)"],
    "cassandra": ["Bash(cqlsh:*)", "Bash(nodetool:*)"],
    "elasticsearch": ["Bash(curl:*)"],
    "neo4j": ["Bash(cypher-shell:*)"],
    "clickhouse": ["Bash(clickhouse-client:*)"],
    "supabase": ["Bash(supabase:*)"],
    "planetscale": ["Bash(pscale:*)"],
    "neon": [],
}

# ─── MCP server templates ─────────────────────────────────────────────────────
MCP_TEMPLATES = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        "_comment": "File system access — '.' = project root (relatif au dossier où claude est lancé)"
    },
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"},
        "_comment": "Set GITHUB_TOKEN in your environment"
    },
    "postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"],
        "_comment": "Set DATABASE_URL in your environment"
    },
    "sqlite": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "./db.sqlite"],
        "_comment": "Update --db-path to your SQLite file"
    },
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
        "_comment": "Set BRAVE_API_KEY in your environment"
    },
    "slack": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {
            "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
            "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
        }
    },
    "linear": {
        "command": "npx",
        "args": ["-y", "@linear/mcp-server"],
        "env": {"LINEAR_API_KEY": "${LINEAR_API_KEY}"}
    },
    "notion": {
        "command": "npx",
        "args": ["-y", "@notionhq/mcp"],
        "env": {"NOTION_API_KEY": "${NOTION_API_KEY}"}
    },
    "playwright": {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest", "--headless"]
    },
    "desktop-commander": {
        "command": "npx",
        "args": ["-y", "@wonderwhy-er/desktop-commander"]
    },
}

MCP_PERMISSIONS = {
    "filesystem": ["mcp__filesystem__read_file", "mcp__filesystem__read_multiple_files", "mcp__filesystem__list_directory", "mcp__filesystem__write_file"],
    "github": ["mcp__github__get_file_contents", "mcp__github__search_code", "mcp__github__list_issues", "mcp__github__create_issue"],
    "postgres": ["mcp__postgres__query"],
    "sqlite": ["mcp__sqlite__query", "mcp__sqlite__read_query"],
    "playwright": [
        "mcp__playwright__browser_navigate", "mcp__playwright__browser_click",
        "mcp__playwright__browser_fill_form", "mcp__playwright__browser_snapshot",
        "mcp__playwright__browser_screenshot", "mcp__playwright__browser_evaluate",
    ],
    "desktop-commander": [
        "mcp__desktop_commander__read_file", "mcp__desktop_commander__list_directory",
        "mcp__desktop_commander__execute_command",
    ],
}


# ─── Hook content generators ──────────────────────────────────────────────────

def make_session_start(manifest: dict) -> str:
    name = manifest.get("project", {}).get("name", "Projet")
    learning_file = manifest.get("context", {}).get("learning_file", "learning.md")

    # Seules les 2 variables dynamiques utilisent un f-string
    dynamic = f'PROJECT_NAME="{name}"\nLEARNING_FILE="{learning_file}"\n'

    # Tout le reste est un raw string — pas de conflit avec les {} bash/python
    static = r'''
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

  python3 - "$LEGACY_NOTE" "$STACK_SECTION" <<'PYEOF'
import json, sys
legacy = sys.argv[1]
stack = sys.argv[2]
lines = ["=== SETUP REQUIS ==="]
if legacy:
    lines += ["", legacy]
lines += ["", "Stack detecte :", stack, ""]
lines += ["Instructions :"]
lines += ["1. Si legacy : explore d'abord (Glob/Grep) pour valider le stack"]
lines += ["2. Lance le SETUP INTERVIEW (CLAUDE.md) - questions une par une"]
lines += ["3. Pre-remplis depuis la detection ci-dessus, confirme avec l'utilisateur"]
lines += ["4. Ecris project.manifest.json"]
lines += ["5. Lance python3 scripts/gen.py"]
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

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
ctx = f"=== {name} - SESSION START ===\n\nBranch: {branch}\nGit status:\n{status}\n\nCommits recents:\n{log}\n\nManifest:\n{manifest}\n\nRegles custom:\n{rules}\n\n{lfile} (dernieres 60 lignes):\n{learning}"
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
'''

    preamble = '''#!/bin/bash
# Hook: SessionStart — Auto-portable, gere setup + injection de contexte
# Se localise via BASH_SOURCE — fonctionne depuis n'importe quel projet

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
'''
    return preamble + dynamic + static


def make_pre_bash_guard(manifest: dict) -> str:
    return '''#!/bin/bash
# Hook: PreToolUse(Bash) — Bloque les commandes dangereuses
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Commandes destructives interdites sans confirmation explicite
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf $HOME"
  "DROP DATABASE"
  "DROP TABLE"
  "TRUNCATE"
  "git push --force origin main"
  "git push --force origin master"
  "git reset --hard HEAD~"
  "> /etc/"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qF "$pattern"; then
    python3 -c "
import json
print(json.dumps({
    'decision': 'block',
    'reason': f'Commande potentiellement destructive détectée : {repr(\"$pattern\")}. Confirme explicitement si tu veux vraiment exécuter ça.'
}))
"
    exit 0
  fi
done

# Laisser passer
exit 0
'''


def make_post_edit(manifest: dict) -> str:
    stack = manifest.get("stack", {})
    guards = manifest.get("guards", {})
    languages = [l.lower() for l in stack.get("languages", [])]
    frameworks = [f.lower() for f in stack.get("frameworks", [])]
    linters = [l.lower() for l in stack.get("linting", [])]

    has_python = "python" in languages
    has_ts = "typescript" in languages or any("react" in f or "next" in f or "expo" in f for f in frameworks)
    has_go = "go" in languages
    has_rust = "rust" in languages
    has_ruby = "ruby" in languages

    lint = guards.get("lint", False)
    type_check = guards.get("type_check", False)
    migration_check = guards.get("migration_check", False)
    i18n_check = guards.get("i18n_check", False)
    test_on_edit = guards.get("test_on_edit", False)

    lines = [
        "#!/bin/bash",
        "# Hook: PostToolUse(Edit|Write) — Guards qualité",
        "# Auto-portable via BASH_SOURCE",
        "",
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
        'PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"',
        "",
        "INPUT=$(cat)",
        'FILE=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get(\'tool_input\',{}).get(\'file_path\',\'\'))" 2>/dev/null || echo "")',
        "",
        "ERRORS=''",
        "WARNINGS=''",
        "",
    ]

    if lint and has_python:
        lines += [
            "# ── Python: ruff lint ──────────────────────────────────",
            'if echo "$FILE" | grep -q "\\.py$"; then',
            "  if command -v ruff &>/dev/null; then",
            '    RUFF_OUT=$(ruff check "$FILE" 2>&1)',
            '    if [ -n "$RUFF_OUT" ]; then',
            '      ERRORS="$ERRORS\\n[ruff] $RUFF_OUT"',
            "    fi",
            "  fi",
            "fi",
            "",
        ]

    if lint and has_ts:
        lines += [
            "# ── TypeScript: eslint ──────────────────────────────────",
            'if echo "$FILE" | grep -qE "\\.(ts|tsx|js|jsx)$"; then',
            "  FRONTEND_DIR=$(find \"$PROJECT_ROOT\" -name 'package.json' -not -path '*/node_modules/*' -maxdepth 3 | head -1 | xargs dirname 2>/dev/null || echo '')",
            '  if [ -n "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/node_modules/.bin/eslint" ]; then',
            '    ESLINT_OUT=$(cd "$FRONTEND_DIR" && node_modules/.bin/eslint "$FILE" --max-warnings=0 2>&1 | tail -20)',
            '    if [ -n "$ESLINT_OUT" ]; then',
            '      WARNINGS="$WARNINGS\\n[eslint] $ESLINT_OUT"',
            "    fi",
            "  fi",
            "fi",
            "",
        ]

    if type_check and has_ts:
        lines += [
            "# ── TypeScript: tsc type-check ─────────────────────────",
            'if echo "$FILE" | grep -qE "\\.(ts|tsx)$"; then',
            "  FRONTEND_DIR=$(find \"$PROJECT_ROOT\" -name 'tsconfig.json' -not -path '*/node_modules/*' -maxdepth 3 | head -1 | xargs dirname 2>/dev/null || echo '')",
            '  if [ -n "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/node_modules/.bin/tsc" ]; then',
            '    TSC_OUT=$(cd "$FRONTEND_DIR" && node_modules/.bin/tsc --noEmit 2>&1 | grep "error TS" | head -10)',
            '    if [ -n "$TSC_OUT" ]; then',
            '      ERRORS="$ERRORS\\n[tsc] $TSC_OUT"',
            "    fi",
            "  fi",
            "fi",
            "",
        ]

    if migration_check and has_python:
        has_django = any("django" in f for f in frameworks)
        if has_django:
            lines += [
                "# ── Django: check missing migrations ───────────────────",
                'if echo "$FILE" | grep -q "models\\.py$"; then',
                "  if command -v docker &>/dev/null; then",
                "    docker compose -f \"$PROJECT_ROOT/docker-compose.yml\" exec -T backend python manage.py makemigrations --check --dry-run 2>/dev/null",
                "    if [ $? -ne 0 ]; then",
                '      WARNINGS="$WARNINGS\\n[migrations] Migrations manquantes — pense a makemigrations apres avoir edite models.py"',
                "    fi",
                "  fi",
                "fi",
                "",
            ]

    if i18n_check:
        lines += [
            "# ── i18n: check fr/en parity ────────────────────────────",
            'if echo "$FILE" | grep -q "locales"; then',
            "  FR_KEYS=$(find \"$PROJECT_ROOT\" -name '*_fr.json' -not -path '*/node_modules/*' 2>/dev/null | xargs cat 2>/dev/null | python3 -c \"import json,sys; [print(k) for d in [json.loads(l) for l in sys.stdin if l.strip()] for k in d.keys()]\" 2>/dev/null | sort | uniq)",
            "  EN_KEYS=$(find \"$PROJECT_ROOT\" -name '*_en.json' -not -path '*/node_modules/*' 2>/dev/null | xargs cat 2>/dev/null | python3 -c \"import json,sys; [print(k) for d in [json.loads(l) for l in sys.stdin if l.strip()] for k in d.keys()]\" 2>/dev/null | sort | uniq)",
            '  DIFF=$(diff <(echo "$FR_KEYS") <(echo "$EN_KEYS") | head -10)',
            '  if [ -n "$DIFF" ]; then',
            '    WARNINGS="$WARNINGS\\n[i18n] Clés fr/en désynchronisées : $DIFF"',
            "  fi",
            "fi",
            "",
        ]

    if test_on_edit and has_python:
        lines += [
            "# ── Tests automatiques (python) ─────────────────────────",
            'if echo "$FILE" | grep -q "\\.py$" && ! echo "$FILE" | grep -q "test_"; then',
            "  TEST_FILE=$(echo \"$FILE\" | sed 's|/\\([^/]*\\)\\.py$|/test_\\1.py|')",
            '  if [ -f "$TEST_FILE" ]; then',
            "    if command -v pytest &>/dev/null; then",
            '      PYTEST_OUT=$(pytest "$TEST_FILE" -q 2>&1 | tail -5)',
            '      if echo "$PYTEST_OUT" | grep -q "FAILED"; then',
            '        ERRORS="$ERRORS\\n[pytest] $PYTEST_OUT"',
            "      fi",
            "    fi",
            "  fi",
            "fi",
            "",
        ]

    lines += [
        "# ── Output ───────────────────────────────────────────────────",
        'if [ -n "$ERRORS" ]; then',
        "  python3 -c \"",
        "import json, sys",
        "msg = sys.argv[1]",
        "print(json.dumps({",
        "    'decision': 'block',",
        "    'reason': f'Guards qualité ont détecté des erreurs :\\n{msg}'",
        "}))",
        "\" \"$ERRORS\"",
        "  exit 0",
        "fi",
        "",
        'if [ -n "$WARNINGS" ]; then',
        "  python3 -c \"",
        "import json, sys",
        "msg = sys.argv[1]",
        "print(json.dumps({",
        "    'hookSpecificOutput': {",
        "        'hookEventName': 'PostToolUse',",
        "        'additionalContext': f'⚠️  Avertissements qualité :\\n{msg}'",
        "    }",
        "}))",
        "\" \"$WARNINGS\"",
        "fi",
        "",
        "exit 0",
    ]

    return "\n".join(lines) + "\n"


def make_user_prompt_submit(manifest: dict) -> str:
    """Hook UserPromptSubmit — intent classification + injection detection."""
    return r'''#!/bin/bash
# Hook: UserPromptSubmit — Intent classification + prompt injection detection
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('prompt',''))" 2>/dev/null || echo "")

python3 - "$PROMPT" <<'PYEOF'
import sys, json, re

prompt = sys.argv[1].lower() if len(sys.argv) > 1 else ""

# ── Injection detection ──────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions",
    r"disregard (previous|all|your) (instructions|rules)",
    r"you are now (a |an )?(?!claude)",
    r"new (system |)prompt",
    r"forget (everything|all) (you|your)",
    r"override (your |)instructions",
    r"jailbreak",
    r"<\|im_start\|>|<\|endoftext\|>|\[INST\]|\[\/INST\]",
]

for pattern in INJECTION_PATTERNS:
    if re.search(pattern, prompt, re.IGNORECASE):
        print(json.dumps({
            "decision": "block",
            "reason": f"Possible prompt injection detected (pattern: '{pattern}'). If this is a legitimate request, rephrase it."
        }))
        sys.exit(0)

# ── Intent classification ────────────────────────────────────────────────────
INTENT_RULES = [
    ("hotfix",           ["hotfix", "urgence prod", "correctif immédiat", "ça crashe en prod", "emergency", "production down", "service down"]),
    ("incident",         ["incident prod", "incident en prod", "alerte critique", "service dégradé", "sla breach", "p1 incident", "p2 incident", "production incident", "service unavailable", "outage"]),
    ("db-migration",     ["migration db", "migration base", "ajoute une migration", "modifie le schéma", "alter table", "nouvelle colonne", "supprime une colonne", "add column", "drop column", "migrate schema", "schema migration"]),
    ("perf-test",        ["test de charge", "load test", "benchmark", "tient la charge", "mesure les performances", "locust", "k6", "performance test", "stress test", "perf baseline"]),
    ("publish",          ["publie le package", "publie sur pypi", "publie sur npm", "npm publish", "publish to pypi", "release library", "publie la librairie", "crates.io", "rubygems", "publish package"]),
    ("api-design",       ["design l'api", "design api", "nouvel endpoint", "api first", "contrat api", "définis le schéma", "ajoute un endpoint", "openapi", "graphql schema", "grpc proto", "api contract"]),
    ("release",          ["release", "prépare une version", "prépare la version", "tag v", "déploie une release"]),
    ("bugfix",           ["bug", "crash", "erreur", "error", "fixe", "corrige", "ça marche pas", "broken", "regression", "régression"]),
    ("security-audit",   ["audit", "sécurité", "security", "vulnérabilité", "scan", "cve", "faille"]),
    ("update-deps",      ["mets à jour les dépendances", "update deps", "update dependencies", "upgrade packages", "outdated packages"]),
    ("refactor",         ["refactor", "nettoie", "restructure", "améliore la structure", "clean up", "dette technique"]),
    ("improve-template", ["améliore le template", "self-improve", "mets-toi à jour", "update template", "template improve"]),
    ("onboard",          ["setup", "initialise", "configure le projet", "onboard", "nouveau projet", "legacy"]),
    ("feature",          ["implémente", "ajoute", "crée une feature", "nouvelle feature", "add feature", "implement"]),
    ("question",         ["comment", "comment fonctionne", "explique", "qu'est-ce que", "pourquoi", "what is", "how does", "explain"]),
]

intent = "other"
for intent_name, keywords in INTENT_RULES:
    if any(kw in prompt for kw in keywords):
        intent = intent_name
        break

# Inject intent as context (not blocking)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"[INTENT:{intent}] — Voir CLAUDE.md routing table pour le workflow correspondant."
    }
}))
PYEOF

exit 0
'''


def make_stop(manifest: dict) -> str:
    learning_file = manifest.get("context", {}).get("learning_file", "learning.md")
    name = manifest.get("project", {}).get("name", "ce projet")
    return f'''#!/bin/bash
# Hook: Stop — Rappel de mise à jour + logging d'observations
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LEARNING_FILE="{learning_file}"
PROJECT_NAME="{name}"

# Vérifie si des fichiers ont été modifiés cette session
CHANGED=$(cd "$PROJECT_ROOT" && git status --short 2>/dev/null | wc -l | tr -d ' ')

# Logger une observation de session pour le self-improve engine
if command -v python3 &>/dev/null && [ -f "$PROJECT_ROOT/scripts/self-improve.py" ]; then
  python3 "$PROJECT_ROOT/scripts/self-improve.py" --log \
    '{{"type": "user_validation", "detail": "session completed, {name}"}}' \
    2>/dev/null &
fi

if [ "$CHANGED" -gt "0" ]; then
  python3 -c "
import json
print(json.dumps({{
    'hookSpecificOutput': {{
        'hookEventName': 'Stop',
        'additionalContext': '💾 Session terminée avec $CHANGED fichier(s) modifié(s). Si tu as découvert des patterns importants, des bugs ou des décisions d\\'architecture, mets à jour \\`{learning_file}\\` pour $PROJECT_NAME.'
    }}
}}))
"
fi

exit 0
'''


# ─── Settings generator ───────────────────────────────────────────────────────

def _add_perms(perms: list, source_dict: dict, key: str):
    """Add permissions from a dict by key, avoiding duplicates."""
    for p in source_dict.get(key, []):
        if p not in perms:
            perms.append(p)


def build_permissions(manifest: dict) -> list:
    perms = list(BASE_PERMISSIONS)

    stack = manifest.get("stack", {})
    languages = [l.lower() for l in stack.get("languages", [])]
    frameworks = [f.lower() for f in stack.get("frameworks", [])]
    databases = [d.lower() for d in stack.get("databases", [])]
    infra = [i.lower() for i in stack.get("runtime", [])]
    pkg_managers = [p.lower() for p in stack.get("package_managers", [])]
    monorepo_tools = [m.lower() for m in stack.get("monorepo_tools", [])]
    data_tools = [d.lower() for d in stack.get("data_tools", [])]
    serverless = [s.lower() for s in stack.get("serverless", [])]
    desktop_frameworks = [d.lower() for d in stack.get("desktop_frameworks", [])]

    # Languages
    for lang in languages:
        _add_perms(perms, STACK_PERMISSIONS, lang)

    # Frameworks → imply languages
    FRAMEWORK_LANG_MAP = {
        ("react", "next", "expo", "vue", "angular", "svelte", "nuxt", "remix", "astro",
         "electron", "ionic", "qwik", "solid", "vite", "stencil"): "typescript",
        ("django", "flask", "fastapi", "celery", "tornado", "starlette", "litestar",
         "airflow", "prefect", "kedro", "pytorch", "tensorflow", "sklearn",
         "scikit-learn", "langchain", "llama-index", "huggingface"): "python",
        ("rails", "sinatra", "hanami"): "ruby",
        ("laravel", "symfony", "slim"): "php",
        ("spring", "quarkus", "micronaut", "ktor"): "java",
        ("dotnet", "aspnet", "blazor", "wpf", "maui"): "dotnet",
        ("flutter",): "dart",
        ("tauri",): "rust",
    }
    for fw in frameworks:
        for fw_keys, lang_key in FRAMEWORK_LANG_MAP.items():
            if any(x in fw for x in fw_keys):
                _add_perms(perms, STACK_PERMISSIONS, lang_key)

    # Databases
    for db in databases:
        for key, plist in DB_PERMISSIONS.items():
            if key in db:
                for p in plist:
                    if p not in perms:
                        perms.append(p)

    # Infra / runtime
    for inf in infra:
        for key, plist in INFRA_PERMISSIONS.items():
            if key in inf:
                for p in plist:
                    if p not in perms:
                        perms.append(p)

    # Package managers
    for pm in pkg_managers:
        _add_perms(perms, PACKAGE_MANAGER_PERMISSIONS, pm)

    # Monorepo tools
    for mt in monorepo_tools:
        _add_perms(perms, MONOREPO_PERMISSIONS, mt)

    # Data / ML tools
    for dt in data_tools:
        _add_perms(perms, DATA_PERMISSIONS, dt)

    # Serverless
    for sl in serverless:
        _add_perms(perms, SERVERLESS_PERMISSIONS, sl)

    # Desktop
    for df in desktop_frameworks:
        _add_perms(perms, DESKTOP_PERMISSIONS, df)

    # MCP permissions
    for server in manifest.get("mcp_servers", []):
        for p in MCP_PERMISSIONS.get(server, []):
            if p not in perms:
                perms.append(p)

    # Extra permissions from manifest
    for extra in manifest.get("permissions", {}).get("extra_bash", []):
        perms.append(f"Bash({extra}:*)")

    for domain in manifest.get("permissions", {}).get("web_domains", []):
        perms.append(f"WebFetch(domain:{domain})")

    return perms


def build_hooks(manifest: dict) -> dict:
    # Chemins relatifs — Claude Code exécute les hooks depuis la racine du projet
    # Les scripts se localisent eux-mêmes via BASH_SOURCE
    name = manifest.get('project', {}).get('name', 'projet')
    hooks = {}

    # UserPromptSubmit — intent classification + injection detection (toujours)
    hooks["UserPromptSubmit"] = [{
        "hooks": [{
            "type": "command",
            "command": "bash .claude/hooks/user-prompt-submit.sh",
            "timeout": 10
        }]
    }]

    # SessionStart (toujours)
    hooks["SessionStart"] = [{
        "hooks": [{
            "type": "command",
            "command": "bash .claude/hooks/session-start.sh",
            "timeout": 15,
            "statusMessage": f"Chargement du contexte {name}..."
        }]
    }]

    # PreToolUse — bash guard (toujours)
    hooks["PreToolUse"] = [{
        "matcher": "Bash",
        "hooks": [{
            "type": "command",
            "command": "bash .claude/hooks/pre-bash-guard.sh",
            "timeout": 10
        }]
    }]

    # PostToolUse — quality guards (si au moins un guard actif)
    guards = manifest.get("guards", {})
    if any(guards.values()):
        hooks["PostToolUse"] = [{
            "matcher": "Edit|Write",
            "hooks": [{
                "type": "command",
                "command": "bash .claude/hooks/post-edit.sh",
                "timeout": 30,
                "statusMessage": "Guards qualité en cours..."
            }]
        }]

    # Stop (toujours)
    hooks["Stop"] = [{
        "hooks": [{
            "type": "command",
            "command": "bash .claude/hooks/stop.sh",
            "timeout": 10,
            "async": True
        }]
    }]

    # PostCompact — reload context
    hooks["PostCompact"] = [{
        "hooks": [{
            "type": "command",
            "command": "bash .claude/hooks/session-start.sh",
            "timeout": 15,
            "statusMessage": "Rechargement du contexte après compaction..."
        }]
    }]

    return hooks


def build_mcp_servers(manifest: dict) -> dict:
    servers = {}
    for server_name in manifest.get("mcp_servers", []):
        if server_name in MCP_TEMPLATES:
            # Copie sans les champs _comment (non standard dans .mcp.json)
            config = {k: v for k, v in MCP_TEMPLATES[server_name].items() if not k.startswith("_")}
            servers[server_name] = config
    return servers


def build_settings(manifest: dict) -> dict:
    settings = {
        "permissions": {
            "allow": build_permissions(manifest)
        },
        "hooks": build_hooks(manifest)
    }

    # Enabled MCP JSON servers
    mcp_servers = manifest.get("mcp_servers", [])
    if mcp_servers:
        settings["enabledMcpjsonServers"] = mcp_servers

    return settings


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("🔧 gen.py — Génération de la config Claude Code")
    print(f"   Root: {ROOT}")

    # Load manifest
    if not MANIFEST_PATH.exists() or MANIFEST_PATH.read_text().strip() in ("{}", ""):
        print("⚠️  project.manifest.json est vide. Lance le setup dans Claude Code d'abord.")
        print("   Dans Claude Code, tape : /setup ou demande à Claude de faire le setup.")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    project_name = manifest.get("project", {}).get("name", "Projet")
    print(f"   Projet: {project_name}")

    # Generate settings.local.json
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    settings = build_settings(manifest)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    print(f"✅ .claude/settings.local.json — {len(settings['permissions']['allow'])} permissions")

    # Generate hooks
    hooks_generated = []

    session_start = make_session_start(manifest)
    (HOOKS_DIR / "session-start.sh").write_text(session_start)
    (HOOKS_DIR / "session-start.sh").chmod(0o755)
    hooks_generated.append("session-start.sh")

    user_prompt = make_user_prompt_submit(manifest)
    (HOOKS_DIR / "user-prompt-submit.sh").write_text(user_prompt)
    (HOOKS_DIR / "user-prompt-submit.sh").chmod(0o755)
    hooks_generated.append("user-prompt-submit.sh")

    pre_bash = make_pre_bash_guard(manifest)
    (HOOKS_DIR / "pre-bash-guard.sh").write_text(pre_bash)
    (HOOKS_DIR / "pre-bash-guard.sh").chmod(0o755)
    hooks_generated.append("pre-bash-guard.sh")

    guards = manifest.get("guards", {})
    if any(guards.values()):
        post_edit = make_post_edit(manifest)
        (HOOKS_DIR / "post-edit.sh").write_text(post_edit)
        (HOOKS_DIR / "post-edit.sh").chmod(0o755)
        hooks_generated.append(f"post-edit.sh ({[k for k,v in guards.items() if v]})")

    stop = make_stop(manifest)
    (HOOKS_DIR / "stop.sh").write_text(stop)
    (HOOKS_DIR / "stop.sh").chmod(0o755)
    hooks_generated.append("stop.sh")

    print(f"✅ Hooks générés : {', '.join(hooks_generated)}")

    # Generate .mcp.json
    mcp_servers = build_mcp_servers(manifest)
    if mcp_servers:
        mcp_config = {"mcpServers": mcp_servers}
        with open(MCP_PATH, "w") as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)
        print(f"✅ .mcp.json — {len(mcp_servers)} serveur(s) MCP : {list(mcp_servers.keys())}")
    else:
        if MCP_PATH.exists():
            MCP_PATH.unlink()
        print("ℹ️  Pas de MCP servers configurés")

    # Summary
    stack = manifest.get("stack", {})
    agents = manifest.get("agents", {})
    active_agents = [k for k, v in agents.items() if v]

    print()
    print("═══════════════════════════════════════════")
    print(f"  {project_name} — config générée avec succès")
    print("═══════════════════════════════════════════")
    print(f"  Stack    : {', '.join(stack.get('languages', []) + stack.get('frameworks', []))}")
    print(f"  Guards   : {', '.join([k for k,v in guards.items() if v]) or 'aucun'}")
    print(f"  Agents   : {', '.join(active_agents) or 'aucun'}")
    print(f"  MCP      : {', '.join(mcp_servers.keys()) or 'aucun'}")
    print()
    print("  Redémarre Claude Code pour appliquer les changements.")
    print()


if __name__ == "__main__":
    main()
