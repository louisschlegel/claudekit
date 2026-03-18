# Template Universel Claude Code — v2.0

> Ce fichier est l'**orchestrateur** du système. Il lit le contexte injecté par les hooks, route les demandes vers les bons agents et workflows, et supervise l'auto-amélioration du template.

---

## 🚀 PREMIER DÉMARRAGE

Si `project.manifest.json` est vide (`{}`) → **lance le setup** (section SETUP ci-dessous).
Si rempli → lis le contexte injecté par le hook `session-start` et commence à orchestrer.

---

## 🔍 DÉTECTION AUTOMATIQUE (projets legacy)

Avant les questions, le hook scanne automatiquement :
```
# Langages
package.json, requirements.txt, pyproject.toml, go.mod, Cargo.toml, Gemfile,
pubspec.yaml (Flutter), build.gradle (Android/Java), pom.xml (Maven), build.sbt (Scala),
mix.exs (Elixir), composer.json (PHP), *.csproj (C#/.NET), CMakeLists.txt (C/C++),
Podfile (iOS), Package.swift (SPM), deps.edn (Clojure), build.zig (Zig)

# Monorepos
turbo.json, nx.json, lerna.json, pnpm-workspace.yaml

# Cloud / Infra
serverless.yml (AWS Lambda), firebase.json, wrangler.toml (Cloudflare Workers),
netlify.toml, *.tf (Terraform), ansible.cfg, .gitlab-ci.yml, Jenkinsfile

# Desktop / Data
electron-builder.yml, tauri.conf.json, dbt_project.yml, *.ipynb (Jupyter)
```
Présente les détections et confirme avant d'écrire le manifest.

---

## 🎯 SETUP INTERVIEW

Questions **une par une** :

**Bloc 1 — Identité**
1. Nom du projet (sans espaces)
2. Description en 1-2 phrases
3. Langue commits/comments (fr/en)

**Bloc 2 — Stack**
4. Langages (Python, TypeScript, Go, Rust, Ruby, Java...)
5. Frameworks (FastAPI, Django, React, React Native, Next.js, Express...)
6. Bases de données (PostgreSQL, MySQL, MongoDB, Redis, SQLite...)
7. Infrastructure (Docker, Kubernetes, Vercel, Railway, AWS...)
8. Tests (pytest, jest, vitest, rspec, go test...)

**Bloc 3 — Workflow**
9. Stratégie git (feature-branch / trunk-based / gitflow)
10. CI/CD (GitHub Actions, GitLab CI, aucun...)
11. Cible de déploiement
12. Déploiement auto sur release ? (oui/non)

**Bloc 4 — Automatisations Claude**
13. MCP servers : `filesystem`, `github`, `postgres`, `sqlite`, `brave-search`, `slack`, `linear`, `notion`, `playwright`, `desktop-commander`
    *(gmail, google-calendar, canva = intégrations natives Claude.ai, pas de config nécessaire)*
14. Guards : lint ? type-check ? test auto ? migrations ? i18n ?
15. Workflows à activer : `feature`, `bugfix`, `hotfix`, `release`, `security-audit`, `dependency-update`, `refactor`, `onboard`, `self-improve`, `db-migration`, `incident-response`, `performance-baseline`, `publish-package`, `api-design`, `a-b-test`, `data-quality`, `llm-eval`, `spec-to-project`
16. Agents à activer : `architect`, `reviewer`, `tester`, `deployer`, `explorer`, `security-auditor`, `debug-detective`, `doc-writer`, `performance-analyst`, `release-manager`, `data-engineer`, `ml-engineer`, `devops-engineer`, `cost-analyst`, `spec-reader`, `template-improver`
17. Type de projet (pour personnalisation) : `web-app`, `api`, `mobile`, `desktop`, `data-pipeline`, `ml`, `library`, `monorepo`, `iac`, `cli`
18. Auto-amélioration : toutes les N sessions ? (défaut: 10)
19. Fichier de mémoire (défaut: `learning.md`)

**Après le setup :**
1. Écrire `project.manifest.json` complet
2. `python3 scripts/gen.py`
3. Créer `learning.md` depuis `learning.md.template`
4. Initialiser `.template/version.json`
5. Confirmer et demander de redémarrer Claude Code

---

## 🧭 ORCHESTRATEUR — ROUTING

Le hook `user-prompt-submit.sh` classifie l'intention et l'injecte en contexte.
**Lis la classification et route immédiatement.**

| Intention détectée | Action |
|-------------------|--------|
| `hotfix` | → `workflows/hotfix.md` |
| `incident` | → `workflows/incident-response.md` |
| `db-migration` | → `workflows/db-migration.md` |
| `perf-test` | → `workflows/performance-baseline.md` |
| `publish` | → `workflows/publish-package.md` |
| `api-design` | → `workflows/api-design.md` |
| `feature` | → `workflows/feature.md` |
| `bugfix` | → `workflows/bugfix.md` |
| `release` | → `workflows/release.md` |
| `security-audit` | → `workflows/security-audit.md` |
| `update-deps` | → `workflows/dependency-update.md` |
| `refactor` | → `workflows/refactor.md` |
| `onboard` | → `workflows/onboarding.md` |
| `improve-template` | → `workflows/self-improve.md` |
| `ab-test` | → `workflows/a-b-test.md` |
| `data-quality` | → `workflows/data-quality.md` |
| `llm-eval` | → `workflows/llm-eval.md` |
| `spec-to-project` | → `workflows/spec-to-project.md` |
| `question` | → réponse directe, pas de workflow |
| `other` | → demande de clarification, puis route |

**Pour invoquer un agent :** lis son fichier dans `.claude/agents/[nom].md`, puis utilise le tool `Agent` avec son contenu comme instructions. Passe toujours le contexte du manifest et le résultat du handoff précédent.

**Pour exécuter un workflow :** lis `workflows/[nom].md` et suis les étapes dans l'ordre. Respecte les gates — si une gate échoue, boucle ou escalade.

---

## 🔄 MISE À JOUR DU TEMPLATE

Quand l'utilisateur dit "mets-toi à jour", "update template", "améliore le template" :
→ Exécuter `workflows/self-improve.md`

Ou directement : `python3 scripts/gen.py` pour régénérer la config.

---

## 📖 PROTOCOLE DE SESSION

**Début de session :**
1. Le hook injecte le contexte (manifest + git + learning.md + version template)
2. Si le hook indique une amélioration en attente → exécuter `workflows/self-improve.md` avant tout
3. Si le hook classifie une intention → router immédiatement
4. Sinon → attendre la demande

**Fin de session :**
- Le hook `stop.sh` lance `scripts/self-improve.py` en async
- Pense à mettre à jour `learning.md` si des patterns importants ont été découverts

---

## 🤖 AGENTS DISPONIBLES

Définis dans `.claude/agents/`. Lis le fichier correspondant avant d'invoquer.

| Agent | Fichier | Spécialité |
|-------|---------|------------|
| `architect` | `.claude/agents/architect.md` | Design, patterns, trade-offs |
| `reviewer` | `.claude/agents/reviewer.md` | Code review, bugs, sécurité |
| `tester` | `.claude/agents/tester.md` | Tests exhaustifs |
| `deployer` | `.claude/agents/deployer.md` | Déploiement, rollback |
| `explorer` | `.claude/agents/explorer.md` | Cartographie codebase |
| `security-auditor` | `.claude/agents/security-auditor.md` | Vulnérabilités, secrets |
| `debug-detective` | `.claude/agents/debug-detective.md` | Root cause analysis |
| `doc-writer` | `.claude/agents/doc-writer.md` | Documentation |
| `performance-analyst` | `.claude/agents/performance-analyst.md` | Performances |
| `release-manager` | `.claude/agents/release-manager.md` | Versioning, changelog |
| `data-engineer` | `.claude/agents/data-engineer.md` | Pipelines data, dbt, Airflow |
| `ml-engineer` | `.claude/agents/ml-engineer.md` | Training, MLOps, serving, LLMs |
| `devops-engineer` | `.claude/agents/devops-engineer.md` | CI/CD, IaC, monitoring |
| `cost-analyst` | `.claude/agents/cost-analyst.md` | Optimisation coûts cloud + LLM |
| `spec-reader` | `.claude/agents/spec-reader.md` | Parse cahier des charges → manifest + backlog |
| `template-improver` | `.claude/agents/template-improver.md` | Auto-amélioration template |

---

## 🛡️ COUCHES DE SÉCURITÉ

Le système a 4 couches de défense indépendantes :

1. **Whitelist de permissions** — `settings.local.json` : seules les commandes nécessaires au stack sont autorisées
2. **Pre-tool gate** — `pre-bash-guard.sh` : bloque les commandes destructives avant exécution
3. **Post-edit quality guards** — `post-edit.sh` : lint, type-check, scan de secrets après chaque fichier édité
4. **Prompt injection detection** — `user-prompt-submit.sh` : détecte les tentatives de manipulation

**Fichiers protégés** (tout agent qui veut les modifier doit avoir une confirmation explicite) :
- `.claude/settings.local.json`
- `scripts/gen.py`
- `.template/version.json`

---

## 📏 RÈGLES DE BASE

Ces règles s'appliquent **toujours**, aucun agent ne peut les override.

### Code
- Lire avant de modifier
- Solution minimale correcte — pas d'over-engineering
- Pas de commentaires sur du code évident
- Ne pas créer de fichiers si un existant peut être modifié

### Git
- `git status` + `git diff` avant tout commit
- Messages de commit selon `workflow.commit_language` du manifest
- Jamais `git push --force` sans confirmation explicite

### Sécurité
- Jamais committer `.env`, credentials, tokens, clés privées
- Valider les inputs aux frontières système uniquement
- Pas de `eval()`, injection de commandes, XSS, SQL injection

### Communication
- Réponses courtes et directes
- Pas de récap après chaque action — l'utilisateur voit le diff
- Questions précises plutôt que suppositions

---

## 📦 LEGACY PROJECT SETUP

```bash
cd mon-projet-existant/
cp -r ~/Desktop/template/.claude/ ./.claude/
mkdir -p scripts workflows .template
cp ~/Desktop/template/scripts/gen.py ./scripts/gen.py
cp ~/Desktop/template/scripts/self-improve.py ./scripts/self-improve.py
cp ~/Desktop/template/scripts/version-bump.py ./scripts/version-bump.py
cp ~/Desktop/template/scripts/changelog-gen.py ./scripts/changelog-gen.py
cp ~/Desktop/template/scripts/auto-learn.py ./scripts/auto-learn.py
cp -r ~/Desktop/template/.claude/agents/ ./.claude/agents/
cp -r ~/Desktop/template/workflows/ ./workflows/
cp ~/Desktop/template/CLAUDE.md ./CLAUDE.md
echo '{}' > project.manifest.json
claude
```

---

## 📁 STRUCTURE

```
project/
├── CLAUDE.md                      ← Orchestrateur (ce fichier)
├── project.manifest.json          ← Config
├── learning.md                    ← Mémoire institutionnelle
├── CHANGELOG.md                   ← Auto-généré par release-manager
├── .mcp.json                      ← Généré par gen.py
├── .gitignore
├── .claude/
│   ├── settings.local.json        ← Permissions + hooks (généré)
│   ├── hooks/                     ← Scripts hooks (générés + bootstrap)
│   └── agents/                    ← Définitions des agents spécialisés
├── workflows/                     ← Pipelines end-to-end
├── scripts/                       ← gen.py, self-improve.py, etc.
└── .template/                     ← Métadonnées du template (gitignore sauf version.json)
    ├── version.json               ← Version + historique améliorations
    ├── improvements.log           ← Observations sessions (JSONL, append-only)
    └── known-patterns.json        ← Patterns en cours de validation
```
