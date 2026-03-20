# Workflow: Agent Teams

Coordination de plusieurs instances Claude Code avec tâches partagées et messaging inter-agents.

> Requiert: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

## Étapes

### 1. Planification (Lead)
- Définir l'objectif global
- Découper en tâches parallélisables
- Identifier les dépendances entre tâches
- Attribuer chaque tâche à un agent spécialisé

### 2. Configuration
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
# Modes d'affichage : in-process | tmux | auto
claude --teammate-mode tmux
```

### 3. Lancement
- Le lead lance les teammates avec des tâches spécifiques
- Chaque teammate travaille dans son propre worktree isolé
- Le lead supervise via le task board partagé

### 4. Coordination
- **Task list partagée** : pending → in-progress → completed
- **Dépendances** : les tâches dépendantes bloquent automatiquement
- **Messaging** : les agents communiquent via la mailbox
- **Plan approval** : le teammate planifie en read-only, le lead approuve

### 5. Review & Merge
- Chaque teammate crée une PR depuis son worktree
- Le lead review et merge les PRs
- Résolution des conflits si nécessaire

## Cas d'usage

| Scénario | Agents recommandés |
|----------|-------------------|
| Feature complexe | architect (plan) + 2x tester + reviewer |
| Refactoring large | explorer (map) + 3x implémentation parallèle |
| Migration | data-modeler (schema) + backend + tests |
| Security audit | security-auditor + compliance-officer + reviewer |

## HANDOFF JSON

```json
{
  "workflow": "agent-teams",
  "status": "complete|in-progress|blocked",
  "team": {
    "lead": "architect",
    "teammates": ["tester-1", "tester-2", "reviewer"],
    "mode": "tmux"
  },
  "tasks": {
    "total": 8,
    "completed": 6,
    "in_progress": 1,
    "blocked": 1
  },
  "prs_created": ["#15", "#16"],
  "next_steps": ["Merge PR #15", "Resolve conflict in PR #16"]
}
```

## CONTRAT DE SORTIE

- [ ] Toutes les tâches complétées ou bloquées documentées
- [ ] PRs créées pour chaque worktree avec changements
- [ ] Conflits identifiés et plan de résolution
- [ ] Tests passent sur chaque branche
- [ ] HANDOFF JSON produit
