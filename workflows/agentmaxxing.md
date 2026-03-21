# Workflow: Agentmaxxing — Orchestration Maximale d'Agents Parallèles

## DÉCLENCHEUR
Intent classifié comme `agentmaxxing` par le hook UserPromptSubmit.
Commande directe : "lance en parallèle", "plusieurs agents", "swarm", "batch refactor", "agentmaxxing".

## CONCEPT
Shift de "writer" à "reviewer" : au lieu de tout implémenter soi-même, décomposer la tâche, spawner des agents workers, et valider leurs outputs. Le temps de traitement est divisé par N — le coût en tokens est multiplié par N.

**Règle d'or :** agentmaxxing ne vaut que si les sous-tâches sont réellement indépendantes. Des dépendances circulaires créent des merge conflicts coûteux.

---

## ÉTAPE 1 — Évaluer si le parallélisme est justifié

Avant de spawner quoi que ce soit, répondre à ces questions :

| Critère | Parallélisme justifié | Séquentiel préférable |
|---------|----------------------|----------------------|
| Taille de la tâche | > 5 fichiers à modifier | 1-3 fichiers |
| Indépendance | Tâches sans dépendances croisées | Tâche A dépend du résultat de B |
| Homogénéité | Même pattern répété N fois | Logique complexe et unique |
| Deadline | Vitesse prioritaire sur le coût | Coût prioritaire sur la vitesse |

Si parallélisme non justifié → router vers le workflow standard (feature, refactor, etc.).

---

## ÉTAPE 2 — Décomposition (Architect)

Invoquer l'agent `architect` pour découper la tâche en N sous-tâches atomiques.

Chaque sous-tâche doit avoir :
- Un **scope clair** : quels fichiers, quelles fonctions
- Des **interfaces définies** : ce qu'elle reçoit et ce qu'elle produit
- Une **vérification autonome** : comment savoir qu'elle est terminée

Exemple de décomposition pour "migrate all API calls to v2" :
```
sous-tâche 1 : migrer src/users/   → remplacer /api/v1/users  par /api/v2/users
sous-tâche 2 : migrer src/orders/  → remplacer /api/v1/orders par /api/v2/orders
sous-tâche 3 : migrer src/billing/ → remplacer /api/v1/billing par /api/v2/billing
sous-tâche 4 : mettre à jour les tests
```

---

## Pattern 1 — Native Agent Teams (recommandé si disponible)

Nécessite : `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude  # lancer Claude Code normalement
```

Ensuite dans la session Claude Code :
- Utiliser le **TeammateTool** pour spawner des agents teammates
- Pattern Lead/Teammates : 1 orchestrateur + N workers
- Le lead maintient une task list partagée et collecte les résultats
- Chaque teammate a son propre context window isolé

**Avantages :**
- Coordination native entre agents
- Communication directe sans setup manuel
- Pas de gestion de branches ou tmux

**Limites :**
- Coût linéaire : N agents = N context windows
- Overhead de coordination non négligeable
- Feature en rollout progressif — peut ne pas être disponible

---

## Pattern 2 — Worktrees + tmux (sans Agent Teams)

Pour N sous-tâches identifiées à l'étape 2.

### Créer les worktrees isolés
```bash
for n in $(seq 1 N); do
  git worktree add .worktrees/task-$n -b feat/agent-task-$n
done
git worktree list  # vérifier
```

### Spawner les sessions tmux
```bash
tmux new-session -d -s agentmaxxing

for n in $(seq 1 N); do
  tmux new-window -t agentmaxxing -n "agent-$n" \
    "cd .worktrees/task-$n && claude --no-mcp 'Ta tâche : [description tâche $n]. Scope : [fichiers]. Interface : [inputs/outputs]. Quand terminé : crée un fichier DONE.md avec un résumé.'"
done

# Afficher toutes les fenêtres
tmux attach -t agentmaxxing
```

### Monitoring de la progression
```bash
# Vérifier quels agents ont terminé
for n in $(seq 1 N); do
  if [ -f .worktrees/task-$n/DONE.md ]; then
    echo "Agent $n : DONE"
    cat .worktrees/task-$n/DONE.md
  else
    echo "Agent $n : en cours..."
  fi
done

# Voir les commits de chaque agent
git worktree list
for n in $(seq 1 N); do
  echo "=== Task $n ==="
  git -C .worktrees/task-$n log --oneline -3
done
```

---

## Pattern 3 — /batch (refactors répétitifs)

Pour les migrations mécaniques identiques sur N fichiers/modules.

```
/batch migrate all API calls from v1 to v2 in src/
/batch add error handling to all functions in lib/
/batch convert all callbacks to async/await in services/
```

**Comportement :** Claude Code crée 5-30 sous-tâches, les exécute en parallèle via des subagents, et peut créer des PRs automatiquement par groupe.

**Avantages :** zéro setup, gestion automatique, logs dans SubagentStop hook.
**Limites :** moins de contrôle sur le scope exact par tâche.

---

## ÉTAPE 3 — Limites pratiques

| Ressource | Limite recommandée |
|-----------|-------------------|
| Agents simultanés (laptop) | 5-7 max |
| Agents simultanés (serveur dédié) | 10-15 max |
| Rate limits API | Surveiller les 429 — augmenter l'intervalle entre spawns si besoin |
| Merge conflicts | Croissent exponentiellement avec N — décomposer finement |
| Coût tokens | Prévoir N × coût_tâche_individuelle × 1.2 (overhead coordination) |

**Signaux d'alerte :**
- Plus de 3 conflits de merge au merge → décomposition trop grossière
- Un agent tourne depuis > 2x le temps estimé → probablement bloqué, investiguer
- Rate limit 429 fréquent → réduire N ou espacer les spawns

---

## ÉTAPE 4 — Merge strategy

Quand tous les agents ont terminé (tous les DONE.md présents) :

### Merge séquentiel recommandé
```bash
# Merger dans l'ordre de dépendance (indépendants en premier)
git merge feat/agent-task-1 --squash -m "feat: task-1 [résumé de DONE.md]"
git merge feat/agent-task-2 --squash -m "feat: task-2 [résumé de DONE.md]"
# ... etc
```

### En cas de conflits
```bash
# Invoquer le reviewer pour chaque conflit
# git diff --diff-filter=U  → lister les fichiers en conflit
```
Invoquer l'agent `reviewer` avec le diff des fichiers en conflit.

### Validation finale
```bash
# Lancer les tests sur le résultat mergé
# Invoquer tester si le projet a une suite de tests
```
Invoquer l'agent `tester` sur le résultat final.

---

## ÉTAPE 5 — Nettoyage

```bash
# Supprimer les worktrees
git worktree remove .worktrees/task-$n --force  # répéter pour chaque n
git worktree prune

# Supprimer les branches d'agents
git branch -d feat/agent-task-{1..N}

# Fermer tmux si utilisé
tmux kill-session -t agentmaxxing
```

---

## CONTRAT DE SORTIE

```
PATTERN USED: agent-teams | worktrees-tmux | batch
AGENTS SPAWNED: N
TASKS COMPLETED: N/N
MERGE CONFLICTS: N (N resolved)
TESTS: PASS / FAIL

ARTIFACTS:
  [liste des fichiers modifiés]

COST ESTIMATE: ~N × [coût unitaire] tokens

NEXT_ACTION: [review PR | deploy | none]
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "pattern": "agent-teams|worktrees-tmux|batch",
  "agents_spawned": 0,
  "tasks_completed": 0,
  "tasks_total": 0,
  "merge_conflicts": 0,
  "tests_pass": true,
  "artifacts": [],
  "branches_merged": [],
  "status": "completed|partial|failed"
}
```
