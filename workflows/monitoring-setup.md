# Workflow: Monitoring Setup

**Déclenché par :** `[INTENT:monitoring-setup]` — mots-clés : "setup monitoring", "configure observabilité", "ajoute prometheus", "grafana", "datadog", "sentry", "configure les alertes", "métriques", "logs centralisés", "tracing", "observabilité"

**Agents impliqués :** devops-engineer → architect → doc-writer

---

## Vue d'ensemble

```
Stack détectée (manifest)
        ↓
Choix de la stack monitoring (3 pilliers)
        ↓
    Métriques          Logs              Traces
  (Prometheus/       (Loki/             (Jaeger/
  Datadog/           Elasticsearch/     Tempo/
  CloudWatch)        Datadog Logs)      Datadog APM)
        ↓                 ↓                  ↓
        └─────────────────┴──────────────────┘
                          ↓
               Dashboards + Alertes
                          ↓
              SLO/SLA monitoring
                          ↓
              Runbooks + Documentation
```

---

## Étape 1 — Audit de l'observabilité existante

```bash
# Vérifier ce qui existe déjà
grep -r "prometheus\|grafana\|datadog\|sentry\|newrelic\|opentelemetry" \
  requirements.txt package.json go.mod Cargo.toml 2>/dev/null

grep -r "logging\|logger\|log\." src/ --include="*.py" --include="*.ts" \
  -l | head -20  # fichiers qui loggent déjà

# Vérifier les variables d'env de monitoring
grep -r "DATADOG\|DD_\|SENTRY\|PROMETHEUS\|GRAFANA\|OTEL_" .env.example 2>/dev/null
```

**Inventaire :**
```
□ Métriques applicatives existantes ?
□ Logs structurés ou printf ?
□ Tracing distribué en place ?
□ Alertes configurées ?
□ Dashboards existants ?
□ SLOs définis ?
```

---

## Étape 2 — Choix de la stack monitoring

Selon `deploy_target` et le stack du manifest :

### Option A — Self-hosted (Kubernetes / Docker Compose)
**Prometheus + Grafana + Loki + Tempo** (stack Grafana complète)
```yaml
# Stack recommandée si vous gérez votre infra
Métriques : Prometheus + Grafana
Logs :      Loki + Promtail
Traces :    Tempo + OpenTelemetry
Alertes :   Grafana Alerting ou Alertmanager
```

### Option B — SaaS managé
**Datadog** (tout-en-un) ou **New Relic** ou **Honeycomb**
```
Métriques + Logs + Traces + APM dans une seule plateforme
Coût : ~$15-23/host/mois (Datadog)
Avantage : zéro ops, corrélation automatique logs/traces/métriques
```

### Option C — Cloud natif
```
AWS :   CloudWatch + X-Ray + Container Insights
GCP :   Cloud Monitoring + Cloud Logging + Cloud Trace
Azure : Azure Monitor + Application Insights
```

### Option D — Hybride économique
**Sentry** (erreurs) + **Grafana Cloud** (métriques/logs gratuit jusqu'à 10k séries)

**Règles de sélection automatique :**
```python
if deploy_target in ["vercel", "railway", "render"]:
    → recommander Datadog ou Grafana Cloud (SaaS)
elif deploy_target in ["aws"]:
    → recommander CloudWatch + X-Ray ou Datadog
elif deploy_target in ["kubernetes", "docker"]:
    → recommander Prometheus + Grafana stack
elif budget == "low":
    → recommander Sentry + Grafana Cloud free tier
```

---

## Étape 3 — Configuration des métriques

### Métriques applicatives (instrumentation)

**Python (FastAPI / Flask) :**
```python
# requirements.txt
prometheus-client==0.20.0
opentelemetry-sdk==1.23.0
opentelemetry-exporter-otlp==1.23.0

# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Métriques métier critiques
REQUEST_COUNT = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'app_request_duration_seconds',
    'Request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

ACTIVE_USERS = Gauge('app_active_users', 'Currently active users')

# Métriques business (adapter au domaine)
ORDERS_CREATED = Counter('business_orders_created_total', 'Orders created', ['status'])
REVENUE_PROCESSED = Counter('business_revenue_dollars_total', 'Revenue processed')

# Middleware FastAPI
from fastapi import Request
import time

async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

**TypeScript (Express / NestJS) :**
```typescript
// npm install prom-client @opentelemetry/sdk-node
import { Counter, Histogram, Registry } from 'prom-client';

const register = new Registry();

const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [register],
});

const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path'],
  buckets: [0.01, 0.05, 0.1, 0.3, 0.5, 1, 2, 5],
  registers: [register],
});

// Middleware Express
app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer({
    method: req.method,
    path: req.route?.path || req.path,
  });
  res.on('finish', () => {
    httpRequestsTotal.inc({ method: req.method, path: req.path, status: res.statusCode });
    end();
  });
  next();
});

// Endpoint /metrics
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

**Go :**
```go
// go get github.com/prometheus/client_golang
import "github.com/prometheus/client_golang/prometheus"
import "github.com/prometheus/client_golang/prometheus/promhttp"

var (
    httpRequests = prometheus.NewCounterVec(
        prometheus.CounterOpts{Name: "http_requests_total"},
        []string{"method", "path", "status"},
    )
    httpDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path"},
    )
)

func init() {
    prometheus.MustRegister(httpRequests, httpDuration)
}

// Exposer /metrics
http.Handle("/metrics", promhttp.Handler())
```

---

## Étape 4 — Logs structurés

**Principe : JSON logging partout, jamais de printf en prod**

**Python :**
```python
# pip install structlog
import structlog
import logging

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()

# Usage — chaque log doit avoir du contexte
log.info("order_created",
    order_id=order.id,
    user_id=user.id,
    amount=order.total,
    duration_ms=duration
)

log.error("payment_failed",
    order_id=order.id,
    error=str(e),
    provider="stripe",
    exc_info=True
)
```

**TypeScript :**
```typescript
// npm install pino pino-pretty
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: process.env.SERVICE_NAME || 'app',
    env: process.env.NODE_ENV,
  },
});

// Usage
logger.info({ userId, orderId, amount }, 'order_created');
logger.error({ err, orderId }, 'payment_failed');
```

**Niveaux de logs standardisés :**
```
DEBUG   → Dev uniquement, jamais en prod
INFO    → Événements métier normaux (order_created, user_login)
WARN    → Dégradation non-critique (retry, rate limit approché)
ERROR   → Erreurs récupérables (payment_failed, external API down)
FATAL   → Erreurs non-récupérables → process s'arrête
```

**Ne jamais logger :**
```python
NEVER_LOG = [
    "password", "token", "secret", "api_key",
    "credit_card", "ssn", "dob",  # PII/compliance
    "session_id",                  # sécurité
]
# Utiliser des masques : user_id pas email, order_id pas adresse complète
```

---

## Étape 5 — Tracing distribué (OpenTelemetry)

```python
# pip install opentelemetry-sdk opentelemetry-exporter-otlp
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Setup
provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317"))
)
trace.set_tracer_provider(provider)

# Auto-instrumentation (zéro code)
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)
RedisInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()

# Spans custom pour les opérations business
tracer = trace.get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("order.amount", order.total)

        with tracer.start_as_current_span("validate_payment"):
            await validate_payment(order)

        with tracer.start_as_current_span("update_inventory"):
            await update_inventory(order.items)
```

---

## Étape 6 — Configuration Prometheus + Grafana (self-hosted)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"

  loki:
    image: grafana/loki:latest
    volumes:
      - loki_data:/loki
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./monitoring/promtail.yml:/etc/promtail/config.yml

  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts/*.yml"

scrape_configs:
  - job_name: 'app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

---

## Étape 7 — Alertes critiques

```yaml
# monitoring/alerts/app.yml
groups:
  - name: app_alerts
    rules:
      # Latence p95 > 500ms
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latence p95 élevée: {{ $value | humanizeDuration }}"

      # Taux d'erreur > 1%
      - alert: HighErrorRate
        expr: rate(app_requests_total{status_code=~"5.."}[5m]) / rate(app_requests_total[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Taux d'erreur 5xx: {{ $value | humanizePercentage }}"

      # Service down
      - alert: ServiceDown
        expr: up{job="app"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} est down"

      # Base de données : connexions saturées
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} connexions PostgreSQL actives"

      # Disque > 85%
      - alert: DiskSpaceHigh
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disque à {{ $value | humanizePercentage }}"
```

---

## Étape 8 — SLOs (Service Level Objectives)

```yaml
# monitoring/slos.yml
# Définir les SLOs AVANT les alertes — les alertes découlent des SLOs

slos:
  - name: api_availability
    description: "API disponible 99.9% du temps"
    target: 0.999
    window: 30d
    indicator:
      # Bon event : requête avec status < 500 ET latence < 1s
      good: rate(app_requests_total{status_code!~"5.."}[5m])
      total: rate(app_requests_total[5m])

  - name: api_latency
    description: "95% des requêtes répondent en < 200ms"
    target: 0.95
    window: 30d
    indicator:
      good: rate(app_request_duration_seconds_bucket{le="0.2"}[5m])
      total: rate(app_request_duration_seconds_count[5m])
```

**Error budget alerting :**
```yaml
# Alerte quand error budget consommé à > 50% en 1h (burn rate trop rapide)
- alert: ErrorBudgetBurnRateHigh
  expr: |
    (
      rate(app_requests_total{status_code=~"5.."}[1h]) /
      rate(app_requests_total[1h])
    ) > (1 - 0.999) * 14.4  # 14.4x burn rate = budget épuisé en 2h
  for: 5m
  labels:
    severity: critical
```

---

## Étape 9 — Dashboard Grafana standard

Créer `monitoring/grafana/dashboards/app-overview.json` avec :

```
Panels obligatoires :
□ Request rate (RPS) — graph temps réel
□ Error rate (%) — graph avec seuil rouge à 1%
□ Latence p50 / p95 / p99 — heatmap ou graph
□ Active connections — gauge
□ CPU + Mémoire — graph
□ Database connections + query time
□ Cache hit rate (si Redis)
□ Error budget restant (si SLO configuré)
□ Dernières alertes déclenchées
```

---

## Étape 10 — Configuration Sentry (error tracking)

```python
# pip install sentry-sdk[fastapi]
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    environment=os.environ.get("ENVIRONMENT", "production"),
    traces_sample_rate=0.1,      # 10% des transactions tracées
    profiles_sample_rate=0.1,    # 10% profilés
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
    ],
    before_send=lambda event, hint: _scrub_pii(event),  # RGPD
    release=os.environ.get("APP_VERSION"),
)

def _scrub_pii(event: dict) -> dict:
    """Supprimer les données personnelles avant envoi à Sentry."""
    for frame in event.get("exception", {}).get("values", [{}]):
        for var in frame.get("stacktrace", {}).get("frames", [{}]):
            for key in list(var.get("vars", {}).keys()):
                if any(pii in key.lower() for pii in ["password", "token", "email", "phone"]):
                    var["vars"][key] = "[Filtered]"
    return event
```

---

## CONTRAT DE SORTIE

```
STACK MONITORING:
  Métriques:  [Prometheus/Datadog/CloudWatch]
  Logs:       [Loki/Elasticsearch/Datadog]
  Traces:     [Jaeger/Tempo/Datadog APM]
  Errors:     [Sentry/Datadog/Rollbar]

FICHIERS CRÉÉS:
  - monitoring/prometheus.yml
  - monitoring/alerts/app.yml
  - monitoring/grafana/dashboards/app-overview.json
  - docker-compose.monitoring.yml (si self-hosted)
  - src/metrics.py (ou metrics.ts)

INSTRUMENTATION:
  - Métriques applicatives: {N} métriques définies
  - Logs structurés: OUI | À FAIRE
  - Tracing: OUI | À FAIRE
  - Error tracking (Sentry): OUI | À FAIRE

ALERTES CONFIGURÉES: {N} alertes
  Critical: {N}
  Warning:  {N}

SLOs DÉFINIS: {N}
  Disponibilité: {target}%
  Latence p95:   {target}ms

RUNBOOK: monitoring/runbook.md (généré)
```

**HANDOFF JSON :**
```json
{
  "monitoring_stack": {
    "metrics": "prometheus|datadog|cloudwatch",
    "logs": "loki|elasticsearch|datadog",
    "traces": "jaeger|tempo|datadog",
    "errors": "sentry|datadog"
  },
  "files_created": ["..."],
  "metrics_defined": 0,
  "alerts_configured": 0,
  "slos_defined": [],
  "structured_logging": false,
  "tracing_enabled": false,
  "sentry_configured": false,
  "dashboards_created": 0
}
```
