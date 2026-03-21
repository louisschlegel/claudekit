# Workflow: Monitoring avec /loop

Utiliser `/loop` pour surveiller automatiquement le projet pendant le développement.

## Patterns

### Health check continu
```
/loop 5m Vérifie que le serveur sur localhost:8000 répond, affiche le status HTTP
```

### CI babysitting
```
/loop 3m Vérifie le status du dernier run CI avec gh run list --limit 1. Si failed, lis les logs et propose un fix.
```

### Error log scanning
```
/loop 10m Scanne les 50 dernières lignes de logs/app.log pour ERROR ou FATAL. Si trouvé, ouvre un diagnostic.
```

### Test regression watch
```
/loop 15m Lance pytest tests/ -q. Si des tests fail, identifie la cause et propose le fix.
```

### Drift detection (IaC)
```
/loop 30m Lance terraform plan et signale si des changements sont détectés
```

## Limites
- Max 50 tâches simultanées par session
- Auto-expire après 3 jours
- S'arrête quand le terminal se ferme
- État non sauvegardé entre sessions

## HANDOFF JSON

```json
{
  "workflow": "monitoring",
  "status": "active",
  "loops": [
    {"task": "health-check", "interval": "5m", "status": "running"},
    {"task": "ci-watch", "interval": "3m", "status": "running"}
  ]
}
```

## CONTRAT DE SORTIE

- [ ] Au moins 1 loop configuré et actif
- [ ] Alertes fonctionnelles (testées manuellement)
- [ ] HANDOFF JSON produit
