# Workflow: Cost Optimization

**Déclenché par :** `[INTENT:cost-optimization]` — mots-clés : "optimise les coûts", "réduis les coûts cloud", "trop cher AWS", "facture cloud", "optimise les tokens", "rightsizing", "coûts LLM", "burn rate trop élevé", "coût infrastructure"

**Agents impliqués :** cost-analyst → architect → devops-engineer

---

## Vue d'ensemble

```
Factures cloud + Usage actuel
          ↓
    [cost-analyst] — Audit complet
          ↓
   Infrastructure    LLM/API tokens    Storage/Network
   (compute, db,    (prompts, models,   (S3, CDN,
    cache, k8s)      caching strategy)   egress)
          ↓               ↓                  ↓
          └───────────────┴──────────────────┘
                          ↓
          Recommandations classées par ROI
                          ↓
          [architect] — Valide les changements
                          ↓
          [devops-engineer] — Implémente
                          ↓
          Budget alerts + Tagging + FinOps dashboard
```

---

## Étape 1 — Collecte des données de coût

### Cloud providers

```bash
# AWS — export des coûts du mois en cours
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "BlendedCost" "UnblendedCost" "UsageQuantity" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output table

# AWS — coûts par ressource (top 20)
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=RESOURCE_ID \
  --filter '{"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": ["'$AWS_ACCOUNT_ID'"]}}' \
  | jq '.ResultsByTime[].Groups | sort_by(.Metrics.BlendedCost.Amount | tonumber) | reverse | .[0:20]'

# GCP — export BigQuery billing
bq query --use_legacy_sql=false '
  SELECT service.description, SUM(cost) as total_cost
  FROM `billing_dataset.gcp_billing_export_v1_*`
  WHERE DATE(_PARTITIONTIME) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  GROUP BY 1
  ORDER BY 2 DESC
  LIMIT 20
'

# Azure
az consumption usage list \
  --billing-period-name $(date +%Y%m) \
  --query "sort_by([].{Service:instanceName, Cost:pretaxCost}, &Cost) | reverse([])" \
  -o table
```

### LLM / API tokens

```python
# Analyser les coûts Anthropic / OpenAI
import anthropic

# Estimer le coût d'une session type
PRICING = {
    # Anthropic ($/M tokens)
    "claude-opus-4-6":     {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-6":   {"input": 3.0,   "output": 15.0},
    "claude-haiku-4-5":    {"input": 0.8,   "output": 4.0},
    # OpenAI
    "gpt-4o":              {"input": 5.0,   "output": 15.0},
    "gpt-4o-mini":         {"input": 0.15,  "output": 0.6},
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, {"input": 0, "output": 0})
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000

# Analyser les logs d'utilisation
def analyze_token_usage(logs: list[dict]) -> dict:
    by_model = {}
    for entry in logs:
        model = entry["model"]
        if model not in by_model:
            by_model[model] = {"input_tokens": 0, "output_tokens": 0, "calls": 0}
        by_model[model]["input_tokens"] += entry.get("input_tokens", 0)
        by_model[model]["output_tokens"] += entry.get("output_tokens", 0)
        by_model[model]["calls"] += 1

    results = {}
    for model, usage in by_model.items():
        cost = estimate_cost(model, usage["input_tokens"], usage["output_tokens"])
        results[model] = {**usage, "estimated_cost_usd": round(cost, 4)}
    return results
```

---

## Étape 2 — Analyse par catégorie (cost-analyst)

**Invoquer l'agent cost-analyst** avec les données collectées.

### 2a — Compute (EC2/GKE/AKS/VMs)

```bash
# AWS — instances sous-utilisées (CPU < 10% sur 14j)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=$INSTANCE_ID \
  --start-time $(date -u -d "14 days ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 \
  --statistics Average \
  --query 'Datapoints[*].Average'

# Kubernetes — pods sous-utilisés
kubectl top pods --all-namespaces | sort -k4 -n  # par CPU
kubectl top nodes                                  # utilisation nodes
```

**Actions de rightsizing :**
```
CPU < 10% sur 14j → downsizer d'une taille (ex: t3.medium → t3.small)
CPU > 80% sur 14j → upsizer ou autoscaling
Instances prod toujours allumées → Reserved Instances (save 40-60%)
Workloads batch/non-critiques → Spot Instances (save 70-90%)
```

### 2b — Storage (S3/GCS/Azure Blob)

```bash
# AWS S3 — analyse des buckets par taille et coût
aws s3 ls --recursive s3://mon-bucket/ | awk '{print $3, $4}' | sort -rn | head -50

# Identifier les objets non-accédés depuis 90j (lifecycle)
aws s3api list-objects-v2 \
  --bucket mon-bucket \
  --query 'Contents[?LastModified<=`'"$(date -u -d '90 days ago' +%Y-%m-%dT%H:%M:%S)"'`].{Key:Key,Size:Size,LastModified:LastModified}' \
  --output table
```

**Lifecycle policies recommandées :**
```json
{
  "Rules": [{
    "Status": "Enabled",
    "Transitions": [
      {"Days": 30,  "StorageClass": "STANDARD_IA"},
      {"Days": 90,  "StorageClass": "GLACIER"},
      {"Days": 365, "StorageClass": "DEEP_ARCHIVE"}
    ],
    "Expiration": {"Days": 2555}  // 7 ans, adapter à la compliance
  }]
}
```

### 2c — Database (RDS/Cloud SQL/Azure SQL)

```sql
-- Identifier les requêtes les plus coûteuses (PostgreSQL)
SELECT
    query,
    calls,
    total_exec_time / 1000 as total_seconds,
    mean_exec_time / 1000 as mean_seconds,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Connexions inutilisées (trop de connexions = sur-dimensionnement)
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Index inutilisés (prennent de la place sans servir)
SELECT
    schemaname, tablename, indexname,
    idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Optimisations database :**
```
RDS Multi-AZ en dev/staging → désactiver (save ~50%)
RDS General Purpose SSD → migrer vers gp3 (save 20%)
RDS sous-utilisé → Aurora Serverless v2 (pay per use)
Connection pooling manquant → ajouter PgBouncer (réduit compute)
```

### 2d — LLM / Tokens

```python
# Stratégies d'optimisation par ordre de ROI

# 1. Caching sémantique (économie 30-70%)
from functools import lru_cache
import hashlib

def get_cache_key(prompt: str) -> str:
    """Hash normalisé pour caching."""
    normalized = " ".join(prompt.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()

# Redis semantic cache
async def cached_llm_call(prompt: str, **kwargs) -> str:
    cache_key = get_cache_key(prompt)
    cached = await redis.get(f"llm:{cache_key}")
    if cached:
        return cached.decode()

    response = await llm_call(prompt, **kwargs)
    await redis.setex(f"llm:{cache_key}", 3600, response)  # TTL 1h
    return response

# 2. Model routing (économie 60-80% sur les requêtes simples)
def route_to_model(task_complexity: str) -> str:
    """Router vers le modèle adapté à la complexité."""
    return {
        "simple": "claude-haiku-4-5",       # classification, extraction
        "medium": "claude-sonnet-4-6",       # résumé, Q&A, code simple
        "complex": "claude-opus-4-6",        # raisonnement, code complexe
    }.get(task_complexity, "claude-sonnet-4-6")

# 3. Prompt compression (économie 20-40%)
def compress_prompt(prompt: str, max_tokens: int = 2000) -> str:
    """Résumer le contexte si trop long."""
    tokens = estimate_tokens(prompt)
    if tokens > max_tokens:
        # Garder le début (instructions) + fin (question actuelle)
        lines = prompt.split('\n')
        head = '\n'.join(lines[:20])
        tail = '\n'.join(lines[-10:])
        return f"{head}\n[...contexte tronqué...]\n{tail}"
    return prompt

# 4. Batching (économie 15-30%)
async def batch_process(items: list[str], batch_size: int = 10) -> list[str]:
    """Traiter en batch plutôt qu'un par un."""
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        # Envoyer en parallèle avec asyncio.gather
        batch_results = await asyncio.gather(*[process_item(item) for item in batch])
        results.extend(batch_results)
    return results
```

---

## Étape 3 — Rapport de recommandations

Produire un rapport classé par ROI (économies annuelles estimées) :

```markdown
## Rapport d'optimisation des coûts — {projet} — {date}

### Coût actuel mensuel
| Catégorie | Coût actuel | Potentiel optimisé | Économie |
|-----------|-------------|-------------------|---------|
| Compute   | ${X}/mois   | ${Y}/mois         | {Z}%    |
| Storage   | ${X}/mois   | ${Y}/mois         | {Z}%    |
| Database  | ${X}/mois   | ${Y}/mois         | {Z}%    |
| LLM/APIs  | ${X}/mois   | ${Y}/mois         | {Z}%    |
| Network   | ${X}/mois   | ${Y}/mois         | {Z}%    |
| **TOTAL** | **${X}/mois** | **${Y}/mois** | **{Z}%** |

### Recommandations classées par ROI

#### 🔴 ROI > 40% — Agir immédiatement

1. **{recommandation}**
   - Économie estimée : ${X}/mois ({Y}%)
   - Effort : {S/M/L}
   - Risque : {LOW/MEDIUM/HIGH}
   - Action : {commande ou étape précise}

#### 🟡 ROI 20-40% — Planifier ce sprint

...

#### 🔵 ROI 10-20% — Backlog

...

### Budget alerts à configurer

{liste d'alertes budget recommandées}
```

---

## Étape 4 — Configuration des budget alerts

```bash
# AWS — alerte si coût mensuel > $X
aws budgets create-budget \
  --account-id $AWS_ACCOUNT_ID \
  --budget '{
    "BudgetName": "Monthly-Budget",
    "BudgetLimit": {"Amount": "500", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "'"$ALERT_EMAIL"'"}]
  }]'

# GCP
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=500USD \
  --threshold-rule=percent=0.8 \
  --all-updates-rule-pubsub-topic=projects/$PROJECT/topics/billing-alerts
```

---

## Étape 5 — Tagging obligatoire (FinOps)

Sans tagging, impossible d'allouer les coûts par équipe/feature.

```bash
# AWS — tagger toutes les ressources EC2 non-taguées
aws ec2 describe-instances \
  --query 'Reservations[].Instances[?!Tags[?Key==`cost-center`]].InstanceId' \
  --output text | xargs -I {} aws ec2 create-tags \
    --resources {} \
    --tags Key=cost-center,Value=UNKNOWN Key=env,Value=UNKNOWN

# Politique de tagging obligatoire (AWS Organizations SCP)
# Tags requis : env, team, project, cost-center
```

---

## CONTRAT DE SORTIE

```
COÛT ACTUEL: ${X}/mois
COÛT OPTIMISÉ ESTIMÉ: ${Y}/mois
ÉCONOMIES POTENTIELLES: {Z}% (~${diff}/mois, ${diff*12}/an)

RECOMMANDATIONS:
  ROI > 40%: {N} actions (implémenter immédiatement)
  ROI 20-40%: {N} actions (ce sprint)
  ROI < 20%: {N} actions (backlog)

BUDGET ALERTS: configurées à 80% et 100%
TAGGING: {N}% des ressources taguées (cible: 100%)

QUICK WINS IMPLÉMENTÉS:
  {liste des actions effectuées dans ce workflow}
```

**HANDOFF JSON :**
```json
{
  "current_monthly_cost_usd": 0,
  "optimized_monthly_cost_usd": 0,
  "savings_percent": 0,
  "savings_annual_usd": 0,
  "recommendations": [
    {"category": "compute", "action": "...", "savings_usd": 0, "effort": "S", "roi_pct": 0}
  ],
  "budget_alerts_configured": false,
  "tagging_coverage_pct": 0,
  "llm_cache_enabled": false,
  "model_routing_enabled": false
}
```
