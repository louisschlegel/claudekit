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

import argparse
import difflib
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

# Hooks gérés par gen.py — tout autre .sh dans hooks/ est custom et non touché
GENERATED_HOOK_NAMES = {
    "session-start.sh", "user-prompt-submit.sh", "pre-bash-guard.sh",
    "post-edit.sh", "stop.sh", "pre-push.sh",
}


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
    "deno": ["Bash(deno:*)", "Bash(deno run:*)", "Bash(deno test:*)", "Bash(deno compile:*)", "Bash(deno fmt:*)", "Bash(deno lint:*)"],
    "uv": ["Bash(uv:*)"],
    "poetry": ["Bash(poetry:*)"],
    "conda": ["Bash(conda:*)", "Bash(mamba:*)"],
    "nix": ["Bash(nix:*)", "Bash(nix-shell:*)", "Bash(nix-env:*)"],
}

# ─── Monorepo tools ────────────────────────────────────────────────────────────
MONOREPO_PERMISSIONS = {
    "turborepo": ["Bash(turbo:*)"],
    "nx": ["Bash(nx:*)", "Bash(npx:*)", "Bash(nx affected:*)", "Bash(nx run-many:*)", "Bash(nx graph:*)"],
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
    "pulumi": ["Bash(pulumi:*)", "Bash(pulumi up:*)", "Bash(pulumi preview:*)", "Bash(pulumi destroy:*)", "Bash(pulumi stack:*)"],
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

# ─── Native Claude integrations (zero-config, permissions only) ──────────────
# Ces intégrations sont fournies directement par Claude.ai — pas besoin de serveur
# à installer. Il suffit de les lister dans manifest.claude_native_integrations[]
# pour que leurs permissions soient auto-approuvées dans settings.local.json.
CLAUDE_NATIVE_INTEGRATIONS = {
    "gmail": [
        "mcp__claude_ai_Gmail__gmail_create_draft",
        "mcp__claude_ai_Gmail__gmail_get_profile",
        "mcp__claude_ai_Gmail__gmail_list_drafts",
        "mcp__claude_ai_Gmail__gmail_list_labels",
        "mcp__claude_ai_Gmail__gmail_read_message",
        "mcp__claude_ai_Gmail__gmail_read_thread",
        "mcp__claude_ai_Gmail__gmail_search_messages",
    ],
    "google-calendar": [
        "mcp__claude_ai_Google_Calendar__gcal_create_event",
        "mcp__claude_ai_Google_Calendar__gcal_delete_event",
        "mcp__claude_ai_Google_Calendar__gcal_find_meeting_times",
        "mcp__claude_ai_Google_Calendar__gcal_find_my_free_time",
        "mcp__claude_ai_Google_Calendar__gcal_get_event",
        "mcp__claude_ai_Google_Calendar__gcal_list_calendars",
        "mcp__claude_ai_Google_Calendar__gcal_list_events",
        "mcp__claude_ai_Google_Calendar__gcal_respond_to_event",
        "mcp__claude_ai_Google_Calendar__gcal_update_event",
    ],
    "canva": [
        "mcp__claude_ai_Canva__cancel-editing-transaction",
        "mcp__claude_ai_Canva__comment-on-design",
        "mcp__claude_ai_Canva__commit-editing-transaction",
        "mcp__claude_ai_Canva__create-design-from-candidate",
        "mcp__claude_ai_Canva__create-folder",
        "mcp__claude_ai_Canva__export-design",
        "mcp__claude_ai_Canva__generate-design",
        "mcp__claude_ai_Canva__generate-design-structured",
        "mcp__claude_ai_Canva__get-assets",
        "mcp__claude_ai_Canva__get-design",
        "mcp__claude_ai_Canva__get-design-content",
        "mcp__claude_ai_Canva__get-design-pages",
        "mcp__claude_ai_Canva__get-design-thumbnail",
        "mcp__claude_ai_Canva__get-export-formats",
        "mcp__claude_ai_Canva__get-presenter-notes",
        "mcp__claude_ai_Canva__import-design-from-url",
        "mcp__claude_ai_Canva__list-brand-kits",
        "mcp__claude_ai_Canva__list-comments",
        "mcp__claude_ai_Canva__list-folder-items",
        "mcp__claude_ai_Canva__list-replies",
        "mcp__claude_ai_Canva__move-item-to-folder",
        "mcp__claude_ai_Canva__perform-editing-operations",
        "mcp__claude_ai_Canva__reply-to-comment",
        "mcp__claude_ai_Canva__request-outline-review",
        "mcp__claude_ai_Canva__resize-design",
        "mcp__claude_ai_Canva__resolve-shortlink",
        "mcp__claude_ai_Canva__search-designs",
        "mcp__claude_ai_Canva__search-folders",
        "mcp__claude_ai_Canva__start-editing-transaction",
        "mcp__claude_ai_Canva__upload-asset-from-url",
    ],
    "claude-in-chrome": [
        "mcp__claude-in-chrome__computer",
        "mcp__claude-in-chrome__find",
        "mcp__claude-in-chrome__form_input",
        "mcp__claude-in-chrome__get_page_text",
        "mcp__claude-in-chrome__gif_creator",
        "mcp__claude-in-chrome__javascript_tool",
        "mcp__claude-in-chrome__navigate",
        "mcp__claude-in-chrome__read_console_messages",
        "mcp__claude-in-chrome__read_network_requests",
        "mcp__claude-in-chrome__read_page",
        "mcp__claude-in-chrome__resize_window",
        "mcp__claude-in-chrome__shortcuts_execute",
        "mcp__claude-in-chrome__shortcuts_list",
        "mcp__claude-in-chrome__switch_browser",
        "mcp__claude-in-chrome__tabs_context_mcp",
        "mcp__claude-in-chrome__tabs_create_mcp",
        "mcp__claude-in-chrome__update_plan",
        "mcp__claude-in-chrome__upload_image",
    ],
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

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" "$COVERAGE" "$DEPS_ALERT" "$CI_STATUS" "$TECH_DEBT" "$OLD_BRANCHES" "$HOT_FILES" "$PENDING_MIGRATIONS" "$DOCS_LIST" "$DOCS_CONTENT" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
coverage, deps_alert, ci_status, tech_debt = sys.argv[9:13]
old_branches, hot_files, pending_migrations = sys.argv[13:16]
docs_list, docs_content = sys.argv[16:18]

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
    ("ab-test",          ["a/b test", "feature flag", "split test", "rollout progressif", "expérimentation", "statistical significance"]),
    ("data-quality",     ["qualité des données", "data quality", "great expectations", "données corrompues", "anomalie de données"]),
    ("llm-eval",         ["évalue le rag", "llm eval", "ragas", "qualité des réponses", "hallucination", "benchmark llm", "rag evaluation"]),
    ("spec-to-project",  ["cahier des charges", "cahier de charges", "analyse cette spec", "voici les specs", "voici mon brief", "prd", "product requirement", "génère le projet depuis", "setup depuis spec", "j'ai un document de spec", "analyse ce document"]),
    ("code-review",      ["review cette pr", "relis ce code", "code review", "analyse ces changements", "review le diff", "donne moi un review", "relecture", "pr review", "review this"]),
    ("monitoring-setup", ["setup monitoring", "configure observabilité", "ajoute prometheus", "grafana", "datadog", "configure les alertes", "métriques", "logs centralisés", "tracing", "observabilité"]),
    ("cost-optimization",["optimise les coûts", "réduis les coûts cloud", "trop cher aws", "facture cloud", "optimise les tokens", "rightsizing", "coûts llm", "burn rate trop élevé", "coût infrastructure"]),
    ("dependency-audit", ["audit les dépendances", "vérifie les cve", "scan les vulnérabilités", "dépendances vulnérables", "npm audit", "pip-audit", "security scan deps", "snyk", "licence check"]),
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

    # Native Claude integrations (gmail, google-calendar, canva, claude-in-chrome)
    # Pas de serveur à installer — juste des permissions à auto-approuver
    for integration in manifest.get("claude_native_integrations", []):
        for p in CLAUDE_NATIVE_INTEGRATIONS.get(integration, []):
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


# ─── Audit config Claude existante ───────────────────────────────────────────

def audit_existing_claude_config(generated_settings_json: str, generated_mcp_json: str | None) -> dict:
    """
    Compare la config Claude existante avec ce que gen.py s'apprête à générer.
    Retourne les éléments qui seraient perdus si on écrasait sans --preserve-custom.
    """
    result = {
        "has_existing": False,
        "custom_permissions": [],   # permissions dans l'existant, absentes du généré
        "custom_mcp_servers": {},   # serveurs MCP non reconnus par gen.py
        "custom_hooks": [],         # hooks .sh non gérés par gen.py (jamais écrasés)
    }

    # ── settings.local.json ────────────────────────────────────────────────────
    if SETTINGS_PATH.exists():
        try:
            existing = json.loads(SETTINGS_PATH.read_text())
            generated = json.loads(generated_settings_json)
            existing_perms = set(existing.get("permissions", {}).get("allow", []))
            generated_perms = set(generated.get("permissions", {}).get("allow", []))
            result["custom_permissions"] = sorted(existing_perms - generated_perms)
            if existing_perms:
                result["has_existing"] = True
        except (json.JSONDecodeError, KeyError):
            pass

    # ── .mcp.json ──────────────────────────────────────────────────────────────
    if MCP_PATH.exists():
        try:
            existing_mcp = json.loads(MCP_PATH.read_text()).get("mcpServers", {})
            # Serveurs présents dans l'existant mais absents de MCP_TEMPLATES → custom
            result["custom_mcp_servers"] = {
                k: v for k, v in existing_mcp.items() if k not in MCP_TEMPLATES
            }
            if existing_mcp:
                result["has_existing"] = True
        except json.JSONDecodeError:
            pass

    # ── hooks custom ───────────────────────────────────────────────────────────
    if HOOKS_DIR.exists():
        for f in sorted(HOOKS_DIR.glob("*.sh")):
            if f.name not in GENERATED_HOOK_NAMES:
                result["custom_hooks"].append(f.name)
        if list(HOOKS_DIR.glob("*.sh")):
            result["has_existing"] = True

    return result


def merge_custom_into_generated(generated: dict, audit: dict) -> dict:
    """
    Fusionne les éléments custom (permissions, MCP servers) dans les fichiers générés.
    Utilisé avec --preserve-custom.
    """
    merged = dict(generated)

    # Merge permissions
    if audit["custom_permissions"]:
        settings = json.loads(merged[".claude/settings.local.json"])
        existing_perms = settings["permissions"]["allow"]
        for p in audit["custom_permissions"]:
            if p not in existing_perms:
                existing_perms.append(p)
        merged[".claude/settings.local.json"] = json.dumps(settings, indent=2, ensure_ascii=False)

    # Merge MCP servers
    if audit["custom_mcp_servers"] and ".mcp.json" in merged:
        mcp_data = json.loads(merged[".mcp.json"])
        mcp_data["mcpServers"].update(audit["custom_mcp_servers"])
        merged[".mcp.json"] = json.dumps(mcp_data, indent=2, ensure_ascii=False)
    elif audit["custom_mcp_servers"]:
        # Pas de .mcp.json généré mais il y a des serveurs custom à préserver
        mcp_data = {"mcpServers": audit["custom_mcp_servers"]}
        merged[".mcp.json"] = json.dumps(mcp_data, indent=2, ensure_ascii=False)

    return merged


# ─── Main ─────────────────────────────────────────────────────────────────────

def _build_generated_files(manifest: dict) -> dict:
    """Return a dict of {relative_path: content_str} for all files gen.py would write."""
    files = {}

    settings = build_settings(manifest)
    files[".claude/settings.local.json"] = json.dumps(settings, indent=2, ensure_ascii=False)

    files[".claude/hooks/session-start.sh"] = make_session_start(manifest)
    files[".claude/hooks/user-prompt-submit.sh"] = make_user_prompt_submit(manifest)
    files[".claude/hooks/pre-bash-guard.sh"] = make_pre_bash_guard(manifest)

    guards = manifest.get("guards", {})
    if any(guards.values()):
        files[".claude/hooks/post-edit.sh"] = make_post_edit(manifest)

    files[".claude/hooks/stop.sh"] = make_stop(manifest)

    mcp_servers = build_mcp_servers(manifest)
    if mcp_servers:
        files[".mcp.json"] = json.dumps({"mcpServers": mcp_servers}, indent=2, ensure_ascii=False)

    return files


def main(dry_run: bool = False, show_diff: bool = False, preserve_custom: bool = False):
    print("gen.py — Generation de la config Claude Code")
    print(f"   Root: {ROOT}")

    # Load manifest
    if not MANIFEST_PATH.exists() or MANIFEST_PATH.read_text().strip() in ("{}", ""):
        print("project.manifest.json est vide. Lance le setup dans Claude Code d'abord.")
        print("   Dans Claude Code, tape : /setup ou demande a Claude de faire le setup.")
        sys.exit(1)

    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    project_name = manifest.get("project", {}).get("name", "Projet")
    print(f"   Projet: {project_name}")

    generated = _build_generated_files(manifest)

    # ── Audit config existante ─────────────────────────────────────────────────
    generated_mcp = generated.get(".mcp.json")
    audit = audit_existing_claude_config(generated[".claude/settings.local.json"], generated_mcp)

    if audit["has_existing"] and not dry_run and not show_diff:
        print()
        print("[audit] Config Claude existante détectée :")
        if audit["custom_permissions"]:
            print(f"  Permissions custom ({len(audit['custom_permissions'])}) absentes du manifest :")
            for p in audit["custom_permissions"]:
                print(f"    - {p}")
        if audit["custom_mcp_servers"]:
            print(f"  MCP servers non reconnus ({len(audit['custom_mcp_servers'])}) :")
            for k in audit["custom_mcp_servers"]:
                print(f"    - {k}")
        if audit["custom_hooks"]:
            print(f"  Hooks custom (conservés intacts) :")
            for h in audit["custom_hooks"]:
                print(f"    - {h}")
        if audit["custom_permissions"] or audit["custom_mcp_servers"]:
            if preserve_custom:
                print()
                print("  → --preserve-custom : fusion des éléments custom dans la config générée.")
                generated = merge_custom_into_generated(generated, audit)
            else:
                print()
                print("  → Ces éléments seront écrasés. Relance avec --preserve-custom pour les fusionner.")
                print("    Ou ajoute-les dans project.manifest.json (permissions.extra_bash / mcp_servers).")
        print()

    # ── --dry-run ─────────────────────────────────────────────────────────────
    if dry_run:
        print()
        print("[dry-run] Fichiers qui seraient generés :")
        for rel_path, content in generated.items():
            size = len(content.encode("utf-8"))
            print(f"  {rel_path}  ({size} bytes)")
        print()
        print(f"  Total : {len(generated)} fichier(s)")
        return

    # ── --diff ────────────────────────────────────────────────────────────────
    if show_diff:
        print()
        any_diff = False
        for rel_path, new_content in generated.items():
            abs_path = ROOT / rel_path
            if abs_path.exists():
                old_content = abs_path.read_text()
            else:
                old_content = ""
            if old_content == new_content:
                continue
            any_diff = True
            diff_lines = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            ))
            print(f"--- diff: {rel_path} ---")
            print("".join(diff_lines))
        if not any_diff:
            print("[diff] Aucun changement — les fichiers sont deja a jour.")
        return

    # ── Normal write ──────────────────────────────────────────────────────────
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)

    settings_content = generated[".claude/settings.local.json"]
    SETTINGS_PATH.write_text(settings_content)
    settings = json.loads(settings_content)
    print(f"[ok] .claude/settings.local.json — {len(settings['permissions']['allow'])} permissions")

    hooks_generated = []

    (HOOKS_DIR / "session-start.sh").write_text(generated[".claude/hooks/session-start.sh"])
    (HOOKS_DIR / "session-start.sh").chmod(0o755)
    hooks_generated.append("session-start.sh")

    (HOOKS_DIR / "user-prompt-submit.sh").write_text(generated[".claude/hooks/user-prompt-submit.sh"])
    (HOOKS_DIR / "user-prompt-submit.sh").chmod(0o755)
    hooks_generated.append("user-prompt-submit.sh")

    (HOOKS_DIR / "pre-bash-guard.sh").write_text(generated[".claude/hooks/pre-bash-guard.sh"])
    (HOOKS_DIR / "pre-bash-guard.sh").chmod(0o755)
    hooks_generated.append("pre-bash-guard.sh")

    guards = manifest.get("guards", {})
    if any(guards.values()):
        (HOOKS_DIR / "post-edit.sh").write_text(generated[".claude/hooks/post-edit.sh"])
        (HOOKS_DIR / "post-edit.sh").chmod(0o755)
        hooks_generated.append(f"post-edit.sh ({[k for k,v in guards.items() if v]})")

    (HOOKS_DIR / "stop.sh").write_text(generated[".claude/hooks/stop.sh"])
    (HOOKS_DIR / "stop.sh").chmod(0o755)
    hooks_generated.append("stop.sh")

    # Install pre-push git hook (symlink or copy)
    pre_push_src = HOOKS_DIR / "pre-push.sh"
    if pre_push_src.exists():
        git_hooks_dir = ROOT / ".git" / "hooks"
        if git_hooks_dir.exists():
            pre_push_dst = git_hooks_dir / "pre-push"
            if not pre_push_dst.exists():
                import os
                try:
                    os.symlink(pre_push_src.resolve(), pre_push_dst)
                    hooks_generated.append("pre-push (git hook installed)")
                except OSError:
                    import shutil
                    shutil.copy2(pre_push_src, pre_push_dst)
                    pre_push_dst.chmod(0o755)
                    hooks_generated.append("pre-push (git hook copied)")
            else:
                hooks_generated.append("pre-push (already installed)")

    print(f"[ok] Hooks generes : {', '.join(hooks_generated)}")

    # Generate .mcp.json
    mcp_servers = build_mcp_servers(manifest)
    if mcp_servers:
        MCP_PATH.write_text(generated[".mcp.json"])
        print(f"[ok] .mcp.json — {len(mcp_servers)} serveur(s) MCP : {list(mcp_servers.keys())}")
    else:
        if MCP_PATH.exists():
            MCP_PATH.unlink()
        print("    Pas de MCP servers configures")

    # Summary
    stack = manifest.get("stack", {})
    agents = manifest.get("agents", {})
    active_agents = [k for k, v in agents.items() if v]

    print()
    print("===========================================")
    print(f"  {project_name} — config generee avec succes")
    print("===========================================")
    print(f"  Stack    : {', '.join(stack.get('languages', []) + stack.get('frameworks', []))}")
    print(f"  Guards   : {', '.join([k for k,v in guards.items() if v]) or 'aucun'}")
    print(f"  Agents   : {', '.join(active_agents) or 'aucun'}")
    print(f"  MCP      : {', '.join(mcp_servers.keys()) or 'aucun'}")
    native = manifest.get("claude_native_integrations", [])
    print(f"  Native   : {', '.join(native) or 'aucun'}")
    print()
    print("  Redemarre Claude Code pour appliquer les changements.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="gen.py — Generateur de config Claude Code depuis project.manifest.json"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Afficher les fichiers qui seraient generés (nom + taille) sans rien ecrire.",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Afficher un diff unifie entre les fichiers actuels et ce qui serait genere.",
    )
    parser.add_argument(
        "--preserve-custom",
        action="store_true",
        help="Fusionner les permissions et MCP servers custom existants dans la config générée (au lieu d'écraser).",
    )
    args = parser.parse_args()

    if args.dry_run and args.diff:
        print("Erreur : --dry-run et --diff sont mutuellement exclusifs.")
        sys.exit(1)

    main(dry_run=args.dry_run, show_diff=args.diff, preserve_custom=args.preserve_custom)
