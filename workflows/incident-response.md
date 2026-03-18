# Workflow: Incident Response

## DÉCLENCHEUR
Intent classifié comme `incident` par le hook UserPromptSubmit.
Commande directe : "incident prod", "alerte critique", "service dégradé", "SLA breach", "production down", "ça crashe en prod".

**Note :** Ce workflow couvre la gestion complète de l'incident (communication, triage, coordination, post-mortem). Pour la correction technique pure, voir `workflows/hotfix.md`. Les deux workflows peuvent être exécutés en parallèle.

## AGENTS IMPLIQUÉS
1. **Debug Detective** — root cause analysis en mode express
2. **Deployer** — rollback et déploiement du fix
3. **Doc Writer** — post-mortem structuré

---

## PHASE 1 — DÉTECTION & TRIAGE (objectif : < 5 min)

### 1.1 — Classifier la sévérité

| Niveau | Critères | Temps de réponse |
|--------|----------|-----------------|
| **P1** | Service totalement indisponible, perte de revenus directe, données compromises | Immédiat |
| **P2** | Fonctionnalité critique dégradée, > 20% des utilisateurs impactés | < 15 min |
| **P3** | Fonctionnalité secondaire dégradée, < 20% des utilisateurs impactés | < 1h |

### 1.2 — Définir le périmètre

Répondre immédiatement à ces questions :
- Depuis quand ? (timestamp précis depuis les logs/monitoring)
- Quels endpoints / services / régions sont impactés ?
- Combien d'utilisateurs ? (sessions actives, erreurs par minute)
- Y a-t-il eu un déploiement récent ? (< 2h)
- Y a-t-il eu un changement d'infrastructure récent ? (scaling, certs, DNS)

```bash
# Vérifier les derniers déploiements
git log --oneline -10
# ou depuis votre CI/CD

# Vérifier les métriques
# (adapter selon votre stack : Datadog, Grafana, CloudWatch, etc.)
curl -s "https://api.monitoring.example.com/metrics/error_rate?last=30m"
```

### 1.3 — Communication initiale (immédiate pour P1/P2)

Poster dans le canal de communication d'équipe (Slack, Teams, etc.) :

```
[P1 INCIDENT] Service [NOM] dégradé depuis [HEURE UTC]
Impact : [N utilisateurs / % des requêtes en erreur]
Symptôme : [description en 1 phrase]
Status : INVESTIGATING
Incident commander : [ton nom]
Prochain update : dans 15 minutes
```

**Désigner un Incident Commander** (une seule personne coordonne, les autres exécutent).

---

## PHASE 2 — MITIGATION RAPIDE (objectif : < 30 min)

**Priorité absolue : réduire l'impact utilisateur AVANT d'identifier la cause racine.**

### 2.1 — Évaluer les options de mitigation rapide

Dans l'ordre de préférence (du moins risqué au plus risqué) :

**Option A : Rollback (si déploiement récent)**
```bash
# Identifier le dernier déploiement stable
git log --oneline -5

# Rollback vers la version précédente
# Railway / Render : rollback depuis le dashboard
# Heroku : heroku rollback
# Kubernetes : kubectl rollout undo deployment/[nom]
# Docker Swarm : docker service update --rollback [service]
```
Invoquer `deployer` avec : `Mode: rollback, Target: [version stable]`

**Option B : Feature flag (si la feature impactée est isolée)**
```bash
# Désactiver la feature via le système de feature flags
# (LaunchDarkly, Unleash, flags en DB, etc.)
```

**Option C : Rate limiting / Circuit breaker**
```bash
# Activer le rate limiting agressif pour protéger le service dégradé
# nginx : limit_req_zone / limit_req
# Cloudflare : activer le mode "Under Attack"
```

**Option D : Maintenance page**
```bash
# Dernier recours — activer une page de maintenance
# Cela stoppe l'hémorragie mais dégrade intentionnellement le service
```

### 2.2 — Mettre à jour le statut

```
[P1 INCIDENT] Service [NOM] — Update [HEURE UTC]
Status : MITIGATING
Action : [rollback v1.2.3 en cours / feature flag désactivé / etc.]
ETA : [N minutes]
Prochain update : dans 15 minutes
```

---

## PHASE 3 — INVESTIGATION

Invoquer `debug-detective` en mode express avec :
```
Mode : incident express
Symptôme : [description + métriques d'erreur]
Timestamp début : [HEURE UTC]
Changements récents : [déploiements, config, infrastructure dans les dernières 4h]
Logs disponibles : [copier les N dernières lignes de logs d'erreur]
Métriques : [error rate, latency, memory, CPU]
```

```bash
# Collecter les logs d'erreur
# Application logs
tail -n 200 /var/log/app/error.log
# ou depuis votre système de logs centralisé
# kubectl logs deployment/[nom] --since=30m --previous

# Vérifier les ressources système
# CPU / Mémoire / Disk / Connexions DB
```

Le debug-detective fournit :
- ROOT CAUSE (hypothèse principale)
- CONTRIBUTING FACTORS
- EVIDENCE (logs, métriques qui confirment)
- FIX RECOMMENDATION

---

## PHASE 4 — RÉSOLUTION

Si rollback déjà effectué en Phase 2 et service stable → passer directement à Phase 5.

Sinon, appliquer le fix recommandé par le debug-detective :
- Si fix court (< 30 min) → corriger et déployer (voir `workflows/hotfix.md`)
- Si fix long → maintenir la mitigation (rollback, feature flag) et planifier le fix

```bash
# Déploiement du fix
git checkout -b hotfix/[nom-incident]
# Appliquer le fix
git commit -m "fix: [description] — résolution incident [date]"

# Invoquer deployer
```

---

## PHASE 5 — VÉRIFICATION

**Ne pas clôturer l'incident sans vérification active.**

```bash
# Health checks
curl -f https://[service]/health
curl -f https://[service]/ready

# Vérifier les métriques clés (attendre 5-10 min de stabilisation)
# - Error rate < seuil normal
# - Latency p95 < SLO
# - Throughput revenu à la normale
# - Aucune alerte active
```

Checklist de vérification :
- [ ] Health check passe
- [ ] Error rate < 0.1% (ou seuil normal du service)
- [ ] Latency p95 dans les SLOs
- [ ] Logs sans erreurs nouvelles sur 5 min consécutives
- [ ] Monitoring confirme la normalisation

---

## PHASE 6 — COMMUNICATION DE CLÔTURE

```
[P1 RESOLVED] Service [NOM] — [HEURE UTC]
Durée de l'incident : [N minutes]
Impact : [N utilisateurs / % de requêtes affectées]
Root cause : [description en 1 phrase]
Fix appliqué : [description en 1 phrase]
Actions préventives : à venir dans le post-mortem
```

Mettre à jour la status page si applicable (Statuspage.io, BetterUptime, etc.).

---

## PHASE 7 — POST-MORTEM (dans les 24-48h)

Invoquer `doc-writer` avec :
```
Type : post-mortem
Incident : [titre]
Durée : [timestamp début → fin]
Sévérité : P1/P2/P3
```

### Template de post-mortem

```markdown
# Post-Mortem : [Titre de l'incident]

**Date :** [YYYY-MM-DD]
**Durée :** [HH:MM] — [HH:MM] ([N minutes])
**Sévérité :** P1 / P2 / P3
**Incident Commander :** [nom]

## Résumé
[2-3 phrases décrivant l'incident, l'impact et la résolution]

## Timeline
| Heure UTC | Événement |
|-----------|-----------|
| HH:MM | Première alerte / premier symptôme détecté |
| HH:MM | Incident déclaré, triage commencé |
| HH:MM | Mitigation appliquée ([rollback/flag/etc.]) |
| HH:MM | Root cause identifiée |
| HH:MM | Fix déployé |
| HH:MM | Service vérifié stable — incident clos |

## Root Cause
[Description technique précise de la cause racine]

## Facteurs contributifs
- [Facteur 1]
- [Facteur 2]

## Impact
- Utilisateurs impactés : [N ou %]
- Durée d'indisponibilité totale : [N minutes]
- SLA impact : [oui/non — détail]

## Ce qui a bien fonctionné
- [Point 1]
- [Point 2]

## Ce qui a mal fonctionné
- [Point 1]
- [Point 2]

## Actions préventives
| Action | Responsable | Date cible | Ticket |
|--------|-------------|------------|--------|
| [action 1] | [nom] | [date] | [#] |
| [action 2] | [nom] | [date] | [#] |
```

Mettre à jour `learning.md` section "Incidents" :
```markdown
### [date] — [titre incident]
- **Sévérité** : P1/P2/P3
- **Durée** : [N min]
- **Root cause** : [description]
- **Fix** : [description]
- **Prévention** : [actions prises]
```

---

## CONTRAT DE SORTIE

```
INCIDENT: [titre]
SEVERITY: P1 / P2 / P3
DURATION: [HH:MM UTC] → [HH:MM UTC] ([N minutes])

IMPACT:
  Users affected: [N]
  Error rate peak: [%]
  SLA breach: yes/no

ROOT CAUSE: [description en 1 phrase]
FIX: [rollback v1.2.3 / feature flag / hotfix deployed]

PHASES:
  Detection: [N min]
  Mitigation: [N min]
  Resolution: [N min]
  Verification: [N min]

COMMUNICATION:
  Initial: sent
  Updates: [N sent]
  Resolution: sent
  Status page: updated / not applicable

POST-MORTEM:
  Status: completed / scheduled [date]
  Actions: [N items identified]

LEARNING.MD: updated
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "incident_id": "...",
  "severity": "P1|P2",
  "duration_minutes": 0,
  "root_cause": "...",
  "mitigated": false,
  "postmortem_path": "..."
}
```
