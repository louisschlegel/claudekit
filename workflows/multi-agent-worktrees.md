# Workflow: Multi-Agent Worktrees

## Quand utiliser
- Feature complexe décomposable en sous-tâches indépendantes
- Tests à exécuter en parallèle
- Review + implémentation simultanée

## Prérequis
- Git repo propre (pas de modifications non commitées)
- Claude Code 2.0+ (TeammateTool supporté)

---

## Mode 1 — Agent Teams (natif, recommandé)

Nécessite : `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

1. Activer : `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
2. Lancer Claude Code normalement
3. Utiliser le TeammateTool ou `--teammate-mode` pour spawner des agents
4. Le "team lead" coordonne via une task list partagée
5. Chaque "teammate" a son propre context window

**Avantages** : coordination native, communication directe entre agents, pas de setup manuel
**Limites** : coût linéaire (N context windows), overhead de coordination, feature en rollout progressif

---

## Mode 2 — Worktrees manuels (voir ci-dessous)

Pour les environnements sans Agent Teams ou pour un contrôle plus fin sur les branches.

## Limites pratiques (Mode 2)

| Ressource | Limite recommandée |
|-----------|-------------------|
| Agents simultanés (laptop) | 5-7 max |
| Agents simultanés (serveur) | 10-15 max |
| Merge conflicts | Croissent avec N — décomposer finement |

## Monitoring tmux

```bash
# Spawner des sessions tmux par agent
tmux new-session -d -s agents
for n in $(seq 1 N); do
  tmux new-window -t agents -n "agent-$n" \
    "cd .worktrees/task-$n && claude '[description tâche $n]'"
done
tmux attach -t agents

# Vérifier la progression
for n in $(seq 1 N); do
  echo "Agent $n: $(git -C .worktrees/task-$n log --oneline -1 2>/dev/null || echo 'pas de commit')"
done
```

---

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

## CONTRAT DE SORTIE

```
STATUS: completed
SUMMARY: [résumé des actions effectuées]
ARTIFACTS: [fichiers créés ou modifiés]
NEXT_ACTION: [prochaine étape recommandée ou none]
```
