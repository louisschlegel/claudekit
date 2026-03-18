# Workflow: Onboarding

## DÉCLENCHEUR
Intent classifié comme `onboard` par le hook UserPromptSubmit.
Session start avec manifest vide (`project.manifest.json` = `{}`).
Commande directe : "setup", "initialise le projet", "configure le template".

## AGENTS IMPLIQUÉS
1. **Explorer** — cartographie du codebase existant (si legacy)
2. **Architect** — recommandations d'architecture (si demandé)
3. **Doc Writer** — génération de `learning.md` initial

---

## CAS 1 : Nouveau projet (manifest vide, pas de code existant)

### Étape 1 — Interview de setup

Poser les 15 questions du manifest (voir CLAUDE.md section "SETUP INTERVIEW").
Collecter les réponses et générer `project.manifest.json`.

### Étape 2 — Générer la configuration

```bash
python3 scripts/gen.py
```

Cela génère :
- `.claude/settings.local.json` — permissions + hooks complets
- `.claude/hooks/session-start.sh` — contexte complet
- `.claude/hooks/pre-bash-guard.sh` — sécurité
- `.claude/hooks/post-edit.sh` — qualité
- `.claude/hooks/stop.sh` — observation
- `.mcp.json` — serveurs MCP configurés

### Étape 3 — Initialiser la structure

```bash
# learning.md depuis le template
cp learning.md.template learning.md
# Remplir la section Architecture avec les décisions initiales

# CHANGELOG.md
echo "# Changelog\n\n## [Unreleased]\n" > CHANGELOG.md

# .env.example
# Créer selon les besoins du projet
```

### Étape 4 — Premier commit

```bash
git init  # si pas déjà fait
git add .claude/ project.manifest.json learning.md CHANGELOG.md
git commit -m "chore: initialize project with template vX.Y.Z"
```

---

## CAS 2 : Projet legacy (code existant, manifest vide)

### Étape 1 — Exploration automatique

Le hook `session-start.sh` a déjà détecté le stack.
Invoquer `explorer` pour une cartographie complète :
```
Scope : répertoire racine complet
Profondeur : 3 niveaux
Output : architecture overview
```

### Étape 2 — Compléter le manifest

Sur la base du rapport de l'explorer :
- Pré-remplir `project.manifest.json` avec le stack détecté
- Demander confirmation/correction des données inférées
- Compléter les champs manquants (workflow, security, etc.)

### Étape 3 — Générer la configuration (identique CAS 1)

```bash
python3 scripts/gen.py
```

### Étape 4 — Audit initial

Invoquer `security-auditor` sur le scope complet pour identifier les dettes de sécurité existantes.

Résultat → section "Bugs" de `learning.md` avec label "[LEGACY DEBT]".

### Étape 5 — Documenter l'existant

Invoquer `doc-writer` pour générer une `learning.md` initiale :
- Section Architecture : basée sur le rapport de l'explorer
- Section Stack/Config : dépendances et versions
- Section Bugs : findings de l'audit sécurité

---

## CONTRAT DE SORTIE

```
ONBOARDING: [nom du projet]
MODE: new / legacy
DATE: YYYY-MM-DD

GENERATED:
  ✓ project.manifest.json
  ✓ .claude/settings.local.json
  ✓ .claude/hooks/ (4 hooks)
  ✓ .mcp.json
  ✓ learning.md
  ✓ CHANGELOG.md

STACK DETECTED: [technologies]
MCP SERVERS: [liste]
SECURITY DEBT: N findings (legacy) / clean (new)

NEXT STEPS:
  1. [action recommandée]
  2. [action recommandée]
```
