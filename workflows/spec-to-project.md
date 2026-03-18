# Workflow: Spec to Project

**Déclenché par :** `[INTENT:spec-to-project]` — mots-clés : "cahier des charges", "spec", "PRD", "brief", "voici les specs", "j'ai un document", "analyse ce document", "génère le projet depuis", "setup depuis spec"

**Agents impliqués :** spec-reader → architect → doc-writer

---

## Vue d'ensemble

```
Document de spec
      ↓
  [spec-reader] — Extraction structurée
      ↓
  Manifest + Learning.md + Backlog
      ↓
  gen.py — Génération config complète
      ↓
  [architect] — Proposition architecture initiale
      ↓
  [doc-writer] — README projet + ADR initial
      ↓
  GitHub setup — Issues + Milestones + Labels
      ↓
  Projet prêt à développer
```

---

## Étape 1 — Réception et validation du document

```
VÉRIFICATIONS PRÉALABLES :
□ Le contenu de la spec est-il fourni ? (texte, path, ou URL)
□ La spec est-elle suffisamment complète pour inférer un stack ? (> 200 mots)
□ La langue principale est-elle identifiable ?

SI spec trop courte (< 200 mots) :
→ Demander à l'utilisateur de compléter avec :
  - Technologies envisagées (ou contraintes)
  - Type d'utilisateurs
  - Fonctionnalités principales (3-5)
  - Deadline approximative

SI spec sous forme de fichier :
→ Lire le fichier avec Read tool
→ Si PDF : demander à l'utilisateur de le convertir en texte (pdftotext ou copier-coller)
```

**Exemples de formats acceptés :**
```
# Format 1 — Texte direct dans le chat
"Voici mon cahier des charges : [...]"

# Format 2 — Fichier Markdown
Read("docs/specs.md") ou Read("PRD.md")

# Format 3 — Notion export
Read("notion-export.md")

# Format 4 — Fichier texte converti depuis PDF
Read("cahier-des-charges.txt")
```

---

## Étape 2 — Analyse par l'agent spec-reader

**Invoquer l'agent spec-reader** avec le contenu intégral de la spec.

L'agent produit :
1. **Identité extraite** — nom, type, domaine, description
2. **Stack inféré** — langages, frameworks, databases, infra
3. **Features structurées** — P0/P1/P2 avec acceptance criteria
4. **NFRs extraits** — performance, sécurité, compliance
5. **Intégrations détectées** — services tiers
6. **Gaps identifiés** — informations manquantes
7. **HANDOFF JSON** — données structurées pour la suite

```
⚠️ GATE : Confiance de l'extraction ?
- HIGH → continuer
- MEDIUM → afficher les ambiguïtés, demander confirmation sur les points clés
- LOW → poser 3-5 questions ciblées pour combler les gaps avant de continuer
```

---

## Étape 3 — Présentation et validation avec l'utilisateur

Présenter un récapitulatif clair avant toute écriture :

```markdown
## Voici ce que j'ai extrait de ta spec

**Projet :** {name} ({type})
**Domaine :** {domain}
**Stack :** {languages} + {frameworks} + {databases}
**Deploy :** {deploy_target}

### Features MVP (P0) — {N} features
- [F-001] {title} (complexité: {S/M/L/XL})
- [F-002] {title}
- ...

### Features v1.1 (P1) — {N} features
- [F-00X] {title}
- ...

### Intégrations
- {name} ({type}, priorité: {P0/P1/P2})

### Contraintes
- Performance : {SLA ou "non spécifié"}
- Compliance : {liste ou "aucune"}
- Deadline : {date ou "non mentionnée"}

### Points à clarifier
- {ambiguité 1}
- {ambiguité 2}

---
Est-ce correct ? Modifications à apporter avant que je génère tout ?
```

**Attendre confirmation** ou corrections de l'utilisateur.

---

## Étape 4 — Génération du manifest

Écrire `project.manifest.json` complet depuis le HANDOFF JSON de spec-reader :

```python
# Exemple de manifest généré
{
  "project": {
    "name": "mon-saas",
    "description": "Plateforme SaaS de gestion RH multi-tenant",
    "type": "web-app",
    "language": "fr"
  },
  "stack": {
    "languages": ["typescript", "python"],
    "frameworks": ["next", "fastapi"],
    "databases": ["postgresql", "redis"],
    "runtime": "node",
    "testing": ["jest", "pytest"],
    "linting": ["eslint", "ruff"],
    "package_managers": ["npm", "pip"],
    "monorepo_tools": [],
    "data_tools": [],
    "serverless": [],
    "desktop_frameworks": []
  },
  "workflow": {
    "git_strategy": "feature-branch",
    "ci_cd": "github-actions",
    "deploy_target": "vercel",
    "auto_deploy": false,
    "commit_language": "fr",
    "environments": ["dev", "staging", "prod"],
    "health_check_url": "",
    "smoke_tests": [],
    "github_releases": true
  },
  "mcp_servers": ["github", "postgres"],
  "guards": {
    "lint": true,
    "type_check": true,
    "test_on_edit": false,
    "migration_check": true,
    "i18n_check": false,
    "secret_scan": true
  },
  "agents": ["architect", "reviewer", "tester", "security-auditor",
             "debug-detective", "deployer", "explorer", "doc-writer",
             "performance-analyst", "release-manager", "devops-engineer",
             "cost-analyst", "template-improver"],
  "workflows": ["feature", "bugfix", "hotfix", "release", "security-audit",
                "dependency-update", "refactor", "onboard", "self-improve",
                "db-migration", "incident-response", "api-design"],
  "automation": {
    "self_improve_every_n_sessions": 10,
    "learning_file": "learning.md"
  },
  "security": {
    "secret_scan": true,
    "dependency_audit": true,
    "owasp_check": true
  },
  "template": {
    "version": "1.1.0",
    "source": "https://github.com/louisschlegel/claudekit"
  }
}
```

---

## Étape 5 — Génération de la config Claude Code

```bash
python3 scripts/gen.py
```

Vérifier la sortie :
```
□ .claude/settings.local.json généré (permissions adaptées au stack)
□ .claude/hooks/session-start.sh mis à jour
□ .claude/hooks/user-prompt-submit.sh mis à jour (intents adaptés)
□ .mcp.json généré (serveurs MCP configurés)
```

---

## Étape 6 — Pré-remplissage de learning.md

Créer `learning.md` avec le contexte métier extrait de la spec :

```markdown
# {nom-projet} — Mémoire Institutionnelle

## Contexte Projet

**Domaine :** {domain}
**Description :** {description}
**Utilisateurs cibles :** {target_users}
**Stakeholders :** {stakeholders}
**Deadline :** {deadline ou "non définie"}

---

## Glossaire Métier

<!-- Termes spécifiques extraits de la spec -->
{glossary}

---

## Contraintes Critiques

<!-- Contraintes non-fonctionnelles P0 -->
{constraints_list}

---

## Décisions d'Architecture Initiales

<!-- Inférées depuis le stack et le type de projet -->
### Stack choisi
- **Frontend :** {framework_front} — {raison}
- **Backend :** {framework_back} — {raison}
- **Database :** {database} — {raison}
- **Deploy :** {deploy_target} — {raison}

---

## Features MVP (P0)

<!-- Extraites de la spec, à compléter lors du dev -->
{features_p0_list}

---

## Intégrations Critiques

{integrations_list}

---

## Patterns et Conventions

<!-- À remplir au fil du développement -->

---

## Bugs Récurrents et Patterns à Éviter

<!-- À remplir au fil du développement -->
```

---

## Étape 7 — Génération du backlog structuré

Créer `backlog.md` avec le backlog complet issu de la spec :

```markdown
# Backlog — {nom-projet}

> Généré depuis le cahier des charges le {date}
> Mis à jour manuellement au fil des itérations

## Légende
- 🔴 P0 — MVP obligatoire
- 🟡 P1 — v1.1, important
- 🔵 P2 — Backlog, nice to have
- Complexité : S (< 1j) | M (1-3j) | L (3-7j) | XL (> 1 semaine)

---

## 🔴 MVP (P0)

| ID | Feature | Complexité | Dépendances | Acceptance Criteria |
|----|---------|------------|-------------|---------------------|
| F-001 | {title} | {S/M/L/XL} | — | {criteria} |
| F-002 | {title} | {S/M/L/XL} | F-001 | {criteria} |
...

**Charge estimée MVP :** {somme des complexités}

---

## 🟡 v1.1 (P1)

| ID | Feature | Complexité | Dépendances | Notes |
|----|---------|------------|-------------|-------|
| F-0XX | {title} | {S/M/L/XL} | {deps} | {notes} |
...

---

## 🔵 Backlog (P2)

| ID | Feature | Complexité | Notes |
|----|---------|------------|-------|
| F-0XX | {title} | {S/M/L/XL} | {notes} |
...

---

## Intégrations

| Service | Type | Priorité | Doc |
|---------|------|----------|-----|
| {name} | {type} | {P0/P1/P2} | {url} |
...

---

## Questions ouvertes

<!-- Ambiguïtés détectées lors de l'analyse de la spec -->
- [ ] {question 1}
- [ ] {question 2}
```

---

## Étape 8 — Proposition d'architecture initiale

**Invoquer l'agent architect** avec :
- Le manifest généré
- Le backlog (features P0)
- Les NFRs extraits (performance, sécurité, scalabilité)

L'architecte produit :
- Diagramme de haut niveau (ASCII)
- Découpage en modules/services
- Choix de patterns (monolithique vs microservices, REST vs GraphQL, etc.)
- ADR initial (Architecture Decision Record)
- Estimation de complexité globale

```
⚠️ GATE : Complexité globale ?
- S/M → continuer directement
- L/XL → présenter l'ADR à l'utilisateur, attendre validation avant d'aller plus loin
```

---

## Étape 9 — Génération du README projet

**Invoquer l'agent doc-writer** pour générer un `README.md` projet-spécifique :

```markdown
# {nom-projet}

{description}

## Fonctionnalités

{liste des features P0 formatée pour un README}

## Stack

{stack avec badges}

## Démarrage rapide

{instructions d'installation}

## Architecture

{diagramme ASCII depuis l'architect}

## Roadmap

{lien vers backlog.md}
```

---

## Étape 10 — Setup GitHub (issues, milestones, labels)

Générer et proposer le script `scripts/setup-github.sh` :

```bash
#!/usr/bin/env bash
# setup-github.sh — Initialise le GitHub du projet depuis le backlog
# Généré par spec-reader le {date}
# Usage : bash scripts/setup-github.sh

set -e

REPO="{owner}/{repo}"  # À remplacer

echo "🏷️  Création des labels..."
gh label create "P0" --color "d73a4a" --description "Must have — MVP" --repo "$REPO" 2>/dev/null || true
gh label create "P1" --color "e4e669" --description "Should have — v1.1" --repo "$REPO" 2>/dev/null || true
gh label create "P2" --color "0075ca" --description "Nice to have — Backlog" --repo "$REPO" 2>/dev/null || true
gh label create "feature" --color "a2eeef" --repo "$REPO" 2>/dev/null || true
gh label create "auth" --color "7057ff" --repo "$REPO" 2>/dev/null || true
gh label create "data" --color "008672" --repo "$REPO" 2>/dev/null || true
gh label create "integration" --color "e6b0aa" --repo "$REPO" 2>/dev/null || true
gh label create "infra" --color "ededed" --repo "$REPO" 2>/dev/null || true

echo "🎯  Création des milestones..."
gh api repos/"$REPO"/milestones \
  --method POST \
  --field title="MVP" \
  --field description="Features P0 — {deadline_mvp}" \
  --field due_on="{deadline_mvp_iso}" 2>/dev/null || true

gh api repos/"$REPO"/milestones \
  --method POST \
  --field title="v1.1" \
  --field description="Features P1" 2>/dev/null || true

echo "📋  Création des issues P0..."
# {issues P0 générées dynamiquement par spec-reader}
{gh_issue_commands_p0}

echo "📋  Création des issues P1..."
{gh_issue_commands_p1}

echo "✅  Setup GitHub terminé !"
echo "   Voir les issues : https://github/$REPO/issues"
```

**Demander confirmation** avant d'exécuter le script (action visible publiquement).

---

## Étape 11 — Récapitulatif final et prochaines étapes

```markdown
## ✅ Projet initialisé depuis la spec

**Fichiers générés :**
- `project.manifest.json` — config claudekit
- `learning.md` — contexte métier pré-rempli
- `backlog.md` — {N} features structurées (P0/P1/P2)
- `README.md` — documentation initiale
- `.claude/settings.local.json` — permissions adaptées
- `.claude/hooks/` — 5 hooks configurés
- `.mcp.json` — MCP servers
- `scripts/setup-github.sh` — script issues GitHub

**ADR initial :** {titre de l'ADR architect}

**Prochaines étapes :**
1. ▶️ Relancer Claude Code pour que le hook session-start charge le contexte
2. 🐙 Exécuter `bash scripts/setup-github.sh` pour créer issues + milestones
3. 🚀 Commencer par la feature F-001 : "{titre F-001}"
4. 📖 Compléter les questions ouvertes dans `backlog.md`

**Gaps à adresser avant de commencer :**
{gaps_list}
```

---

## CONTRAT DE SORTIE

```
SPEC SOURCE: [titre/hash]
CONFIANCE EXTRACTION: HIGH | MEDIUM | LOW

MANIFEST: project.manifest.json (généré)
LEARNING: learning.md (pré-rempli, {N} sections)
BACKLOG: backlog.md ({N} features: {p0} P0 / {p1} P1 / {p2} P2)
README: README.md (généré)
GITHUB SETUP: scripts/setup-github.sh (prêt à exécuter)

GEN.PY: ✅ exécuté
HOOKS: ✅ configurés
MCP: ✅ configuré

GAPS RESTANTS: [liste]
PROCHAINE FEATURE: F-001 — {titre}
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "spec_source": "...",
  "confidence": "HIGH|MEDIUM|LOW",
  "manifest_generated": true,
  "gen_py_run": true,
  "project": {
    "name": "...",
    "type": "...",
    "domain": "..."
  },
  "stack_summary": "TypeScript + Next.js + FastAPI + PostgreSQL",
  "features_total": 0,
  "features_p0": 0,
  "features_p1": 0,
  "features_p2": 0,
  "next_feature": {"id": "F-001", "title": "..."},
  "gaps": ["..."],
  "files_generated": [
    "project.manifest.json",
    "learning.md",
    "backlog.md",
    "README.md",
    "scripts/setup-github.sh"
  ],
  "github_setup_pending": true
}
```
