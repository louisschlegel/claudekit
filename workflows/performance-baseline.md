# Workflow: Performance Baseline

## DÉCLENCHEUR
Intent classifié comme `perf-test` par le hook UserPromptSubmit.
Commande directe : "test de charge", "benchmark", "load test", "tient la charge ?", "mesure les performances", "profile l'appli".

## AGENTS IMPLIQUÉS
1. **Performance Analyst** — analyse des résultats, identification des régressions
2. **Deployer** — gate de déploiement si régression détectée

---

## ÉTAPE 1 — Définir les scénarios de test

Identifier les **endpoints critiques** (pas tout tester — tester ce qui compte) :
- Le chemin principal de l'utilisateur (ex : login → dashboard → action principale)
- Les endpoints les plus appelés (top 5 depuis les logs/APM)
- Les endpoints les plus lents
- Les endpoints sous lesquels la DB est la plus sollicitée

Pour chaque scénario, définir :
```
Scénario : [nom]
Endpoint : [méthode + URL]
Payload : [exemple de requête]
Données requises : [user de test, données en base, token d'auth]
```

---

## ÉTAPE 2 — Définir les SLOs cibles

Si pas de SLOs définis, utiliser ces valeurs par défaut :

| Métrique | Seuil par défaut | Critique |
|---------|-----------------|----------|
| Latency p50 | < 100ms | > 500ms |
| Latency p95 | < 200ms | > 1000ms |
| Latency p99 | < 500ms | > 2000ms |
| Error rate | < 0.1% | > 1% |
| Throughput | > 50 rps | < 10 rps |
| Memory | stable (pas de leak) | +20% sur la durée du test |
| CPU | < 70% à charge nominale | > 90% |

Adapter selon le projet (API temps-réel vs batch processing ont des SLOs très différents).

---

## ÉTAPE 3 — Préparer l'environnement de test

```bash
# Vérifier l'isolation — le test de charge ne doit PAS tourner en production
# Environnement recommandé : staging avec données réalistes (anonymisées)

# Préparer les données de test
# - Même volume que la prod (ou ratio documenté)
# - Utilisateurs de test avec tokens valides
# - Index DB identiques à la prod

# Désactiver les rate limiters pour le test
# (ou les configurer pour ne pas bloquer les VUs)

# Vérifier que le monitoring est actif
# (CPU, mémoire, connexions DB doivent être visibles pendant le test)
```

---

## ÉTAPE 4 — Exécuter les tests de charge

### Avec k6 (recommandé pour les APIs REST)

```javascript
// k6-test.js — Template à adapter
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('error_rate');
const apiLatency = new Trend('api_latency');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Montée progressive
    { duration: '2m',  target: 50 },   // Charge nominale
    { duration: '30s', target: 100 },  // Pic de charge
    { duration: '1m',  target: 50 },   // Redescente
    { duration: '30s', target: 0 },    // Arrêt
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],  // SLOs
    error_rate: ['rate<0.001'],                       // < 0.1% erreurs
    http_req_failed: ['rate<0.001'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export default function () {
  // Exemple : parcours utilisateur principal
  const headers = { Authorization: `Bearer ${AUTH_TOKEN}` };

  // Requête principale
  const res = http.get(`${BASE_URL}/api/users/me`, { headers });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  errorRate.add(res.status >= 400);
  apiLatency.add(res.timings.duration);

  sleep(1);
}
```

```bash
# Lancer le test
k6 run \
  -e BASE_URL=https://staging.example.com \
  -e AUTH_TOKEN=$(cat .test-token) \
  --out json=results/k6-$(date +%Y%m%d-%H%M).json \
  k6-test.js
```

### Avec Locust (recommandé pour Python / scénarios complexes)

```python
# locustfile.py — Template à adapter
from locust import HttpUser, task, between
import json

class APIUser(HttpUser):
    wait_time = between(0.5, 2)
    token = None

    def on_start(self):
        """Authentification au démarrage de chaque VU"""
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "test-password"
        })
        self.token = response.json().get("access_token")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(3)
    def get_main_resource(self):
        with self.client.get("/api/resources", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Got {response.status_code}")

    @task(1)
    def create_resource(self):
        payload = {"name": "test-item", "value": 42}
        with self.client.post("/api/resources", json=payload, catch_response=True) as response:
            if response.status_code not in [200, 201]:
                response.failure(f"Got {response.status_code}")
```

```bash
# Lancer le test Locust
locust -f locustfile.py \
  --host https://staging.example.com \
  --users 50 \
  --spawn-rate 10 \
  --run-time 3m \
  --headless \
  --csv results/locust-$(date +%Y%m%d-%H%M)
```

---

## ÉTAPE 5 — Collecter et analyser les résultats

Métriques à collecter :

```bash
# Depuis k6 (JSON output)
python3 - <<'EOF'
import json, statistics

results = []
with open("results/k6-latest.json") as f:
    for line in f:
        data = json.loads(line)
        if data.get("metric") == "http_req_duration":
            results.append(data["data"]["value"])

results.sort()
n = len(results)
print(f"p50:  {results[n//2]:.1f}ms")
print(f"p95:  {results[int(n*0.95)]:.1f}ms")
print(f"p99:  {results[int(n*0.99)]:.1f}ms")
print(f"max:  {results[-1]:.1f}ms")
EOF
```

Métriques système à surveiller pendant le test :
```bash
# Connexions DB actives (PostgreSQL)
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Mémoire et CPU de l'application
# (depuis votre monitoring : Datadog, Grafana, CloudWatch, htop)
```

---

## ÉTAPE 6 — Comparer vs baseline historique

Invoquer `performance-analyst` avec :
```
Résultats actuels : [p50, p95, p99, error_rate, throughput]
Baseline précédente : [depuis .template/perf-baselines.json]
Stack : [manifest stack]
Changements depuis la baseline : [liste des PRs/commits]
```

```bash
# Lire la baseline existante
cat .template/perf-baselines.json
```

Format de la baseline (`.template/perf-baselines.json`) :
```json
{
  "version": "v1.2.3",
  "date": "2024-01-15",
  "environment": "staging",
  "scenarios": {
    "GET /api/users/me": {
      "p50_ms": 45,
      "p95_ms": 120,
      "p99_ms": 280,
      "error_rate_pct": 0.02,
      "throughput_rps": 87
    }
  }
}
```

---

## ÉTAPE 7 — Gate : Détection de régression

**Seuils de régression :**

| Métrique | Avertissement | Bloquant |
|---------|--------------|----------|
| p95 latency | +10% | +20% |
| p99 latency | +15% | +30% |
| Error rate | +0.05% | +0.1% |
| Throughput | -10% | -20% |
| Memory | +10% | +20% |

Gate :
- Aucune régression → continuer le déploiement
- Régression AVERTISSEMENT → documenter, continuer avec approbation explicite
- Régression BLOQUANTE → **STOP**. Invoquer `performance-analyst` pour root cause

```python
# Calcul automatique de régression
def check_regression(baseline, current, threshold=0.20):
    regression = (current - baseline) / baseline
    if regression > threshold:
        return f"BLOQUANT: +{regression*100:.1f}% (seuil: +{threshold*100:.0f}%)"
    elif regression > threshold * 0.5:
        return f"AVERTISSEMENT: +{regression*100:.1f}%"
    elif regression < -0.05:
        return f"AMELIORATION: {regression*100:.1f}%"
    return "OK"
```

---

## ÉTAPE 8 — Si régression détectée

Invoquer `performance-analyst` avec :
```
Régression : p95 [avant]ms → [après]ms (+X%)
Changements récents : [liste des commits depuis la baseline]
Stack : [manifest stack]
```

Profiler l'application pour identifier le goulot d'étranglement :

```bash
# Python — profiler les requêtes lentes
# py-spy (production-safe)
py-spy top --pid $(pgrep -f "uvicorn\|gunicorn\|django")

# Node.js — profiler avec clinic
clinic doctor -- node server.js

# PostgreSQL — identifier les requêtes lentes
psql -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Vérifier les N+1 queries
# (activer le query logging dans Django/SQLAlchemy/Sequelize)
```

---

## ÉTAPE 9 — Mettre à jour la baseline

Seulement si les performances sont égales ou meilleures que la baseline actuelle :

```bash
# Mettre à jour .template/perf-baselines.json
python3 scripts/update-perf-baseline.py \
  --results results/k6-$(date +%Y%m%d)*.json \
  --version $(git describe --tags --abbrev=0) \
  --env staging
```

Committer la baseline mise à jour :
```bash
git add .template/perf-baselines.json
git commit -m "perf: update baseline to v[X.Y.Z] — p95 [N]ms ([+/-N]%)"
```

---

## CONTRAT DE SORTIE

```
PERFORMANCE TEST: [scenario(s) tested]
DATE: YYYY-MM-DD
ENVIRONMENT: staging / prod-like
VERSION: [git tag ou commit]

RESULTS:
  Scenario: [nom]
  p50:  [N]ms  (baseline: [N]ms, delta: [+/-N]%)
  p95:  [N]ms  (baseline: [N]ms, delta: [+/-N]%)
  p99:  [N]ms  (baseline: [N]ms, delta: [+/-N]%)
  Error rate: [N]%  (SLO: < 0.1%)
  Throughput: [N] rps  (SLO: > [N] rps)

REGRESSION GATE: PASS / WARN / BLOCK
  [Détail des métriques hors seuil si applicable]

BASELINE: updated / unchanged
DEPLOY: unblocked / blocked — [raison]

PERFORMANCE ANALYST: [résumé des recommandations si régression]
```
