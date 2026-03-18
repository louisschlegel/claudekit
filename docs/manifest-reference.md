# Manifest Reference

`project.manifest.json` est le fichier de configuration central de claudekit. Il est généré lors du setup interview et lu par `scripts/gen.py` pour produire tous les fichiers de configuration Claude Code.

---

## Schema complet

```json
{
  "project": { ... },
  "stack": { ... },
  "workflow": { ... },
  "ml": { ... },
  "mcp_servers": [ ... ],
  "guards": { ... },
  "agents": [ ... ],
  "workflows": [ ... ],
  "automation": { ... },
  "security": { ... },
  "notifications": { ... },
  "template": { ... }
}
```

---

## `project`

Identité du projet.

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `name` | string | ✅ | Nom du projet (sans espaces) |
| `description` | string | ✅ | Description courte (1-2 phrases) |
| `type` | string | ✅ | Type de projet (voir valeurs ci-dessous) |
| `language` | string | ✅ | Langue des commits et commentaires : `fr` ou `en` |

**Valeurs `type` :**
- `web-app` — Application web / SaaS
- `api` — API REST, GraphQL, gRPC
- `mobile` — iOS, Android, React Native, Flutter
- `desktop` — Electron, Tauri
- `data-pipeline` — Pipelines batch/streaming, ETL
- `ml` — Machine learning, MLOps, LLMs
- `library` — Package npm, PyPI, crates.io
- `monorepo` — Plusieurs apps dans un seul repo
- `iac` — Infrastructure as Code (Terraform, Ansible)
- `cli` — Outil en ligne de commande

---

## `stack`

Technologies utilisées. Détermine les permissions Bash générées par `gen.py`.

| Champ | Type | Description |
|-------|------|-------------|
| `languages` | string[] | Langages de programmation |
| `frameworks` | string[] | Frameworks applicatifs |
| `databases` | string[] | Bases de données |
| `runtime` | string | Runtime principal : `node`, `python`, `go`, `rust`, `jvm`, `dotnet` |
| `testing` | string[] | Frameworks de test |
| `linting` | string[] | Outils de lint |
| `package_managers` | string[] | Gestionnaires de paquets |
| `monorepo_tools` | string[] | Outils monorepo |
| `data_tools` | string[] | Outils data/ML |
| `serverless` | string[] | Plateformes serverless |
| `desktop_frameworks` | string[] | Frameworks desktop |

**Valeurs `languages` supportées :**
`python`, `typescript`, `javascript`, `go`, `rust`, `ruby`, `php`, `java`, `elixir`, `swift`, `kotlin`, `c`, `c++`, `cpp`, `csharp`, `dotnet`, `fsharp`, `dart`, `flutter`, `scala`, `clojure`, `groovy`, `r`, `bash`, `shell`, `lua`, `perl`, `haskell`, `nim`, `zig`, `ocaml`

**Valeurs `frameworks` détectés automatiquement :**
`django`, `fastapi`, `flask`, `celery`, `react`, `react-native`, `expo`, `nextjs`, `vuejs`, `nuxt`, `angular`, `svelte`, `remix`, `astro`, `nestjs`, `fastify`, `express`, `laravel`, `symfony`, `spring-boot`, `quarkus`, `pytorch`, `tensorflow`, `jax`, `sklearn`, `langchain`, `llamaindex`, `huggingface`, `mlflow`, `wandb`, `dvc`, `bentoml`, `airflow`, `prefect`, `dagster`, `dbt`, `electron`, `tauri`, `flutter`

**Valeurs `databases` :**
`postgresql`, `mysql`, `sqlite`, `redis`, `mongodb`, `elasticsearch`, `cassandra`, `dynamodb`, `bigquery`, `snowflake`, `clickhouse`, `neo4j`, `pinecone`, `chroma`, `qdrant`, `faiss`, `weaviate`

**Valeurs `package_managers` :**
`npm`, `pnpm`, `yarn`, `bun`, `deno`, `pip`, `uv`, `poetry`, `conda`, `cargo`, `nix`

**Valeurs `monorepo_tools` :**
`turborepo`, `nx`, `lerna`, `bazel`, `buck`, `pants`

**Valeurs `data_tools` :**
`jupyter`, `dbt`, `airflow`, `prefect`, `dagster`, `mlflow`, `wandb`, `dvc`, `bentoml`, `ollama`, `spark`, `ray`, `kafka`, `seldon`, `triton`, `vllm`, `llamacpp`

**Valeurs `serverless` :**
`serverless`, `sam`, `cdk`, `firebase`, `wrangler`, `netlify`

**Valeurs `desktop_frameworks` :**
`electron`, `tauri`

---

## `workflow`

Configuration du pipeline de développement.

| Champ | Type | Description |
|-------|------|-------------|
| `git_strategy` | string | `feature-branch`, `trunk-based`, `gitflow` |
| `ci_cd` | string | `github-actions`, `gitlab-ci`, `none` |
| `deploy_target` | string | Cible de déploiement (ex: `vercel`, `docker`, `kubernetes`, `railway`, `expo-eas`) |
| `auto_deploy` | boolean | Déploiement automatique après release |
| `commit_language` | string | `fr` ou `en` |
| `deploy_command` | string | Commande de déploiement |
| `environments` | string[] | Environnements disponibles (ex: `["staging", "production"]`) |
| `health_check_url` | string | URL de health check après déploiement |
| `smoke_tests` | string[] | Commandes de smoke tests post-déploiement |
| `github_releases` | boolean | Créer des GitHub Releases lors des releases |

---

## `ml`

Configuration spécifique aux projets ML. Ignoré si `project.type` ≠ `ml`.

| Champ | Type | Description |
|-------|------|-------------|
| `task_type` | string | `classification`, `regression`, `clustering`, `ranking`, `generation`, `embedding` |
| `frameworks` | string[] | Frameworks ML utilisés |
| `experiment_tracking` | string | `mlflow`, `wandb`, `none` |
| `data_versioning` | string | `dvc`, `lakeFS`, `none` |
| `serving` | string | `fastapi`, `triton`, `vllm`, `tgi`, `torchserve`, `sagemaker`, `vertex` |
| `vector_db` | string | `faiss`, `chroma`, `qdrant`, `weaviate`, `pinecone`, `none` |
| `target_latency_ms` | number | Latence cible d'inférence en ms |
| `target_metric` | string | Métrique principale (ex: `f1`, `auc`, `rmse`, `bleu`) |
| `baseline_score` | number | Score baseline à battre |

---

## `mcp_servers`

Liste des serveurs MCP à configurer dans `.mcp.json`.

```json
"mcp_servers": ["github", "postgres", "brave-search"]
```

| Valeur | Usage | Variable d'env requise |
|--------|-------|----------------------|
| `filesystem` | Accès fichiers étendu | — |
| `github` | Issues, PRs, code search | `GITHUB_TOKEN` |
| `postgres` | Requêtes PostgreSQL directes | `DATABASE_URL` |
| `sqlite` | Base SQLite locale | — |
| `brave-search` | Recherche web | `BRAVE_API_KEY` |
| `slack` | Envoi de messages Slack | `SLACK_BOT_TOKEN` |
| `linear` | Issues Linear | `LINEAR_API_KEY` |
| `notion` | Pages Notion | `NOTION_API_KEY` |
| `playwright` | Automatisation browser | — |
| `desktop-commander` | Contrôle desktop | — |

> Gmail, Google Calendar et Canva sont des intégrations natives Claude.ai — pas de configuration MCP.

---

## `guards`

Guards de qualité exécutés par `post-edit.sh` après chaque modification de fichier.

| Champ | Type | Description |
|-------|------|-------------|
| `lint` | boolean | Lint automatique (`ruff` pour Python, `eslint` pour TS/JS) |
| `type_check` | boolean | `tsc --noEmit` après édition de fichiers TypeScript |
| `test_on_edit` | boolean | Lance pytest/jest sur le fichier de test correspondant |
| `migration_check` | boolean | `makemigrations --check` après édition de models Django |
| `i18n_check` | boolean | Vérifie la parité des clés de traduction fr/en |
| `secret_scan` | boolean | Détecte les patterns de secrets dans les fichiers édités |

---

## `agents`

Liste des agents activés pour ce projet. Seuls les agents listés sont mentionnés dans le contexte de session.

```json
"agents": ["architect", "reviewer", "tester", "security-auditor", "deployer"]
```

**Agents disponibles :**
`architect`, `reviewer`, `tester`, `security-auditor`, `debug-detective`, `deployer`, `explorer`, `doc-writer`, `performance-analyst`, `release-manager`, `data-engineer`, `ml-engineer`, `devops-engineer`, `template-improver`

---

## `workflows`

Liste des workflows activés. Détermine ce qui est mentionné dans le setup et dans l'aide contextuelle.

```json
"workflows": ["feature", "bugfix", "hotfix", "release", "security-audit"]
```

**Workflows disponibles :**
`feature`, `bugfix`, `hotfix`, `release`, `security-audit`, `dependency-update`, `refactor`, `onboard`, `self-improve`, `db-migration`, `incident-response`, `performance-baseline`, `publish-package`, `api-design`

---

## `automation`

| Champ | Type | Défaut | Description |
|-------|------|--------|-------------|
| `self_improve_every_n_sessions` | number | `10` | Fréquence d'auto-amélioration (en sessions) |
| `learning_file` | string | `"learning.md"` | Chemin vers le fichier de mémoire |

---

## `security`

| Champ | Type | Description |
|-------|------|-------------|
| `secret_scan` | boolean | Activer le scan de secrets dans post-edit |
| `dependency_audit` | boolean | Audit des dépendances dans session-start |
| `owasp_check` | boolean | Inclure les checks OWASP dans le contexte de l'agent security-auditor |

---

## `notifications`

| Champ | Type | Description |
|-------|------|-------------|
| `slack_channel` | string | Canal Slack pour les notifications (ex: `"#deployments"`) |
| `on_deploy` | boolean | Notifier après chaque déploiement |
| `on_incident` | boolean | Notifier lors d'un incident P1/P2 |

---

## `template`

Métadonnées du template claudekit lui-même.

| Champ | Type | Description |
|-------|------|-------------|
| `version` | string | Version du template utilisée |
| `source` | string | Source du template (URL du repo) |
| `last_improved` | string | Date de la dernière auto-amélioration (ISO 8601) |

---

## Exemple minimal

```json
{
  "project": {
    "name": "my-api",
    "description": "REST API avec auth JWT",
    "type": "api",
    "language": "en"
  },
  "stack": {
    "languages": ["python"],
    "frameworks": ["fastapi"],
    "databases": ["postgresql", "redis"],
    "runtime": "python",
    "testing": ["pytest"],
    "linting": ["ruff"],
    "package_managers": ["uv"],
    "monorepo_tools": [],
    "data_tools": [],
    "serverless": [],
    "desktop_frameworks": []
  },
  "workflow": {
    "git_strategy": "feature-branch",
    "ci_cd": "github-actions",
    "deploy_target": "docker",
    "auto_deploy": false,
    "commit_language": "en"
  },
  "mcp_servers": ["github", "postgres"],
  "guards": {
    "lint": true,
    "type_check": false,
    "test_on_edit": true,
    "migration_check": false,
    "i18n_check": false,
    "secret_scan": true
  },
  "agents": ["architect", "reviewer", "tester", "security-auditor", "debug-detective"],
  "workflows": ["feature", "bugfix", "release", "security-audit"],
  "automation": {
    "self_improve_every_n_sessions": 10,
    "learning_file": "learning.md"
  }
}
```

Pour un exemple complet, voir [`project.manifest.EXAMPLE.json`](../project.manifest.EXAMPLE.json) ou le dossier [`examples/`](../examples/).
