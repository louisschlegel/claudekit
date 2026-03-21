---
name: overnight
description: Launch a long-running autonomous task — Claude works while you sleep, with verification loops and safe commits
effort: high
user-invocable: true
triggers:
  - "overnight"
  - "travaille cette nuit"
  - "work overnight"
  - "lance ça et je reviens demain"
  - "boucle de travail"
  - "run all night"
---

# Skill: /overnight

Lance une tâche longue en autonomie — Claude travaille pendant que tu dors.

## Protocole

### 1. Définir la tâche clairement
```
Migre tous les composants React class vers des hooks fonctionnels.
Critères : tous les tests passent, lint OK, pas de régressions visuelles.
```

### 2. Configurer l'autonomie
```bash
# Option A : sandbox (recommandé)
claude --permission-mode acceptEdits

# Option B : full bypass (en sandbox uniquement)
claude --dangerously-skip-permissions
```

### 3. Instruction de boucle
```
Pour chaque fichier à migrer :
1. Lis le fichier et comprends la logique
2. Réécris avec hooks (useState, useEffect, etc.)
3. Lance les tests associés
4. Si tests passent → commit et passe au suivant
5. Si tests échouent → tente 2 corrections maximum
6. Si toujours en échec → skip, note dans SKIP_LOG.md, passe au suivant

Après chaque batch de 5 fichiers, fais un récap dans PROGRESS.md.
Quand tout est fini, écris un résumé final dans OVERNIGHT_REPORT.md.
```

### 4. Monitoring à distance
- `claude --resume` pour voir la session
- `git log --oneline -20` pour voir l'avancement
- `cat PROGRESS.md` pour le récap

### 5. Au retour
1. `git log --oneline` — voir les commits
2. `cat OVERNIGHT_REPORT.md` — lire le rapport
3. `cat SKIP_LOG.md` — voir ce qui a été skippé
4. `npm test` ou `pytest` — vérifier que tout passe

## Tâches idéales pour overnight

- Migrations de code (React class → hooks, Python 2 → 3, etc.)
- Ajout de tests sur du code non testé
- Refactoring de fichiers un par un
- Documentation de toutes les fonctions publiques
- Conversion de CSS en Tailwind
- i18n : extraction de toutes les strings hardcodées

## Tâches à NE PAS lancer overnight

- Changements d'architecture (besoin de décisions humaines)
- Déploiement en production
- Modifications de la base de données
- Anything that touches user data

## Complémentaire avec

- `/execute-plan` — pour des tâches avec checkpoints
- `/loop 10m pytest` — monitoring continu
- Agent teams — pour paralléliser le travail overnight
