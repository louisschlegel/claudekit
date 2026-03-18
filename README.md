# claudekit

[![Validate](https://github.com/louisschlegel/claudekit/actions/workflows/validate.yml/badge.svg)](https://github.com/louisschlegel/claudekit/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](.template/version.json)

Un template auto-configurant, auto-améliorant, qui génère toute l'infrastructure Claude Code adaptée à n'importe quel projet — hooks, permissions, MCP servers, guards qualité, sous-agents, workflows complets — à partir d'un simple interview conversationnel.

---

## Installation

### Nouveau projet
```bash
git clone https://github.com/louisschlegel/claudekit mon-projet
cd mon-projet
claude
```

### Projet legacy — one-liner
```bash
curl -fsSL https://raw.githubusercontent.com/louisschlegel/claudekit/main/install.sh | bash
claude
```

### Projet legacy — manuel
```bash
cd mon-projet-existant/
curl -fsSL https://raw.githubusercontent.com/louisschlegel/claudekit/main/install.sh | bash -s .
claude
```

Claude détecte le manifest vide → lance le setup automatiquement → génère toute la config.

---

## Ce que tu obtiens après le setup

```
ton-projet/
├── CLAUDE.md                    # Orchestrateur — routing 15 intents
├── project.manifest.json        # Config générée lors du setup
├── learning.md                  # Mémoire institutionnelle (auto-alimentée)
├── .mcp.json                    # Serveurs MCP configurés
├── .claude/
│   ├── settings.local.json      # Permissions Bash adaptées à ton stack
│   └── hooks/
│       ├── session-start.sh     # Contexte session + 7 signaux opérationnels
│       ├── user-prompt-submit.sh # Intent classification + injection detection
│       ├── pre-bash-guard.sh    # Blocage commandes destructives
│       ├── post-edit.sh         # Guards qualité (lint, type-check, migrations)
│       └── stop.sh              # Auto-learning en fin de session
└── ...                          # Tes 14 agents et 14 workflows
```

---

## Architecture du système

```
template/
├── CLAUDE.md                        # Orchestrateur — routing table (15 intents) + règles
├── project.manifest.json            # {} → déclenche setup | rempli → contexte
├── project.manifest.EXAMPLE.json   # Référence complète du schema
├── learning.md.template             # Template pour la mémoire persistante
├── install.sh                       # One-liner pour projets legacy
│
├── scripts/
│   ├── gen.py                       # Générateur principal (manifest → tout)
│   ├── auto-learn.py                # Extrait les handoffs JSON agents → learning.md
│   ├── self-improve.py              # Moteur d'observation (log friction events)
│   ├── version-bump.py              # Semantic versioning (patch/minor/major)
│   └── changelog-gen.py             # git log → CHANGELOG.md (conventional commits)
│
├── examples/
│   ├── web-app.manifest.json        # SaaS Next.js + FastAPI + PostgreSQL
│   ├── api.manifest.json            # REST API Python + Docker
│   ├── ml.manifest.json             # MLOps PyTorch + MLflow + FastAPI
│   └── mobile.manifest.json         # React Native + Expo + Turborepo
│
├── .claude/
│   ├── hooks/
│   │   ├── session-start.sh         # Bootstrap (40+ détecteurs stack + 7 signaux)
│   │   └── user-prompt-submit.sh    # Bootstrap (15 intents + 8 patterns injection)
│   └── agents/                      # 14 agents spécialisés
│       ├── architect.md             # Conception + ADR + JSON handoff
│       ├── reviewer.md              # Code review (BLOCKER/WARNING/SUGGESTION)
│       ├── tester.md                # Tests exhaustifs
│       ├── security-auditor.md      # OWASP + deps + secrets
│       ├── debug-detective.md       # Root cause + 5 whys + git bisect
│       ├── deployer.md              # Déploiement sécurisé + rollback
│       ├── explorer.md              # Cartographie de codebase
│       ├── doc-writer.md            # Docstrings + README + API docs
│       ├── performance-analyst.md   # Profiling + optimisation
│       ├── release-manager.md       # Orchestration release + changelog
│       ├── data-engineer.md         # Pipelines data, dbt, Airflow, streaming
│       ├── ml-engineer.md           # MLOps : train → serve → monitor
│       ├── devops-engineer.md       # Infra, CI/CD, observabilité, résilience
│       └── template-improver.md     # Meta-agent : améliore le template
│
├── workflows/                       # 14 workflows end-to-end
│   ├── feature.md                   # Feature branch → merge + auto-learn
│   ├── bugfix.md                    # Bug → root cause → test → fix
│   ├── hotfix.md                    # Correctif urgent prod (express)
│   ├── release.md                   # Tests → audit → changelog → tag → deploy
│   ├── security-audit.md            # Scan complet + findings
│   ├── refactor.md                  # Refactoring sécurisé
│   ├── onboarding.md                # Nouveau projet ou legacy
│   ├── self-improve.md              # Auto-amélioration du template
│   ├── dependency-update.md         # Audit → grouper par risque → update
│   ├── db-migration.md              # Migrations SQL zero-downtime + rollback
│   ├── incident-response.md         # P1/P2 — mitigation → RCA → post-mortem
│   ├── performance-baseline.md      # Profiling → baseline → benchmark
│   ├── publish-package.md           # npm/PyPI/crates.io — build → sign → publish
│   └── api-design.md                # API-first : spec → review → mock → implem
│
└── .template/
    ├── version.json                 # Version du template + historique
    ├── known-patterns.json          # Patterns en attente de validation
    └── improvements.log             # Observations JSONL (runtime, non commité)
```

---

## Comment ça marche

### 1. Intent classification (UserPromptSubmit hook)

Chaque message est analysé avant d'arriver à Claude :
- **Injection detection** : bloque 8 patterns de prompt injection
- **Intent classification** : 15 intents détectés automatiquement

| Intent | Mots-clés déclencheurs |
|--------|----------------------|
| `hotfix` | urgence prod, emergency, production down |
| `incident` | incident prod, outage, SLA breach, P1/P2 |
| `db-migration` | migration db, alter table, add column |
| `perf-test` | load test, benchmark, locust, k6 |
| `publish` | publie sur npm/pypi, npm publish |
| `api-design` | design api, nouvel endpoint, openapi |
| `feature` | implémente, ajoute, nouvelle feature |
| `bugfix` | bug, crash, erreur, fixe, regression |
| `release` | release, prépare une version, tag v |
| `security-audit` | audit, sécurité, vulnérabilité, CVE |
| `update-deps` | mets à jour les dépendances, upgrade packages |
| `refactor` | refactor, nettoie, restructure |
| `onboard` | setup, initialise, configure le projet |
| `improve-template` | améliore le template, self-improve |
| `question` | comment, explique, pourquoi, what is |

### 2. Contexte session (SessionStart hook)

**Manifest vide** → détection automatique du stack (40+ marqueurs) : package.json, requirements.txt, go.mod, Cargo.toml, dbt_project.yml, MLproject, pubspec.yaml, build.gradle, *.tf, serverless.yml, etc.

**Manifest rempli** → 7 signaux opérationnels injectés à chaque session :

| Signal | Source |
|--------|--------|
| Couverture de tests | coverage.xml / lcov / coverage-summary.json |
| Migrations en attente | `python3 manage.py makemigrations --check` |
| Dépendances vulnérables | pip-audit / npm audit |
| Branches stale (> 14j) | git for-each-ref |
| Statut CI/CD | `gh run list` |
| Fichiers chauds sans tests | git log --name-only + analyse |
| Dette technique | grep TODO/FIXME/HACK |

### 3. Sécurité pré-exécution (PreToolUse)

Bloque avant exécution : `rm -rf /`, `DROP DATABASE`, `git push --force origin main`, `chmod 777`, etc.

### 4. Qualité post-edit (PostToolUse)

Après chaque fichier modifié (selon `guards` dans le manifest) :
- **lint** : ruff / eslint
- **type_check** : tsc --noEmit
- **migration_check** : Django makemigrations --check
- **i18n_check** : parité clés fr/en
- **test_on_edit** : pytest/jest sur le fichier correspondant

### 5. Auto-learning (Stop hook + auto-learn.py)

Chaque fin de session → observation JSONL dans `.template/improvements.log` → tous les N sessions → agent `template-improver` analyse et améliore.

`auto-learn.py` extrait les HANDOFF JSON des agents → sections structurées dans `learning.md`.

---

## Réseau d'agents

Tous les agents ont un **HANDOFF JSON structuré** pour passage de contexte, et des **checklists par type de projet** (web-app, api, mobile, library, data, ml, iac).

| Agent | Rôle | Écrit |
|-------|------|-------|
| `architect` | Conception + ADR + trade-offs | learning.md |
| `reviewer` | Code review (BLOCKER/WARNING/SUGGESTION) | — |
| `tester` | Tests exhaustifs + edge cases | Fichiers de test |
| `security-auditor` | OWASP + deps + secrets | — |
| `debug-detective` | Root cause + 5 whys + git bisect | — |
| `deployer` | Déploiement + rollback | Tags git |
| `explorer` | Cartographie codebase | — |
| `doc-writer` | Docstrings + README + API docs | .md + docstrings |
| `performance-analyst` | Profiling + optimisation | — |
| `release-manager` | Orchestration release + changelog | CHANGELOG |
| `data-engineer` | Pipelines data, dbt, Airflow, streaming | dbt models, DAGs |
| `ml-engineer` | MLOps : framing → train → serve → monitor | Scripts ML |
| `devops-engineer` | Infra, CI/CD, observabilité, résilience | Dockerfile, CI, IaC |
| `template-improver` | Améliore le template lui-même | Fichiers template |

---

## Workflows complets

| Workflow | Intent | Agents impliqués |
|----------|--------|-----------------|
| `feature.md` | `feature` | architect → tester → reviewer → doc-writer |
| `bugfix.md` | `bugfix` | debug-detective → tester → reviewer |
| `hotfix.md` | `hotfix` | debug-detective → reviewer → deployer |
| `release.md` | `release` | security-auditor → release-manager → deployer |
| `security-audit.md` | `security-audit` | security-auditor → reviewer |
| `refactor.md` | `refactor` | explorer → architect → tester → reviewer |
| `onboarding.md` | `onboard` | explorer → architect → doc-writer |
| `self-improve.md` | `improve-template` | template-improver |
| `dependency-update.md` | `update-deps` | security-auditor → reviewer |
| `db-migration.md` | `db-migration` | architect → tester → deployer |
| `incident-response.md` | `incident` | debug-detective → devops-engineer |
| `performance-baseline.md` | `perf-test` | performance-analyst → architect |
| `publish-package.md` | `publish` | security-auditor → release-manager |
| `api-design.md` | `api-design` | architect → reviewer → doc-writer |

---

## Examples de manifests

Le dossier [`examples/`](examples/) contient des manifests pré-configurés :

| Fichier | Stack |
|---------|-------|
| [`web-app.manifest.json`](examples/web-app.manifest.json) | Next.js + FastAPI + PostgreSQL + Vercel |
| [`api.manifest.json`](examples/api.manifest.json) | FastAPI + PostgreSQL + Docker |
| [`ml.manifest.json`](examples/ml.manifest.json) | PyTorch + MLflow + FastAPI |
| [`mobile.manifest.json`](examples/mobile.manifest.json) | React Native + Expo + Turborepo |

Copier le manifest le plus proche de ton projet, le renommer `project.manifest.json`, puis lancer `python3 scripts/gen.py`.

---

## Génération

`scripts/gen.py` lit le manifest et génère :

| Fichier | Ce qui est généré |
|---------|-------------------|
| `.claude/settings.local.json` | Permissions Bash adaptées au stack |
| `.claude/hooks/session-start.sh` | Contexte + 7 signaux opérationnels |
| `.claude/hooks/user-prompt-submit.sh` | 15 intents + injection detection |
| `.claude/hooks/pre-bash-guard.sh` | Blocage commandes destructives |
| `.claude/hooks/post-edit.sh` | Guards qualité |
| `.claude/hooks/stop.sh` | Auto-learning async |
| `.mcp.json` | Serveurs MCP |

---

## Self-improvement

```
Session → stop.sh → self-improve.py (observation JSONL)
                           ↓ tous les N sessions
                  template-improver agent
                           ↓
    AUTO → appliqué | APPROVAL → diff proposé | PR → branche créée
                           ↓
              version-bump.py → .template/version.json
```

---

## 4 couches de sécurité indépendantes

1. **Permissions whitelist** — seules les commandes nécessaires au stack sont autorisées
2. **Pre-tool gate** — bloque les commandes destructives avant exécution
3. **Post-edit guards** — lint + type-check + scan secrets après chaque édition
4. **Prompt injection detection** — bloque les tentatives de manipulation

---

## Stacks supportés

**Langages (31) :** Python, TypeScript, JavaScript, Go, Rust, Ruby, PHP, Java, Elixir, Swift, Kotlin, C, C++, C#/.NET, F#, Dart/Flutter, Scala, Clojure, Groovy, R, Bash, Lua, Perl, Haskell, Nim, Zig, OCaml

**Frameworks web :** Django, FastAPI, Flask, React, Next.js, Vue, Nuxt, Angular, Svelte, Remix, Astro, NestJS, Express, Laravel, Spring Boot, Quarkus

**Data/ML :** PyTorch, TensorFlow, JAX, scikit-learn, XGBoost, LightGBM, Hugging Face, LangChain, LlamaIndex, MLflow, W&B, DVC, dbt, Airflow, Prefect, Dagster, Spark, Ray, Kafka, FAISS, Chroma, Qdrant, vLLM, Ollama

**Mobile/Desktop :** Flutter, React Native, Expo, Electron, Tauri, iOS (Swift), Android (Kotlin)

**Infra :** Docker, Kubernetes, Terraform, Ansible, Vercel, Railway, AWS, GCloud, Azure, Serverless, Firebase, Cloudflare Workers

**Bases de données :** PostgreSQL, MySQL, Redis, MongoDB, SQLite, Elasticsearch, Cassandra, DynamoDB, BigQuery, Snowflake, ClickHouse, Neo4j, Pinecone

**Package managers :** npm, pnpm, yarn, bun, deno, pip, uv, poetry, conda, cargo, nix

**Monorepos :** Turborepo, Nx, Lerna, Bazel, Buck, Pants

---

## MCP Servers configurables

| Server | Usage | Prérequis |
|--------|-------|-----------|
| `filesystem` | Accès fichiers étendu | npx |
| `github` | Issues, PRs, code search | `GITHUB_TOKEN` |
| `postgres` | Requêtes directes | `DATABASE_URL` |
| `sqlite` | Base SQLite locale | npx |
| `brave-search` | Recherche web | `BRAVE_API_KEY` |
| `slack` | Notifications | `SLACK_BOT_TOKEN` |
| `linear` | Issues Linear | `LINEAR_API_KEY` |
| `notion` | Pages Notion | `NOTION_API_KEY` |
| `playwright` | Browser automation | npx |
| `desktop-commander` | Contrôle desktop | npx |

> Gmail, Google Calendar et Canva sont des intégrations natives Claude.ai — pas de configuration MCP nécessaire.

---

## Portabilité

Tous les hooks utilisent `$BASH_SOURCE` pour se localiser — le template fonctionne depuis n'importe quel emplacement, sans configuration.

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
```

---

## Contributing

Voir [CONTRIBUTING.md](.github/CONTRIBUTING.md) — bugs, nouveaux agents, stacks, workflows.

## License

[MIT](LICENSE)
