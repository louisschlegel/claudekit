# claudekit

[![Validate](https://github.com/louisschlegel/claudekit/actions/workflows/validate.yml/badge.svg)](https://github.com/louisschlegel/claudekit/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](.template/version.json)

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
├── CLAUDE.md                    # Orchestrateur — routing 23 intents
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
└── ...                          # Tes 16 agents et 22 workflows
```

---

## Architecture du système

```
template/
├── CLAUDE.md                        # Orchestrateur — routing table (23 intents) + règles
├── project.manifest.json            # {} → déclenche setup | rempli → contexte
├── project.manifest.EXAMPLE.json   # Référence complète du schema
├── learning.md.template             # Template pour la mémoire persistante
├── install.sh                       # One-liner pour projets legacy
│
├── scripts/
│   ├── gen.py                       # Générateur principal (manifest → tout) — --dry-run, --diff
│   ├── claudekit.py                 # CLI unifié : validate, check, gen, bump, status, install
│   ├── migrate-template.py          # Migration manifest entre versions (1.0.x → 1.1.0 → ...)
│   ├── auto-learn.py                # Extrait les handoffs JSON agents → learning.md (--deduplicate)
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
│   │   └── user-prompt-submit.sh    # Bootstrap (23 intents + 8 patterns injection)
│   └── agents/                      # 16 agents spécialisés
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
│       ├── cost-analyst.md          # Optimisation coûts cloud (AWS/GCP/Azure) + LLM tokens
│       ├── spec-reader.md           # Parse cahier des charges → manifest + backlog + issues
│       ├── data-engineer.md         # Pipelines data, dbt, Airflow, streaming
│       ├── ml-engineer.md           # MLOps : train → serve → monitor
│       ├── devops-engineer.md       # Infra, CI/CD, observabilité, résilience
│       └── template-improver.md     # Meta-agent : améliore le template
│
├── workflows/                       # 22 workflows end-to-end
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
│   ├── api-design.md                # API-first : spec → review → mock → implem
│   ├── a-b-test.md                  # Power analysis → feature flags → significance → ship/kill
│   ├── data-quality.md              # Great Expectations + dbt + ISO 8000 score + SLA
│   ├── llm-eval.md                  # RAGAS + hallucination detection + BLEU/ROUGE + deploy gate
│   ├── spec-to-project.md           # Cahier des charges → manifest + backlog + arch + GitHub issues
│   ├── code-review.md               # PR review structuré (BLOCKER/WARNING/SUGGESTION) → gh pr review
│   ├── monitoring-setup.md          # Prometheus/Grafana/Loki/Sentry → dashboards + alertes + SLOs
│   ├── cost-optimization.md         # Audit cloud + LLM → recommandations ROI + budget alerts
│   └── dependency-audit.md          # CVE + licences + deps fantômes → rapport sans modification
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
- **Intent classification** : 23 intents détectés automatiquement

| Intent | Mots-clés déclencheurs |
|--------|----------------------|
| `hotfix` | urgence prod, emergency, production down |
| `incident` | incident prod, outage, SLA breach, P1/P2 |
| `db-migration` | migration db, alter table, add column |
| `perf-test` | load test, benchmark, locust, k6 |
| `publish` | publie sur npm/pypi, npm publish |
| `api-design` | design api, nouvel endpoint, openapi |
| `ab-test` | a/b test, feature flag, expérience, power analysis, significance |
| `data-quality` | qualité des données, great expectations, dbt test, validation données |
| `llm-eval` | évalue le rag, llm eval, ragas, hallucination, benchmark llm |
| `spec-to-project` | cahier des charges, voici les specs, voici mon brief, PRD, analyse ce document |
| `code-review` | review cette PR, relis ce code, code review, review le diff, relecture |
| `monitoring-setup` | setup monitoring, prometheus, grafana, datadog, observabilité, alertes |
| `cost-optimization` | optimise les coûts, trop cher AWS, facture cloud, rightsizing, coûts LLM |
| `dependency-audit` | audit les dépendances, vérifie les CVE, npm audit, pip-audit, licence check |
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
| `cost-analyst` | Optimisation coûts cloud (AWS/GCP/Azure) + LLM tokens | — |
| `spec-reader` | Parse cahier des charges → manifest + backlog + issues GitHub | project.manifest.json, learning.md, backlog.md |
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
| `a-b-test.md` | `ab-test` | ml-engineer → tester → reviewer |
| `data-quality.md` | `data-quality` | data-engineer → tester → reviewer |
| `llm-eval.md` | `llm-eval` | ml-engineer → tester → reviewer |
| `spec-to-project.md` | `spec-to-project` | spec-reader → architect → doc-writer |
| `code-review.md` | `code-review` | explorer → security-auditor → reviewer → architect |
| `monitoring-setup.md` | `monitoring-setup` | devops-engineer → architect → doc-writer |
| `cost-optimization.md` | `cost-optimization` | cost-analyst → architect → devops-engineer |
| `dependency-audit.md` | `dependency-audit` | security-auditor → reviewer |

---

## Examples de manifests

Le dossier [`examples/`](examples/) contient des manifests pré-configurés :

| Fichier | Stack |
|---------|-------|
| [`web-app.manifest.json`](examples/web-app.manifest.json) | Next.js + FastAPI + PostgreSQL + Vercel |
| [`api.manifest.json`](examples/api.manifest.json) | FastAPI + PostgreSQL + Docker |
| [`ml.manifest.json`](examples/ml.manifest.json) | PyTorch + MLflow + FastAPI |
| [`mobile.manifest.json`](examples/mobile.manifest.json) | React Native + Expo + Turborepo |
| [`iac.manifest.json`](examples/iac.manifest.json) | Terraform + AWS + EKS + Kubernetes |
| [`cli.manifest.json`](examples/cli.manifest.json) | Python CLI (Typer + Rich) → PyPI |

Copier le manifest le plus proche de ton projet, le renommer `project.manifest.json`, puis lancer `python3 scripts/gen.py`.

---

## Génération

`scripts/gen.py` lit le manifest et génère :

| Fichier | Ce qui est généré |
|---------|-------------------|
| `.claude/settings.local.json` | Permissions Bash adaptées au stack |
| `.claude/hooks/session-start.sh` | Contexte + 7 signaux opérationnels |
| `.claude/hooks/user-prompt-submit.sh` | 23 intents + injection detection |
| `.git/hooks/pre-push` | Secret scan + lint + tests avant chaque push (installé par gen.py) |
| `scripts/migrate-template.py` | Migration automatique manifest entre versions |
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

## Commandes utiles

```bash
# claudekit CLI (nouveau en v1.1.0)
python3 scripts/claudekit.py status     # Vue d'ensemble : version, agents, workflows, scripts
python3 scripts/claudekit.py validate   # CI complète en local
python3 scripts/claudekit.py gen        # Régénère la config depuis project.manifest.json
python3 scripts/claudekit.py bump patch # Bump version (patch/minor/major)
python3 scripts/claudekit.py install /path/to/project  # Installe dans un projet existant

# gen.py options avancées
python3 scripts/gen.py --dry-run        # Prévisualise les fichiers générés sans écrire
python3 scripts/gen.py --diff           # Montre les diffs avec la config actuelle

# auto-learn
python3 scripts/auto-learn.py --deduplicate  # Déduplique les entrées cross-session

# migrate-template (mise à jour du template)
python3 scripts/migrate-template.py --check  # Vérifie si des migrations sont disponibles
python3 scripts/migrate-template.py          # Applique les migrations automatiquement
python3 scripts/migrate-template.py --dry-run  # Simule sans écrire

# make shortcuts
make validate      # CI complète en local
make check         # Validation rapide avant de pusher
make gen           # Alias pour gen.py
make bump-patch    # Bump version patch (1.0.0 → 1.0.1)
make changelog     # Met à jour CHANGELOG.md depuis git log
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/manifest-reference.md`](docs/manifest-reference.md) | Référence complète du schema manifest (tous les champs, types, valeurs) |
| [`CONTRIBUTING.md`](.github/CONTRIBUTING.md) | Ajouter un agent, un workflow, un stack |
| [`SECURITY.md`](SECURITY.md) | Responsible disclosure + design sécurité |
| [`examples/`](examples/) | Manifests pré-configurés pour 4 types de projet |

---

## Contributing

Voir [CONTRIBUTING.md](.github/CONTRIBUTING.md) — bugs, nouveaux agents, stacks, workflows.

Idées et discussions : [GitHub Discussions](https://github.com/louisschlegel/claudekit/discussions)

Roadmap : [Issue #1](https://github.com/louisschlegel/claudekit/issues/1)

## License

[MIT](LICENSE)
