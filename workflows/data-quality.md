# Workflow: Data Quality Audit

**Déclenché par :** `[INTENT:data-quality]` — mots-clés : "qualité des données", "data quality", "great expectations", "dbt test", "audit pipeline", "données corrompues", "anomalie de données"

**Agents impliqués :** data-engineer → tester → reviewer

---

## Vue d'ensemble

```
Inventaire des sources → Profiling → Tests GE/dbt → Règles métier
         ↓                                                ↓
  Anomalies détectées ──────────────────────────→ Alertes + Remédiation
         ↓
  Data quality score + SLA
```

---

## Étape 1 — Inventaire et profiling

```python
import pandas as pd
import great_expectations as gx

# Profiling automatique
context = gx.get_context()
validator = context.sources.pandas_default.read_dataframe(df)

# Métriques de base à collecter pour chaque table :
profile = {
    "row_count": len(df),
    "null_pct": df.isnull().mean().to_dict(),
    "duplicate_pct": df.duplicated().mean(),
    "schema": df.dtypes.to_dict(),
    "value_ranges": df.describe().to_dict(),
    "cardinality": {col: df[col].nunique() for col in df.columns},
}
```

**Questions à répondre pour chaque table :**
- Combien de lignes ? Évolution attendue vs observée ?
- Taux de nulls par colonne — acceptable ?
- Doublons sur la clé primaire ?
- Valeurs hors plage (dates dans le futur, montants négatifs, etc.) ?
- Références orphelines (FK sans PK correspondante) ?

---

## Étape 2 — Great Expectations — suite de tests

```python
# great_expectations_suite.py
import great_expectations as gx

context = gx.get_context()

# Créer ou charger une suite
suite = context.add_expectation_suite("orders_suite")

validator = context.get_validator(
    batch_request=batch_request,
    expectation_suite_name="orders_suite"
)

# ── Complétude ─────────────────────────────────────────────
validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_not_be_null("customer_id")
validator.expect_column_values_to_not_be_null("created_at")

# ── Unicité ────────────────────────────────────────────────
validator.expect_column_values_to_be_unique("order_id")

# ── Plages de valeurs ──────────────────────────────────────
validator.expect_column_values_to_be_between("amount", min_value=0)
validator.expect_column_values_to_be_between(
    "created_at",
    min_value="2020-01-01",
    max_value="today"
)

# ── Ensembles de valeurs ───────────────────────────────────
validator.expect_column_values_to_be_in_set(
    "status", ["pending", "confirmed", "shipped", "delivered", "cancelled"]
)

# ── Patterns ──────────────────────────────────────────────
validator.expect_column_values_to_match_regex(
    "email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# ── Volume ────────────────────────────────────────────────
validator.expect_table_row_count_to_be_between(min_value=1000, max_value=10_000_000)

# ── Fraîcheur ─────────────────────────────────────────────
validator.expect_column_max_to_be_between(
    "created_at",
    min_value=(datetime.now() - timedelta(hours=25)).isoformat()
)

validator.save_expectation_suite()

# Exécuter et générer le rapport
results = context.run_checkpoint(checkpoint_name="orders_checkpoint")
print(f"Success: {results.success}")
```

---

## Étape 3 — dbt tests

```yaml
# models/marts/orders/schema.yml
models:
  - name: orders
    description: "Table de commandes normalisée"
    columns:
      - name: order_id
        description: "Identifiant unique de commande"
        tests:
          - unique
          - not_null

      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('customers')
              field: customer_id

      - name: status
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']

      - name: amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

      - name: created_at
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= current_timestamp"

# Test de fraîcheur
sources:
  - name: raw
    tables:
      - name: orders
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
        loaded_at_field: _etl_loaded_at
```

```bash
# Exécuter les tests dbt
dbt test --select orders
dbt source freshness
dbt test --store-failures  # Stocker les échecs pour analyse
```

---

## Étape 4 — Règles métier personnalisées

```sql
-- tests/generic/no_orphan_orders.sql
-- Commandes sans client correspondant
SELECT order_id
FROM {{ ref('orders') }} o
LEFT JOIN {{ ref('customers') }} c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL

-- tests/generic/revenue_reconciliation.sql
-- Réconciliation revenus : somme commandes vs table de synthèse
WITH orders_total AS (
    SELECT SUM(amount) as total FROM {{ ref('orders') }}
    WHERE status = 'confirmed' AND date_trunc('month', created_at) = date_trunc('month', current_date)
),
summary_total AS (
    SELECT monthly_revenue FROM {{ ref('revenue_summary') }}
    WHERE month = date_trunc('month', current_date)
)
SELECT ABS(o.total - s.monthly_revenue) as discrepancy
FROM orders_total o, summary_total s
WHERE ABS(o.total - s.monthly_revenue) > 0.01  -- tolérance 1 centime
```

---

## Étape 5 — Data quality score et SLA

```python
# data_quality_score.py
from dataclasses import dataclass

@dataclass
class QualityDimension:
    name: str
    score: float  # 0-100
    weight: float

def compute_dq_score(dimensions: list[QualityDimension]) -> float:
    """Score pondéré de qualité des données (0-100)"""
    total_weight = sum(d.weight for d in dimensions)
    return sum(d.score * d.weight / total_weight for d in dimensions)

# Dimensions standard (ISO 8000) :
dimensions = [
    QualityDimension("completeness",  score=95.0, weight=0.25),  # % non-null
    QualityDimension("uniqueness",    score=99.9, weight=0.25),  # % sans doublons
    QualityDimension("validity",      score=97.0, weight=0.20),  # % respectant les contraintes
    QualityDimension("timeliness",    score=88.0, weight=0.15),  # % dans les délais SLA
    QualityDimension("consistency",   score=94.0, weight=0.10),  # % cohérents cross-sources
    QualityDimension("accuracy",      score=91.0, weight=0.05),  # % corrects vs source of truth
]

score = compute_dq_score(dimensions)
print(f"Data Quality Score: {score:.1f}/100")

# SLA : alerter si score < seuil
SLA_THRESHOLD = 95.0
if score < SLA_THRESHOLD:
    send_alert(f"DQ score {score:.1f} below SLA {SLA_THRESHOLD}")
```

---

## Étape 6 — Alerting et remédiation

**Stratégies de remédiation selon le type d'anomalie :**

| Anomalie | Stratégie | Action |
|----------|-----------|--------|
| Nulls > seuil | Imputation ou rejet | Dead letter queue |
| Doublons | Déduplication | `ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC)` |
| Valeurs hors plage | Clipping ou rejet | Log + alerting |
| Fraîcheur dépassée | Relancer le pipeline | Trigger DAG Airflow |
| Références orphelines | Enrichissement | JOIN avec table de référence |
| Volume anormal | Investigation | Alerting + pause pipeline |

---

## CONTRAT DE SORTIE

```
TABLES AUDITED: [liste]
AUDIT DATE: [date]

QUALITY SCORES:
  Completeness: X%
  Uniqueness: X%
  Validity: X%
  Timeliness: X%
  Overall DQ Score: X/100

CRITICAL ISSUES: [liste — bloquent les SLAs]
WARNINGS: [liste — à corriger cette semaine]

TESTS ADDED: [N] GE expectations, [N] dbt tests
SLA STATUS: [pass/fail] (threshold: X)

FILES TO CREATE/MODIFY:
  [liste]
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "tables_audited": ["..."],
  "dq_score": 0.0,
  "dimensions": {
    "completeness": 0.0,
    "uniqueness": 0.0,
    "validity": 0.0,
    "timeliness": 0.0
  },
  "critical_issues": ["..."],
  "warnings": ["..."],
  "ge_expectations_added": 0,
  "dbt_tests_added": 0,
  "sla_met": true,
  "files": [
    {"path": "...", "role": "ge_suite|dbt_test|quality_script|alert_config"}
  ]
}
```
