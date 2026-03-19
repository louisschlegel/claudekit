# Workflow: Multi-Agent Worktrees

## Quand utiliser
- Feature complexe décomposable en sous-tâches indépendantes
- Tests à exécuter en parallèle
- Review + implémentation simultanée

## Prérequis
- Git repo propre (pas de modifications non commitées)
- Claude Code 2.0+ (TeammateTool supporté)

## Étapes

### 1. Décomposition (Architect)
Invoquer l'agent `architect` pour découper la feature en N tâches indépendantes.
Chaque tâche doit : avoir des inputs/outputs clairs, ne pas avoir de dépendances circulaires.

### 2. Création des worktrees
Pour chaque tâche :
```bash
git worktree add .worktrees/task-{n} -b feat/task-{n}
```

### 3. Spawn des agents
Utiliser le tool `Agent` pour spawner un sous-agent par worktree :
- Chaque agent reçoit : sa tâche, le chemin du worktree, les interfaces avec les autres tâches
- Instructions : "Tu travailles dans .worktrees/task-{n}. Ne modifie que les fichiers de ta tâche."

### 4. Monitoring
Le hook `SubagentStop` (si configuré) log chaque completion.
Vérifier la progression avec `git worktree list`.

### 5. Merge
Quand tous les agents ont terminé :
```bash
git worktree remove .worktrees/task-{n}
git merge feat/task-{n}
```
Résoudre les conflits si besoin avec l'agent `reviewer`.

### 6. Validation
Lancer l'agent `tester` sur le résultat mergé.

## Gates
- [ ] Toutes les tâches complétées (vérifier via `git worktree list`)
- [ ] Tests passent
- [ ] Reviewer approuve

## Nettoyage
```bash
git worktree prune
git branch -d feat/task-{1..n}
```

---

**HANDOFF JSON (pour orchestrateur) :**
```json
{"status": "completed", "summary": "", "next_action": "", "artifacts": []}
```
