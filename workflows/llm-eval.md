# Workflow: LLM Evaluation

**Déclenché par :** `[INTENT:llm-eval]` — mots-clés : "évalue le rag", "llm eval", "ragas", "qualité des réponses", "hallucination", "benchmark llm", "evaluer le modèle", "rag evaluation"

**Agents impliqués :** ml-engineer → tester → reviewer

---

## Vue d'ensemble

```
Jeu d'évaluation → Métriques automatiques → Human eval → Score global
        ↓                     ↓                   ↓
  Golden dataset         RAGAS / BLEU         Crowdsourcing
        ↓                     ↓                   ↓
        └─────────────────────┴───────────────────┘
                              ↓
                    Rapport + décision (deploy/iterate)
```

---

## Étape 1 — Construire le jeu d'évaluation (golden dataset)

```python
# eval_dataset.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class EvalSample:
    question: str
    ground_truth: str           # Réponse de référence (human-written)
    contexts: list[str]         # Documents récupérés (pour RAG)
    answer: Optional[str] = None  # Réponse générée (rempli lors de l'éval)
    metadata: dict = None

# Règles pour un bon golden dataset :
# - Minimum 50 samples pour des métriques stables (200+ recommandé)
# - Couvrir les cas limites : questions ambiguës, hors-domaine, multi-hop
# - Distribuer sur tous les topics/catégories du domaine
# - Inclure des questions sans réponse dans le corpus (pour tester le refus)
# - Ground truth rédigé par des experts domaine
```

**Sources de données d'évaluation :**
```python
# Option 1 : Annoter manuellement (gold standard)
# Option 2 : LLM-as-judge pour créer le dataset initial
# Option 3 : Questions réelles des utilisateurs + validation humaine

from anthropic import Anthropic

def generate_eval_questions(corpus: str, n: int = 50) -> list[EvalSample]:
    """Génère des questions d'éval depuis le corpus via LLM."""
    client = Anthropic()
    prompt = f"""
    From this corpus, generate {n} diverse evaluation questions with ground truth answers.
    Cover: factual, reasoning, edge cases, and out-of-scope questions.

    Corpus: {corpus[:3000]}

    Return JSON array: [{{"question": "...", "ground_truth": "...", "type": "factual|reasoning|edge|out-of-scope"}}]
    """
    # ... parse response
```

---

## Étape 2 — Métriques automatiques RAG (RAGAS)

```python
# ragas_eval.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,        # La réponse est-elle fidèle aux documents récupérés ?
    answer_relevancy,   # La réponse répond-elle à la question ?
    context_precision,  # Les documents récupérés sont-ils pertinents ?
    context_recall,     # Le contexte contient-il l'info pour répondre ?
    answer_correctness, # La réponse est-elle correcte vs ground truth ?
)
from datasets import Dataset

# Préparer le dataset RAGAS
data = {
    "question": [s.question for s in eval_samples],
    "answer": [s.answer for s in eval_samples],
    "contexts": [s.contexts for s in eval_samples],
    "ground_truth": [s.ground_truth for s in eval_samples],
}
dataset = Dataset.from_dict(data)

# Évaluer
results = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness],
)

print(results)
# Output:
# faithfulness        : 0.92
# answer_relevancy    : 0.87
# context_precision   : 0.78
# context_recall      : 0.83
# answer_correctness  : 0.81
```

---

## Étape 3 — Détection des hallucinations

```python
# hallucination_detector.py
from anthropic import Anthropic

client = Anthropic()

def check_hallucination(question: str, context: str, answer: str) -> dict:
    """LLM-as-judge pour détecter les hallucinations."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""You are a factual accuracy judge.

Question: {question}
Context provided: {context}
Answer given: {answer}

Is the answer:
1. FAITHFUL - fully supported by the context
2. PARTIAL - mostly supported but contains unsupported claims
3. HALLUCINATED - contains significant claims not in the context

Respond with JSON: {{"verdict": "FAITHFUL|PARTIAL|HALLUCINATED", "unsupported_claims": ["..."], "confidence": 0.0}}"""
        }]
    )
    import json
    return json.loads(response.content[0].text)

# Batch evaluation
hallucination_results = [
    check_hallucination(s.question, "\n".join(s.contexts), s.answer)
    for s in eval_samples
]

hallucination_rate = sum(
    1 for r in hallucination_results if r["verdict"] == "HALLUCINATED"
) / len(hallucination_results)
print(f"Hallucination rate: {hallucination_rate:.1%}")
```

---

## Étape 4 — Métriques NLP classiques

```python
# nlp_metrics.py
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import nltk

nltk.download('punkt', quiet=True)
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

def compute_metrics(references: list[str], hypotheses: list[str]) -> dict:
    bleu_scores, rouge_scores = [], {"rouge1": [], "rouge2": [], "rougeL": []}
    smoothie = SmoothingFunction().method4

    for ref, hyp in zip(references, hypotheses):
        # BLEU
        ref_tokens = nltk.word_tokenize(ref.lower())
        hyp_tokens = nltk.word_tokenize(hyp.lower())
        bleu_scores.append(sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=smoothie))

        # ROUGE
        scores = scorer.score(ref, hyp)
        for metric in rouge_scores:
            rouge_scores[metric].append(scores[metric].fmeasure)

    return {
        "bleu": round(sum(bleu_scores) / len(bleu_scores), 4),
        "rouge1": round(sum(rouge_scores["rouge1"]) / len(rouge_scores["rouge1"]), 4),
        "rouge2": round(sum(rouge_scores["rouge2"]) / len(rouge_scores["rouge2"]), 4),
        "rougeL": round(sum(rouge_scores["rougeL"]) / len(rouge_scores["rougeL"]), 4),
    }
```

---

## Étape 5 — Human evaluation

```python
# human_eval_template.py
# Interface simplifiée pour l'évaluation humaine (peut être un CSV ou Streamlit app)

EVAL_CRITERIA = {
    "accuracy": "Is the answer factually correct? (1-5)",
    "completeness": "Does the answer cover all aspects of the question? (1-5)",
    "clarity": "Is the answer clear and well-written? (1-5)",
    "faithfulness": "Is the answer grounded in the provided context? (1-5)",
    "safety": "Does the answer contain harmful/biased content? (1=yes, 5=no)",
}

# Minimum 3 annotateurs pour fiabilité inter-annotateur
# Calculer Cohen's Kappa ou Fleiss' Kappa pour mesurer l'accord
from sklearn.metrics import cohen_kappa_score

kappa = cohen_kappa_score(annotator_1_scores, annotator_2_scores)
print(f"Inter-annotator agreement (Cohen's κ): {kappa:.3f}")
# κ > 0.6 = bon accord, κ > 0.8 = excellent
```

---

## Étape 6 — Rapport et décision de déploiement

**Seuils de déploiement recommandés :**

| Métrique | Minimum | Cible |
|----------|---------|-------|
| Faithfulness (RAGAS) | 0.85 | > 0.90 |
| Answer Relevancy | 0.80 | > 0.85 |
| Context Precision | 0.75 | > 0.80 |
| Hallucination Rate | < 5% | < 2% |
| Human Accuracy | > 3.5/5 | > 4.0/5 |
| Latency p95 | < 5s | < 2s |

```python
# deploy_gate.py
def check_deploy_gate(metrics: dict) -> tuple[bool, list[str]]:
    """Vérifie si les métriques permettent le déploiement."""
    failures = []

    if metrics.get("faithfulness", 0) < 0.85:
        failures.append(f"Faithfulness {metrics['faithfulness']:.2f} < 0.85")
    if metrics.get("hallucination_rate", 1) > 0.05:
        failures.append(f"Hallucination rate {metrics['hallucination_rate']:.1%} > 5%")
    if metrics.get("answer_relevancy", 0) < 0.80:
        failures.append(f"Answer relevancy {metrics['answer_relevancy']:.2f} < 0.80")

    return len(failures) == 0, failures

can_deploy, reasons = check_deploy_gate(eval_results)
if not can_deploy:
    print("DEPLOY BLOCKED:")
    for r in reasons: print(f"  - {r}")
```

---

## CONTRAT DE SORTIE

```
MODEL/RAG SYSTEM: [nom + version]
EVAL DATASET: [N samples, sources]

RAGAS METRICS:
  Faithfulness:      X.XX
  Answer Relevancy:  X.XX
  Context Precision: X.XX
  Context Recall:    X.XX
  Answer Correctness:X.XX

NLP METRICS:
  BLEU:   X.XX
  ROUGE-L: X.XX

HALLUCINATION:
  Rate: X.X%
  Examples: [3 pires cas]

HUMAN EVAL:
  Accuracy:     X.X/5
  Completeness: X.X/5
  Fleiss κ:     X.XX

DEPLOY GATE: PASS | FAIL
BLOCKERS: [si fail]

FILES TO CREATE/MODIFY:
  [liste]
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "model": "...",
  "eval_samples": 0,
  "ragas": {
    "faithfulness": 0.0,
    "answer_relevancy": 0.0,
    "context_precision": 0.0,
    "context_recall": 0.0,
    "answer_correctness": 0.0
  },
  "hallucination_rate": 0.0,
  "bleu": 0.0,
  "rouge_l": 0.0,
  "human_accuracy": 0.0,
  "inter_annotator_kappa": 0.0,
  "deploy_gate": "pass|fail",
  "blockers": ["..."],
  "latency_p95_ms": 0,
  "files": [
    {"path": "...", "role": "eval_dataset|ragas_suite|human_eval|deploy_gate"}
  ]
}
```
