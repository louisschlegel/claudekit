#!/bin/bash
# Hook: SessionStart — Bootstrap portable
# Se localise via BASH_SOURCE — fonctionne depuis n'importe quel projet
# Gère 2 cas : manifest vide (setup) et manifest rempli (injection de contexte)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# ─── Cas 1 : manifest vide → guide le setup ──────────────────────────────────
MANIFEST_CONTENT=$(cat "$PROJECT_ROOT/project.manifest.json" 2>/dev/null | tr -d '[:space:]')

if [ "$MANIFEST_CONTENT" = "{}" ] || [ -z "$MANIFEST_CONTENT" ]; then

  DETECTED=""
  find_file() {
    find "$PROJECT_ROOT" -maxdepth 2 -name "$1" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/.dart_tool/*" 2>/dev/null | head -1
  }

  # ── Langages : markers de fichiers ─────────────────────────────────────────
  PKG_JSON=$(find_file "package.json")
  REQUIREMENTS=$(find_file "requirements.txt")
  PYPROJECT=$(find_file "pyproject.toml")
  GO_MOD=$(find_file "go.mod")
  CARGO=$(find_file "Cargo.toml")
  GEMFILE=$(find_file "Gemfile")
  PUBSPEC=$(find_file "pubspec.yaml")        # Dart/Flutter
  BUILD_GRADLE=$(find_file "build.gradle")   # Java/Kotlin/Android
  POM_XML=$(find_file "pom.xml")             # Maven/Java
  BUILD_SBT=$(find_file "build.sbt")         # Scala
  MIX_EXS=$(find_file "mix.exs")             # Elixir
  COMPOSER=$(find_file "composer.json")      # PHP
  CSPROJ=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.csproj" -not -path "*/.git/*" 2>/dev/null | head -1)  # .NET
  FSPROJ=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.fsproj" -not -path "*/.git/*" 2>/dev/null | head -1)  # F#
  CMAKELISTS=$(find_file "CMakeLists.txt")   # C/C++
  MAKEFILE=$(find_file "Makefile")           # C/C++/Generic
  PODFILE=$(find_file "Podfile")             # iOS CocoaPods
  PACKAGE_SWIFT=$(find_file "Package.swift") # Swift Package Manager
  CABAL=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.cabal" -not -path "*/.git/*" 2>/dev/null | head -1)   # Haskell
  RPROJ=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.Rproj" -not -path "*/.git/*" 2>/dev/null | head -1)   # R
  DEPS_EDN=$(find_file "deps.edn")           # Clojure
  PROJECT_CLJ=$(find_file "project.clj")     # Clojure/Lein
  BUILD_ZIG=$(find_file "build.zig")         # Zig
  DUNE=$(find_file "dune-project")           # OCaml

  # ── Monorepo detection ──────────────────────────────────────────────────────
  TURBO_JSON=$(find_file "turbo.json")
  NX_JSON=$(find_file "nx.json")
  LERNA_JSON=$(find_file "lerna.json")
  PNPM_WORKSPACE=$(find_file "pnpm-workspace.yaml")

  # ── Cloud / Infra ────────────────────────────────────────────────────────────
  SERVERLESS_YML=$(find_file "serverless.yml")
  SAM_YAML=$(find_file "template.yaml")
  FIREBASE_JSON=$(find_file "firebase.json")
  WRANGLER=$(find_file "wrangler.toml")
  NETLIFY=$(find_file "netlify.toml")
  TERRAFORM_TF=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.tf" -not -path "*/.git/*" 2>/dev/null | head -1)
  ANSIBLE_CFG=$(find_file "ansible.cfg")

  # ── Desktop / Electron / Tauri ───────────────────────────────────────────────
  ELECTRON_CFG=$(find_file "electron-builder.yml")
  TAURI_CFG=$(find "$PROJECT_ROOT" -maxdepth 3 -name "tauri.conf.json" -not -path "*/.git/*" 2>/dev/null | head -1)

  # ── Data / ML ────────────────────────────────────────────────────────────────
  DBT_PROJECT=$(find_file "dbt_project.yml")
  AIRFLOW_CFG=$(find_file "airflow.cfg")
  MLFLOW=$(find_file "MLproject")
  DVC_FILE=$(find_file ".dvc")
  JUPYTER=$(find "$PROJECT_ROOT" -maxdepth 2 -name "*.ipynb" -not -path "*/.git/*" 2>/dev/null | head -1)
  OLLAMA_FILE=$(find_file "Modelfile")
  DAGSTER_FILE=$(find_file "workspace.yaml")

  # ── CI/CD detection ──────────────────────────────────────────────────────────
  GITLAB_CI=$(find_file ".gitlab-ci.yml")
  CIRCLE_CI=$(find "$PROJECT_ROOT" -maxdepth 2 -path "*/.circleci/config.yml" 2>/dev/null | head -1)
  JENKINS=$(find_file "Jenkinsfile")
  AZURE_PIPELINES=$(find_file "azure-pipelines.yml")

  # ── Assemble DETECTED ────────────────────────────────────────────────────────
  [ -n "$PKG_JSON" ]      && DETECTED="$DETECTED\n- package.json -> Node/TypeScript ($(dirname "$PKG_JSON" | sed "s|$PROJECT_ROOT/||"))"
  [ -n "$REQUIREMENTS" ]  && DETECTED="$DETECTED\n- requirements.txt -> Python"
  [ -n "$PYPROJECT" ]     && DETECTED="$DETECTED\n- pyproject.toml -> Python (modern)"
  [ -n "$GO_MOD" ]        && DETECTED="$DETECTED\n- go.mod -> Go"
  [ -n "$CARGO" ]         && DETECTED="$DETECTED\n- Cargo.toml -> Rust"
  [ -n "$GEMFILE" ]       && DETECTED="$DETECTED\n- Gemfile -> Ruby"
  [ -n "$PUBSPEC" ]       && DETECTED="$DETECTED\n- pubspec.yaml -> Dart/Flutter"
  [ -n "$BUILD_GRADLE" ]  && DETECTED="$DETECTED\n- build.gradle -> Java/Kotlin/Android"
  [ -n "$POM_XML" ]       && DETECTED="$DETECTED\n- pom.xml -> Java/Maven"
  [ -n "$BUILD_SBT" ]     && DETECTED="$DETECTED\n- build.sbt -> Scala"
  [ -n "$MIX_EXS" ]       && DETECTED="$DETECTED\n- mix.exs -> Elixir"
  [ -n "$COMPOSER" ]      && DETECTED="$DETECTED\n- composer.json -> PHP"
  [ -n "$CSPROJ" ]        && DETECTED="$DETECTED\n- .csproj -> C#/.NET"
  [ -n "$FSPROJ" ]        && DETECTED="$DETECTED\n- .fsproj -> F#/.NET"
  [ -n "$CMAKELISTS" ]    && DETECTED="$DETECTED\n- CMakeLists.txt -> C/C++ (CMake)"
  [ -n "$PODFILE" ]       && DETECTED="$DETECTED\n- Podfile -> iOS (CocoaPods)"
  [ -n "$PACKAGE_SWIFT" ] && DETECTED="$DETECTED\n- Package.swift -> Swift (SPM)"
  [ -n "$CABAL" ]         && DETECTED="$DETECTED\n- .cabal -> Haskell"
  [ -n "$RPROJ" ]         && DETECTED="$DETECTED\n- .Rproj -> R"
  [ -n "$DEPS_EDN" ]      && DETECTED="$DETECTED\n- deps.edn -> Clojure"
  [ -n "$PROJECT_CLJ" ]   && DETECTED="$DETECTED\n- project.clj -> Clojure/Leiningen"
  [ -n "$BUILD_ZIG" ]     && DETECTED="$DETECTED\n- build.zig -> Zig"
  [ -n "$DUNE" ]          && DETECTED="$DETECTED\n- dune-project -> OCaml"

  # ── Framework detection from file contents ───────────────────────────────────
  if [ -n "$PKG_JSON" ]; then
    grep -q '"react-native"'  "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> React Native/Expo"
    grep -q '"next"'          "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Next.js"
    grep -q '"vue"'           "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Vue.js"
    grep -q '"nuxt"'          "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Nuxt"
    grep -q '"@sveltejs'      "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> SvelteKit/Svelte"
    grep -q '"svelte"'        "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Svelte"
    grep -q '"remix"'         "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Remix"
    grep -q '"astro"'         "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Astro"
    grep -q '"@angular'       "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Angular"
    grep -q '"electron"'      "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Electron (desktop)"
    grep -q '"vitest"'        "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Vitest (testing)"
    grep -q '"cypress"'       "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Cypress (E2E)"
    grep -q '"playwright"'    "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Playwright (E2E)"
    grep -q '"nestjs\|@nestjs' "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> NestJS"
    grep -q '"express"'       "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Express"
    grep -q '"fastify"'       "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Fastify"
    grep -q '"turbo"'         "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Turborepo (monorepo)"
    # Package manager
    grep -q '"packageManager"' "$PKG_JSON" 2>/dev/null && PM=$(python3 -c "import json; d=json.load(open('$PKG_JSON')); print(d.get('packageManager',''))" 2>/dev/null) && [ -n "$PM" ] && DETECTED="$DETECTED\n  -> Package manager: $PM"
    # Workspaces = monorepo
    grep -q '"workspaces"'    "$PKG_JSON" 2>/dev/null && DETECTED="$DETECTED\n  -> Monorepo (workspaces)"
  fi
  if [ -n "$REQUIREMENTS" ] || [ -n "$PYPROJECT" ]; then
    PYFILE="${REQUIREMENTS:-$PYPROJECT}"
    grep -qi "django"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Django"
    grep -qi "fastapi"        "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> FastAPI"
    grep -qi "flask"          "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Flask"
    grep -qi "celery"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Celery"
    grep -qi "sqlalchemy"     "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> SQLAlchemy"
    grep -qi "alembic"        "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Alembic (migrations)"
    grep -qi "pandas\|numpy\|scikit\|sklearn" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Data Science (pandas/numpy/sklearn)"
    grep -qi "torch\|pytorch"  "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> PyTorch (ML/DL)"
    grep -qi "tensorflow\|keras" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> TensorFlow/Keras (ML/DL)"
    grep -qi "jax\b"           "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> JAX (ML)"
    grep -qi "xgboost\|lightgbm\|catboost" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Gradient Boosting (XGBoost/LightGBM/CatBoost)"
    grep -qi "transformers\|huggingface" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Hugging Face Transformers (NLP/LLM)"
    grep -qi "langchain"       "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> LangChain (LLM orchestration)"
    grep -qi "llama.index\|llama_index" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> LlamaIndex (RAG)"
    grep -qi "openai"          "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> OpenAI SDK"
    grep -qi "anthropic"       "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Anthropic SDK (Claude)"
    grep -qi "mlflow"          "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> MLflow (experiment tracking)"
    grep -qi "wandb"           "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Weights & Biases (experiment tracking)"
    grep -qi "dvc"             "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> DVC (data versioning)"
    grep -qi "bentoml"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> BentoML (ML serving)"
    grep -qi "faiss\|chromadb\|qdrant\|weaviate\|pinecone" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Vector DB (RAG)"
    grep -qi "airflow"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Apache Airflow (pipelines)"
    grep -qi "prefect"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Prefect (pipelines)"
    grep -qi "dagster"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Dagster (pipelines)"
    grep -qi "pydantic"       "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Pydantic"
    grep -qi "pytest"         "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> pytest"
    grep -qi "black\|ruff\|flake8" "$PYFILE" 2>/dev/null && DETECTED="$DETECTED\n  -> Python linter detected"
  fi
  if [ -n "$PUBSPEC" ]; then
    grep -q "flutter"         "$PUBSPEC" 2>/dev/null && DETECTED="$DETECTED\n  -> Flutter app"
  fi
  if [ -n "$BUILD_GRADLE" ]; then
    grep -q "android"         "$BUILD_GRADLE" 2>/dev/null && DETECTED="$DETECTED\n  -> Android"
    grep -q "kotlin"          "$BUILD_GRADLE" 2>/dev/null && DETECTED="$DETECTED\n  -> Kotlin"
    grep -q "spring"          "$BUILD_GRADLE" 2>/dev/null && DETECTED="$DETECTED\n  -> Spring Boot"
  fi
  if [ -n "$POM_XML" ]; then
    grep -q "spring"          "$POM_XML" 2>/dev/null && DETECTED="$DETECTED\n  -> Spring Boot"
    grep -q "quarkus"         "$POM_XML" 2>/dev/null && DETECTED="$DETECTED\n  -> Quarkus"
  fi
  if [ -n "$COMPOSER" ]; then
    grep -q "laravel"         "$COMPOSER" 2>/dev/null && DETECTED="$DETECTED\n  -> Laravel"
    grep -q "symfony"         "$COMPOSER" 2>/dev/null && DETECTED="$DETECTED\n  -> Symfony"
  fi

  # ── Monorepo tools ─────────────────────────────────────────────────────────
  [ -n "$TURBO_JSON" ]     && DETECTED="$DETECTED\n- turbo.json -> Turborepo (monorepo)"
  [ -n "$NX_JSON" ]        && DETECTED="$DETECTED\n- nx.json -> Nx (monorepo)"
  [ -n "$LERNA_JSON" ]     && DETECTED="$DETECTED\n- lerna.json -> Lerna (monorepo)"
  [ -n "$PNPM_WORKSPACE" ] && DETECTED="$DETECTED\n- pnpm-workspace.yaml -> pnpm workspaces (monorepo)"

  # ── Infrastructure ─────────────────────────────────────────────────────────
  [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ] && DETECTED="$DETECTED\n- docker-compose -> Docker"
  [ -d "$PROJECT_ROOT/.github/workflows" ]  && DETECTED="$DETECTED\n- .github/workflows -> GitHub Actions"
  [ -f "$PROJECT_ROOT/vercel.json" ]        && DETECTED="$DETECTED\n- vercel.json -> Vercel"
  [ -f "$PROJECT_ROOT/fly.toml" ]           && DETECTED="$DETECTED\n- fly.toml -> Fly.io"
  [ -n "$SERVERLESS_YML" ]                  && DETECTED="$DETECTED\n- serverless.yml -> Serverless Framework (AWS Lambda)"
  [ -n "$FIREBASE_JSON" ]                   && DETECTED="$DETECTED\n- firebase.json -> Firebase"
  [ -n "$WRANGLER" ]                        && DETECTED="$DETECTED\n- wrangler.toml -> Cloudflare Workers"
  [ -n "$NETLIFY" ]                         && DETECTED="$DETECTED\n- netlify.toml -> Netlify"
  [ -n "$TERRAFORM_TF" ]                    && DETECTED="$DETECTED\n- *.tf -> Terraform/OpenTofu (IaC)"
  [ -n "$ANSIBLE_CFG" ]                     && DETECTED="$DETECTED\n- ansible.cfg -> Ansible"
  [ -n "$GITLAB_CI" ]                       && DETECTED="$DETECTED\n- .gitlab-ci.yml -> GitLab CI"
  [ -n "$CIRCLE_CI" ]                       && DETECTED="$DETECTED\n- .circleci/config.yml -> CircleCI"
  [ -n "$JENKINS" ]                         && DETECTED="$DETECTED\n- Jenkinsfile -> Jenkins"
  [ -n "$AZURE_PIPELINES" ]                 && DETECTED="$DETECTED\n- azure-pipelines.yml -> Azure Pipelines"

  # ── Desktop ─────────────────────────────────────────────────────────────────
  [ -n "$ELECTRON_CFG" ]  && DETECTED="$DETECTED\n- electron-builder.yml -> Electron (desktop app)"
  [ -n "$TAURI_CFG" ]     && DETECTED="$DETECTED\n- tauri.conf.json -> Tauri (desktop app)"

  # ── Data / ML ───────────────────────────────────────────────────────────────
  [ -n "$DBT_PROJECT" ]   && DETECTED="$DETECTED\n- dbt_project.yml -> dbt (data transformation)"
  [ -n "$AIRFLOW_CFG" ]   && DETECTED="$DETECTED\n- airflow.cfg -> Apache Airflow"
  [ -n "$MLFLOW" ]        && DETECTED="$DETECTED\n- MLproject -> MLflow (experiment tracking)"
  [ -n "$DVC_FILE" ]      && DETECTED="$DETECTED\n- .dvc -> DVC (data versioning)"
  [ -n "$DAGSTER_FILE" ]  && DETECTED="$DETECTED\n- workspace.yaml -> Dagster (pipelines)"
  [ -n "$OLLAMA_FILE" ]   && DETECTED="$DETECTED\n- Modelfile -> Ollama (local LLM)"
  [ -n "$JUPYTER" ]       && DETECTED="$DETECTED\n- *.ipynb -> Jupyter Notebooks (ML/data science)"

  # ── Databases ───────────────────────────────────────────────────────────────
  grep -r "postgresql\|postgres" "$PROJECT_ROOT" --include="*.yml" --include="*.yaml" --include=".env.example" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- PostgreSQL detected"
  grep -r "redis" "$PROJECT_ROOT" --include="*.yml" --include="*.yaml" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- Redis detected"
  grep -r "mongodb\|mongo:" "$PROJECT_ROOT" --include="*.yml" --include="*.yaml" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- MongoDB detected"
  grep -r "supabase" "$PROJECT_ROOT" --include="*.ts" --include="*.py" -l 2>/dev/null | head -1 | grep -q . && DETECTED="$DETECTED\n- Supabase detected"

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

PROJECT_NAME=$(echo "$MANIFEST" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('project',{}).get('name','Projet'))" 2>/dev/null || echo "Projet")
LEARNING_FILE=$(echo "$MANIFEST" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('context',{}).get('learning_file','learning.md'))" 2>/dev/null || echo "learning.md")
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

# ─── Signal 8.5 — Handoff de session précédente ──────────────────────────────
HANDOFF=""
if [ -f "$PROJECT_ROOT/.template/handoff.md" ]; then
  HANDOFF=$(head -50 "$PROJECT_ROOT/.template/handoff.md" 2>/dev/null || echo "")
fi

python3 - "$PROJECT_NAME" "$GIT_BRANCH" "$GIT_STATUS" "$GIT_LOG" "$MANIFEST" "$CUSTOM_RULES" "$LEARNING_FILE" "$LEARNING" "$COVERAGE" "$DEPS_ALERT" "$CI_STATUS" "$TECH_DEBT" "$OLD_BRANCHES" "$HOT_FILES" "$PENDING_MIGRATIONS" "$HANDOFF" <<'PYEOF'
import json, sys
name, branch, status, log, manifest, rules, lfile, learning = sys.argv[1:9]
coverage, deps_alert, ci_status, tech_debt = sys.argv[9:13]
old_branches, hot_files, pending_migrations = sys.argv[13:16]
handoff = sys.argv[16] if len(sys.argv) > 16 else ""

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

if rules:
    ctx += f"\n\nRegles custom:\n{rules}"
ctx += f"\n\n{lfile} (dernieres 60 lignes):\n{learning}"

if handoff.strip():
    ctx += f"\n\n=== HANDOFF SESSION PRECEDENTE ===\n{handoff}"

print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
PYEOF
