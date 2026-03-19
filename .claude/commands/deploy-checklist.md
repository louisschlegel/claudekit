# Command: /deploy-checklist

Checklist pré-déploiement complète.

## Checks obligatoires

- [ ] **Tests** : tous les tests passent (`make test` / `pytest` / `npm test`)
- [ ] **Lint** : pas d'erreurs de linting
- [ ] **Type-check** : pas d'erreurs de typage (si applicable)
- [ ] **Migrations** : migrations créées et testées localement
- [ ] **Env vars** : nouvelles variables documentées et ajoutées en staging/prod
- [ ] **CHANGELOG** : mis à jour avec les changements
- [ ] **Version** : bumpée si release

## Checks recommandés

- [ ] **Rollback plan** : documenté et testé
- [ ] **Feature flags** : changements risqués derrière un flag
- [ ] **Monitoring** : alertes configurées pour les nouvelles features
- [ ] **Performance** : pas de régression détectée (load test si critique)
- [ ] **Sécurité** : `/check-security` passé
- [ ] **Documentation** : API docs et README à jour
- [ ] **Communication** : équipe/stakeholders informés du déploiement

## Après déploiement

- [ ] **Smoke tests** : endpoints critiques répondent en prod
- [ ] **Monitoring** : pas d'erreurs anormales dans les 15 premières minutes
- [ ] **Health check** : `/health` retourne 200
