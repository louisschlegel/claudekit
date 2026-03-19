# Workflow: Cost Audit

Profiler l'utilisation de tokens, identifier les patterns coûteux, optimiser le model routing.

## Étapes

### 1. Collecter les données
- Lire `.template/usage.jsonl` (historique des sessions)
- Lire `.template/agent-events.jsonl` (événements par outil)
- Calculer : tokens in/out par session, par agent, par workflow

### 2. Analyser les coûts
| Modèle | Input ($/Mtok) | Output ($/Mtok) |
|--------|----------------|-----------------|
| Haiku | $0.25 | $1.25 |
| Sonnet | $3 | $15 |
| Opus | $15 | $75 |

- Identifier les workflows les plus chers
- Identifier les agents qui consomment le plus
- Détecter les patterns coûteux :
  - Lectures de fichiers volumineux sans filtre
  - Commandes bash avec sorties verbeuses
  - Compactions fréquentes (signe de contexte mal géré)

### 3. Recommandations par ROI
- **Quick wins** : filtrer les sorties de tests (show only failures)
- **Model routing** : utiliser Haiku pour les tâches simples (grep, ls, git status)
- **Caching** : identifier les requêtes répétitives
- **Compaction** : optimiser le `/compact` focus par workflow
- **Skills over CLAUDE.md** : déplacer les instructions spécialisées vers des skills (load-on-demand)

### 4. Implémenter les optimisations
- Mettre à jour `model_routing` dans le manifest
- Ajouter des filtres PreToolUse pour les commandes verbeuses
- Configurer `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` si pertinent

## HANDOFF JSON

```json
{
  "workflow": "cost-audit",
  "status": "complete",
  "period": "last 30 days",
  "total_cost_estimate": "$12.45",
  "cost_by_model": {"sonnet": "$8.20", "opus": "$3.80", "haiku": "$0.45"},
  "top_expensive_workflows": ["feature", "code-review", "security-audit"],
  "recommendations": [
    {"action": "Filter test output in PreToolUse", "savings": "~30%", "effort": "low"},
    {"action": "Route explorer to haiku", "savings": "~15%", "effort": "low"}
  ],
  "projected_savings": "35-40%"
}
```

## CONTRAT DE SORTIE

- [ ] Données d'utilisation collectées et analysées
- [ ] Coût par modèle, agent, et workflow calculé
- [ ] Top 5 patterns coûteux identifiés
- [ ] Recommandations avec estimation de savings
- [ ] Au moins 1 optimisation implémentée
- [ ] HANDOFF JSON produit
