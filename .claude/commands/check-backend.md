# Command: /check-backend

Vérification santé du backend.

## Checks

1. **Endpoints** : tester les routes principales (health, auth, CRUD) via curl
2. **Base de données** : connexion OK, migrations appliquées, pas de migration pending
3. **Queues** : consumers actifs (Celery, Bull, Sidekiq)
4. **Logs d'erreur** : scanner les 100 dernières lignes pour ERROR/CRITICAL
5. **Performance** : temps de réponse moyen des endpoints principaux
6. **Env vars** : toutes les variables requises sont définies

## Output
```
Backend Health Check — <project_name>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Health endpoint responds (23ms)
✓ Database connection OK
✓ All migrations applied (0 pending)
✗ 3 ERROR entries in last 100 log lines
✓ Avg response time: 45ms
✓ All required env vars present
```
