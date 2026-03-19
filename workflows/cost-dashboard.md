# Workflow: Cost Dashboard

## Quand utiliser
- Analyser les coûts Claude Code de l'équipe
- Identifier les sessions les plus coûteuses
- Optimiser l'usage des tokens

## Sources de données

### Usage local (claudekit)
Les sessions sont loggées dans `.template/usage.jsonl` par le hook `stop.sh`.
Analyser avec :
```bash
python3 -c "
import json
from pathlib import Path
log = Path('.template/usage.jsonl')
if log.exists():
    sessions = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    print(f'Sessions: {len(sessions)}')
    for s in sessions[-10:]:
        print(f\"  {s.get('ts', '?')} — {s.get('changed_files', 0)} fichiers modifiés\")
"
```

### Grafana (équipe)
Utiliser le dashboard SigNoz/Grafana disponible sur : https://signoz.io/docs/dashboards/dashboard-templates/claude-code-dashboard/

### API Analytics Anthropic
Disponible sur https://platform.claude.com/docs/en/build-with-claude/claude-code-analytics-api pour les plans Team/Enterprise.

## Agent recommandé
`cost-analyst`

---

**HANDOFF JSON (pour orchestrateur) :**
```json
{"status": "completed", "summary": "", "next_action": "", "artifacts": []}
```
