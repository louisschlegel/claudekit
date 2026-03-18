# Workflow: A/B Test

**Déclenché par :** `[INTENT:ab-test]` — mots-clés : "a/b test", "feature flag", "expérimentation", "rollout progressif", "split test", "statistical significance"

**Agents impliqués :** architect → tester → reviewer → deployer

---

## Vue d'ensemble

```
Feature flag défini → Variante B implémentée → Tests → Rollout progressif
       ↓                                                        ↓
  Allocation traffic                                   Analyse statistique
       ↓                                                        ↓
  Métriques collectées ──────────────────────────→ Décision (ship/kill)
```

---

## Étape 1 — Définir l'expérience

Avant tout code, répondre à ces questions :

```
HYPOTHÈSE : "Changer X augmentera Y de Z%"
MÉTRIQUE PRINCIPALE : [conversion / retention / latence / revenue]
MÉTRIQUES SECONDAIRES : [impacts collatéraux à surveiller]
TAILLE D'ÉCHANTILLON : [calculer avec power analysis]
DURÉE MINIMALE : [au moins 1 cycle business complet, min 7 jours]
CRITÈRE DE SUCCÈS : [p-value < 0.05, minimum detectable effect = X%]
CRITÈRE D'ARRÊT : [dégradation > Y% → rollback immédiat]
```

**Power analysis (Python) :**
```python
from scipy import stats
import numpy as np

def required_sample_size(baseline_rate, mde, alpha=0.05, power=0.8):
    """
    baseline_rate : taux actuel (ex: 0.05 = 5% conversion)
    mde : minimum detectable effect relatif (ex: 0.10 = +10%)
    """
    effect_size = (baseline_rate * (1 + mde) - baseline_rate) / \
                  np.sqrt(baseline_rate * (1 - baseline_rate))
    analysis = stats.TTestIndPower()
    n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power)
    return int(np.ceil(n))

# Exemple : 5% baseline, détecter +10%, α=0.05, power=80%
n = required_sample_size(0.05, 0.10)
print(f"Taille par variante : {n} utilisateurs")
```

---

## Étape 2 — Implémenter le feature flag

**Invoquer `architect`** pour choisir la stratégie :

```python
# Option A : Feature flag in-app (simple)
def get_variant(user_id: str, flag: str, traffic_pct: float = 0.5) -> str:
    import hashlib
    h = int(hashlib.md5(f"{user_id}:{flag}".encode()).hexdigest(), 16)
    return "B" if (h % 100) < (traffic_pct * 100) else "A"

# Option B : LaunchDarkly / Unleash / Flipt (recommandé en prod)
import ldclient
variation = ldclient.get().variation("feature-flag-key", user_context, False)

# Option C : Environnement variable (déploiements blue/green)
import os
VARIANT = os.getenv("AB_VARIANT", "A")
```

**Structure recommandée :**
```python
# feature_flags.py
from dataclasses import dataclass
from typing import Literal

@dataclass
class ExperimentConfig:
    name: str
    variants: list[str]
    traffic_split: dict[str, float]  # {"A": 0.5, "B": 0.5}
    metrics: list[str]
    min_sample_size: int
    start_date: str
    end_date: str | None = None

EXPERIMENTS = {
    "checkout-button-color": ExperimentConfig(
        name="checkout-button-color",
        variants=["A", "B"],
        traffic_split={"A": 0.5, "B": 0.5},
        metrics=["conversion_rate", "checkout_time_ms"],
        min_sample_size=1000,
        start_date="2024-01-01",
    )
}
```

---

## Étape 3 — Instrumenter les métriques

**Invoquer `tester`** pour valider l'instrumentation :

```python
# events.py — tracking des événements d'expérience
def track_experiment_exposure(user_id: str, experiment: str, variant: str):
    analytics.track(user_id, "experiment_exposure", {
        "experiment_name": experiment,
        "variant": variant,
        "timestamp": datetime.utcnow().isoformat(),
    })

def track_conversion(user_id: str, experiment: str, metric: str, value: float = 1.0):
    analytics.track(user_id, "experiment_conversion", {
        "experiment_name": experiment,
        "metric": metric,
        "value": value,
        "timestamp": datetime.utcnow().isoformat(),
    })
```

**Gate qualité :**
- [ ] L'exposition est loggée avant que l'utilisateur voie la variante
- [ ] Pas de double exposition (même utilisateur voit toujours la même variante)
- [ ] Les events incluent `user_id`, `experiment_name`, `variant`, `timestamp`

---

## Étape 4 — Rollout progressif

**Invoquer `deployer`** avec la stratégie de déploiement :

```
Phase 1 : 5% du trafic → B  (2-4h, watch for errors)
Phase 2 : 20% du trafic → B (24h, monitor metrics)
Phase 3 : 50% du trafic → B (durée min pour significance)
Phase 4 : décision → ship (100%) ou kill (0%)
```

**Critères de rollback immédiat :**
- Error rate > baseline + 1%
- p99 latency > baseline * 1.5
- Crash rate augmente
- Métrique principale dégrade > seuil d'arrêt défini à l'étape 1

---

## Étape 5 — Analyse statistique

```python
# analyse_ab.py
import numpy as np
from scipy import stats

def analyze_experiment(
    control_conversions: int, control_total: int,
    treatment_conversions: int, treatment_total: int,
    alpha: float = 0.05
) -> dict:
    p_control = control_conversions / control_total
    p_treatment = treatment_conversions / treatment_total

    # Z-test pour proportions
    z_stat, p_value = stats.proportions_ztest(
        [treatment_conversions, control_conversions],
        [treatment_total, control_total]
    )

    relative_lift = (p_treatment - p_control) / p_control * 100

    # Intervalle de confiance 95%
    se = np.sqrt(p_control*(1-p_control)/control_total + p_treatment*(1-p_treatment)/treatment_total)
    ci_low = (p_treatment - p_control) - 1.96 * se
    ci_high = (p_treatment - p_control) + 1.96 * se

    return {
        "control_rate": round(p_control, 4),
        "treatment_rate": round(p_treatment, 4),
        "relative_lift_pct": round(relative_lift, 2),
        "p_value": round(p_value, 4),
        "significant": p_value < alpha,
        "ci_95": [round(ci_low, 4), round(ci_high, 4)],
        "recommendation": "ship" if p_value < alpha and relative_lift > 0 else
                         "kill" if p_value < alpha and relative_lift < 0 else
                         "continue"
    }
```

---

## Étape 6 — Décision et cleanup

**Si `ship` :**
1. Ramp to 100%
2. Supprimer le flag et le code de l'ancienne variante A
3. Documenter le résultat dans `learning.md`

**Si `kill` :**
1. Ramp to 0% (rollback complet)
2. Post-mortem : pourquoi l'hypothèse était fausse ?
3. Documenter dans `learning.md`

**Si `continue` :**
1. Vérifier que la durée minimale est atteinte
2. Vérifier la taille d'échantillon
3. Étendre la durée si nécessaire

**Cleanup obligatoire :**
```python
# Après décision : supprimer tous les vestiges du flag
# - Code de branchement (if variant == "A": ...)
# - Config du flag dans le feature flag service
# - Tables/colonnes d'événements analytics si plus nécessaires
# → Invoquer reviewer pour vérifier qu'aucun vestige ne reste
```

---

## CONTRAT DE SORTIE

```
EXPERIMENT: [nom]
HYPOTHESIS: [texte]

RESULTS:
  Control (A): [N] users, [X]% conversion
  Treatment (B): [N] users, [X]% conversion
  Relative lift: [+/-X]%
  p-value: [X] (significant: oui/non)
  95% CI: [low, high]

DECISION: ship | kill | continue
RATIONALE: [explication]

CLEANUP:
  Flag removed: oui/non
  Code cleaned: oui/non
  learning.md updated: oui/non
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "experiment": "...",
  "variant_a_rate": 0.0,
  "variant_b_rate": 0.0,
  "relative_lift_pct": 0.0,
  "p_value": 0.0,
  "significant": false,
  "decision": "ship|kill|continue",
  "sample_size_a": 0,
  "sample_size_b": 0,
  "duration_days": 0,
  "flag_cleaned_up": false,
  "files_modified": ["..."]
}
```
