# Command: /incident-response

Playbook de réponse à incident. Suit le protocole : Triage → Diagnose → Fix → Post-mortem.

## Phase 1 : Triage (5 min)

1. **Sévérité** :
   - **SEV1** : Service down, perte de données, breach sécurité → tout le monde on-call
   - **SEV2** : Dégradation majeure, feature critique cassée → équipe concernée
   - **SEV3** : Bug mineur, dégradation cosmétique → backlog

2. **Impact** : combien d'utilisateurs affectés ? Depuis quand ?
3. **Communication** : notifier le canal incident (Slack/Teams)

## Phase 2 : Diagnose (15 min)

1. Vérifier les dashboards (Grafana, Datadog, Sentry)
2. Lire les logs récents (`kubectl logs`, CloudWatch, journalctl)
3. Identifier le dernier déploiement (`git log --oneline -5`)
4. Corréler avec les changements récents

## Phase 3 : Fix

1. **Rollback** si le déploiement est la cause : `git revert HEAD && deploy`
2. **Hotfix** si rollback impossible : branche `hotfix/*`, fix minimal, déployer
3. **Mitigation** temporaire : feature flag, DNS failover, scale up

## Phase 4 : Post-mortem (24h après)

Créer `docs/postmortems/YYYY-MM-DD-<titre>.md` :
- Timeline
- Root cause (5 Whys)
- Impact chiffré
- Actions correctives (avec owners et deadlines)
- Ce qui a bien/mal fonctionné dans la réponse
