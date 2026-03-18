# Template Universel Claude Code

Un template auto-configurant, auto-améliorant, qui génère toute l'infrastructure Claude Code adaptée à n'importe quel projet — hooks, permissions, MCP servers, guards qualité, sous-agents, workflows complets — à partir d'un simple interview conversationnel.

**Version template :** 1.0.0

---

## Démarrage rapide

### Nouveau projet
```bash
cp -r ~/Desktop/template/ ~/Desktop/mon-projet/
cd ~/Desktop/mon-projet/
claude
```
Claude détecte le manifest vide → lance le setup automatiquement.

### Projet legacy (activer sur un projet existant)
```bash
cd ~/Desktop/mon-projet-existant/

cp -r ~/Desktop/template/.claude/ ./.claude/
mkdir -p scripts workflows .template
cp ~/Desktop/template/scripts/gen.py ./scripts/gen.py
cp ~/Desktop/template/scripts/self-improve.py ./scripts/self-improve.py
cp ~/Desktop/template/scripts/version-bump.py ./scripts/version-bump.py
cp ~/Desktop/template/scripts/changelog-gen.py ./scripts/changelog-gen.py
cp ~/Desktop/template/scripts/auto-learn.py ./scripts/auto-learn.py
cp ~/Desktop/template/CLAUDE.md ./CLAUDE.md
cp -r ~/Desktop/template/.claude/agents/ ./.claude/agents/
cp -r ~/Desktop/template/workflows/ ./workflows/
echo '{}' > project.manifest.json

claude
```
Claude scanne le projet (package.json, requirements.txt, go.mod, Cargo.toml, docker-compose.yml, dbt_project.yml, MLproject, etc.), détecte le stack automatiquement, confirme avec toi, puis génère tout.

---

## Architecture du système

```
template/
├── CLAUDE.md                        # Orchestrateur — routing table (15 intents) + règles
├── project.manifest.json            # {} → déclenche setup | rempli → contexte
├── project.manifest.EXAMPLE.json   # Référence complète du schema
├── learning.md.template             # Template pour la mémoire persistante
├── CHANGELOG.md                     # Généré par scripts/changelog-gen.py
│
├── scripts/
│   ├── gen.py                       # Générateur principal (manifest → tout)
│   ├── auto-learn.py                # Extrait les handoffs JSON agents → learning.md
│   ├── self-improve.py              # Moteur d'observation (log friction events)
│   ├── version-bump.py              # Semantic versioning (patch/minor/major)
│   └── changelog-gen.py             # git log → CHANGELOG.md (conventional commits)
│
├── .claude/
│   ├── settings.local.json          # Bootstrap (perms + 2 hooks) → remplacé par gen.py
│   ├── hooks/
│   │   ├── session-start.sh         # Bootstrap → remplacé par gen.py
│   │   ├── user-prompt-submit.sh    # Bootstrap → remplacé par gen.py
│   │   ├── pre-bash-guard.sh        # Généré par gen.py
│   │   ├── post-edit.sh             # Généré par gen.py
│   │   └── stop.sh                  # Généré par gen.py
│   └── agents/                      # 14 agents spécialisés
│       ├── architect.md             # Conception + ADR + JSON handoff
│       ├── reviewer.md              # Code review (BLOCKER/WARNING/SUGGESTION)
│       ├── tester.md                # Tests exhaustifs (pytest/jest/vitest/go test)
│       ├── security-auditor.md      # OWASP + deps + secrets + config
│       ├── debug-detective.md       # Root cause analysis + 5 whys + git bisect
│       ├── deployer.md              # Déploiement sécurisé + rollback
│       ├── explorer.md              # Cartographie de codebase
│       ├── doc-writer.md            # Docstrings + README + API docs
│       ├── performance-analyst.md   # Profiling + optimisation
│       ├── release-manager.md       # Orchestration de release + changelog
│       ├── data-engineer.md         # Pipelines data, dbt, Airflow, streaming
│       ├── ml-engineer.md           # MLOps complet : train → serve → monitor
│       ├── devops-engineer.md       # Infra, CI/CD, observabilité, résilience
│       └── template-improver.md     # Meta-agent : améliore le template
│
├── workflows/                       # 14 workflows end-to-end
│   ├── feature.md                   # Feature branch → merge + auto-learn
│   ├── bugfix.md                    # Bug → root cause → test → fix + auto-learn
│   ├── hotfix.md                    # Correctif urgent prod (express, sans rituel)
│   ├── release.md                   # Tests → audit → changelog → tag → deploy
│   ├── security-audit.md            # Scan complet + traitement des findings
│   ├── refactor.md                  # Refactoring sécurisé (tests avant/après)
│   ├── onboarding.md                # Nouveau projet ou legacy
│   ├── self-improve.md              # Auto-amélioration du template
│   ├── dependency-update.md         # Audit → grouper par risque → update → test
│   ├── db-migration.md              # Migrations SQL zero-downtime + rollback
│   ├── incident-response.md         # P1/P2 — mitigation → RCA → post-mortem
│   ├── performance-baseline.md      # Profiling → baseline → optimisation → benchmark
│   ├── publish-package.md           # npm/PyPI/crates.io — build → sign → publish
│   └── api-design.md                # API-first : spec → review → mock → implem
│
└── .template/
    ├── version.json                 # Version du template + historique
    ├── known-patterns.json          # Patterns en attente de validation
    └── improvements.log             # Observations JSONL (alimenté par stop.sh)
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
| `db-migration` | migration db, alter table, add column, schema migration |
| `perf-test` | load test, benchmark, locust, k6, stress test |
| `publish` | publie sur npm/pypi, npm publish, release library |
| `api-design` | design api, nouvel endpoint, openapi, graphql schema |
| `feature` | implémente, ajoute, nouvelle feature, implement |
| `bugfix` | bug, crash, erreur, fixe, regression |
| `release` | release, prépare une version, tag v |
| `security-audit` | audit, sécurité, vulnérabilité, CVE |
| `update-deps` | mets à jour les dépendances, upgrade packages |
| `refactor` | refactor, nettoie, restructure, dette technique |
| `onboard` | setup, initialise, configure le projet, legacy |
| `improve-template` | améliore le template, self-improve |
| `question` | comment, explique, pourquoi, what is |

### 2. Contexte session (SessionStart hook)

À chaque démarrage de session :

**Manifest vide** → détection automatique du stack (40+ marqueurs) :
- Langages : package.json, requirements.txt, go.mod, Cargo.toml, mix.exs, composer.json, *.csproj, build.gradle, build.sbt, pubspec.yaml, CMakeLists.txt, *.tf, build.zig, dune-project
- Frameworks : React, Next.js, Vue, Angular, Svelte, Remix, Astro, FastAPI, Django, Flask, NestJS, Spring Boot, Laravel, Flutter, PyTorch, TensorFlow, LangChain, LlamaIndex, Hugging Face, MLflow, Airflow, dbt
- Monorepos : turbo.json, nx.json, lerna.json, pnpm-workspace.yaml
- Serverless : serverless.yml, firebase.json, wrangler.toml, netlify.toml
- CI/CD : .github/workflows/, .gitlab-ci.yml, Jenkinsfile, azure-pipelines.yml

**Manifest rempli** → 7 signaux opérationnels injectés en contexte :
1. **Couverture de tests** : % actuel (coverage.xml, lcov, coverage-summary.json)
2. **Migrations en attente** : Django `makemigrations --check`
3. **Dépendances vulnérables** : pip-audit / npm audit
4. **Branches feature stales** : > 14 jours sans merge
5. **Statut CI/CD** : dernière run GitHub Actions
6. **Fichiers chauds sans tests** : modifiés souvent, peu couverts
7. **Dette technique** : count TODO/FIXME dans le code

### 3. Sécurité pré-exécution (PreToolUse hook)

Avant chaque commande Bash :
- Bloque les patterns destructifs (`rm -rf /`, `DROP DATABASE`, `git push --force origin main`, `chmod 777`, etc.)

### 4. Qualité post-edit (PostToolUse hook)

Après chaque modification de fichier (configuré via `guards` dans le manifest) :
- **lint** : ruff (Python), eslint (TypeScript/JS)
- **type_check** : tsc --noEmit
- **migration_check** : Django `makemigrations --check --dry-run`
- **i18n_check** : parité clés fr/en
- **test_on_edit** : pytest/jest sur le fichier de test correspondant

### 5. Auto-learning (Stop hook + auto-learn.py)

En fin de session :
- `stop.sh` → `self-improve.py` log une observation JSONL
- Tous les N sessions → `[INTENT:improve-template]` → agent `template-improver`
- `auto-learn.py` extrait les handoffs JSON des agents → sections structurées dans `learning.md`

---

## Génération

`scripts/gen.py` lit le manifest et génère :

| Fichier | Ce qui est généré |
|---------|-------------------|
| `.claude/settings.local.json` | Permissions Bash adaptées au stack (31 langages, 8 package managers, monorepos, serverless, data, desktop) |
| `.claude/hooks/session-start.sh` | Contexte complet : manifest + git + learning.md + 7 signaux opérationnels |
| `.claude/hooks/user-prompt-submit.sh` | Intent classification (15 intents) + injection detection |
| `.claude/hooks/pre-bash-guard.sh` | Blocage commandes destructives |
| `.claude/hooks/post-edit.sh` | Guards qualité selon manifest.guards |
| `.claude/hooks/stop.sh` | Rappel learning.md + log self-improve async |
| `.mcp.json` | Serveurs MCP configurés |

---

## Réseau d'agents

Tous les agents suivent un contrat strict : rôle unique, périmètre d'écriture limité, **contrat de sortie structuré avec HANDOFF JSON** pour passage de contexte entre agents. Chaque agent a une section **SPÉCIALISATIONS PAR TYPE DE PROJET** (web-app, api, mobile, library, data, ml, iac).

| Agent | Rôle | Écrit |
|-------|------|-------|
| `architect` | Conception + ADR + trade-offs | learning.md uniquement |
| `reviewer` | Code review (BLOCKER/WARNING/SUGGESTION) | Rien (findings only) |
| `tester` | Tests exhaustifs + edge cases | Fichiers de test |
| `security-auditor` | OWASP + deps + secrets + config | Rien (findings only) |
| `debug-detective` | Root cause + 5 whys + git bisect | Rien (findings only) |
| `deployer` | Déploiement + rollback | Tags git, logs |
| `explorer` | Cartographie codebase | Rien |
| `doc-writer` | Docstrings + README + API docs | Fichiers .md + docstrings |
| `performance-analyst` | Profiling + optimisation | Rien (propositions) |
| `release-manager` | Orchestration release + changelog | CHANGELOG, versions |
| `data-engineer` | Pipelines data, dbt, Airflow, streaming | dbt models, DAGs, scripts |
| `ml-engineer` | MLOps : framing → train → serve → monitor | Scripts training, serving, monitoring |
| `devops-engineer` | Infra, CI/CD, observabilité, résilience | Dockerfile, CI, IaC |
| `template-improver` | **Améliore le template lui-même** | Fichiers template uniquement |

---

## Workflows complets

| Workflow | Intent | Agents impliqués |
|----------|--------|-----------------|
| `feature.md` | `feature` | architect → tester → reviewer → doc-writer |
| `bugfix.md` | `bugfix` | debug-detective → tester → reviewer |
| `hotfix.md` | `hotfix` | debug-detective → reviewer (express) → deployer |
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

## Self-improvement

Le template s'améliore automatiquement au fil des sessions :

```
Session → stop.sh → self-improve.py --log (observation)
                           ↓
                  .template/improvements.log (JSONL)
                           ↓ (tous les N sessions)
              [INTENT:improve-template] détecté
                           ↓
                  template-improver agent
                           ↓
         Analyse → classifie → matrice confiance/risque
                           ↓
    AUTO: appliqué direct | APPROVAL: diff proposé | PR: branche créée
                           ↓
              version-bump.py → version.json
```

Types d'observations loggées :
- `hook_friction` — hook a bloqué quelque chose de légitime
- `agent_gap` — tâche sans agent correspondant
- `workflow_gap` — séquence répétée sans workflow dédié
- `manifest_gap` — config désirée non supportée par le schema
- `detection_miss` — stack non détecté lors du setup
- `permission_error` — commande bloquée illégitimement
- `user_correction` — l'utilisateur a corrigé une sortie d'agent
- `user_validation` — l'utilisateur a validé une approche non-évidente

### Auto-learn

`scripts/auto-learn.py` extrait les blocs HANDOFF JSON des agents et les persiste dans `learning.md` :
- Décisions d'architecture (ADR) depuis `architect`
- Findings récurrents depuis `reviewer` et `security-auditor`
- Patterns de performance depuis `performance-analyst`
- Métriques ML depuis `ml-engineer`

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

## Stacks supportés

**Langages (31) :** Python, TypeScript, JavaScript, Go, Rust, Ruby, PHP, Java, Elixir, Swift, Kotlin, C, C++, C#/.NET, F#, Dart/Flutter, Scala, Clojure, Groovy, R, Bash, Lua, Perl, Haskell, Nim, Zig, OCaml

**Frameworks web :** Django, FastAPI, Flask, Celery, React, React Native, Expo, Next.js, Vue, Nuxt, Angular, Svelte, Remix, Astro, NestJS, Fastify, Express, Laravel, Symfony, Spring Boot, Quarkus

**Data/ML :** PyTorch, TensorFlow, JAX, scikit-learn, XGBoost, LightGBM, Hugging Face Transformers, LangChain, LlamaIndex, OpenAI SDK, Anthropic SDK, MLflow, W&B, DVC, BentoML, FAISS, Chroma, Qdrant, dbt, Airflow, Prefect, Dagster, Spark, Ray, Kafka

**Mobile/Desktop :** Flutter, Electron, Tauri, iOS (Swift/Podfile), Android (Kotlin/Gradle)

**Infra :** Docker, Kubernetes, Terraform, Ansible, Vercel, Railway, AWS, GCloud, Azure, Serverless Framework, AWS SAM/CDK, Firebase, Cloudflare Workers, Netlify

**Bases de données :** PostgreSQL, MySQL, Redis, MongoDB, SQLite, Elasticsearch, Cassandra, DynamoDB, BigQuery, Snowflake, ClickHouse, Neo4j, Pinecone

**Package managers :** npm, pnpm, yarn, bun, deno, pip, uv, poetry, conda, cargo, nix

**Monorepos :** Turborepo, Nx, Lerna, Bazel, Buck, Pants

---

## 4 couches de sécurité indépendantes

1. **Whitelist de permissions** — `settings.local.json` : seules les commandes nécessaires au stack sont autorisées
2. **Pre-tool gate** — `pre-bash-guard.sh` : bloque les commandes destructives avant exécution
3. **Post-edit quality guards** — `post-edit.sh` : lint, type-check, scan de secrets après chaque fichier édité
4. **Prompt injection detection** — `user-prompt-submit.sh` : détecte et bloque les tentatives de manipulation

---

## Portabilité

Tous les hooks utilisent `$BASH_SOURCE` pour se localiser :
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
```

Les chemins dans `settings.local.json` sont relatifs à la racine du projet (Claude Code exécute les hooks depuis là).

**Le template fonctionne depuis n'importe quel emplacement, sans configuration.**
