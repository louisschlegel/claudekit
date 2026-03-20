# Command: /cost-report

Génère un rapport de coûts estimés de la session et des sessions récentes.

## Protocole

1. Lire `.template/usage.jsonl` (si existant)
2. Lire `.template/agent-events.jsonl` (événements par outil)
3. Calculer :
   - Coût estimé de la session courante
   - Coût moyen par session (7 derniers jours)
   - Top 3 opérations les plus coûteuses
   - Répartition par modèle (Haiku/Sonnet/Opus)
4. Afficher un résumé formaté :

```
Cost Report — claudekit
━━━━━━━━━━━━━━━━━━━━━━━━
This session:  ~$0.45 (1,200 in + 8,500 out tokens)
Last 7 days:   ~$3.20 (avg $0.46/session)

By model:      Sonnet 78% | Opus 18% | Haiku 4%
Top costs:     1. code-review ($0.82)
               2. feature workflow ($0.65)
               3. security-audit ($0.41)

Recommendations:
  → Route explorer agent to Haiku (saves ~$0.15/session)
  → Filter pytest output with -q (saves ~30% on test runs)
```
