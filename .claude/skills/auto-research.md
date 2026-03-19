---
name: auto-research
description: Self-improving skill loop — run against eval criteria, analyze failures, improve, re-test
triggers:
  - "améliore cette skill"
  - "eval cette skill"
  - "self-improve skill"
  - "test and improve"
  - "autoResearch"
---

# Skill: /auto-research

Implémente le pattern AutoResearch : les skills avec des critères d'évaluation binaires s'améliorent automatiquement.

## Protocole

1. **Définir les critères** : assertions PASS/FAIL explicites pour l'output de la skill
2. **Exécuter** la skill sur 3-5 cas de test
3. **Évaluer** chaque output (binaire : pass/fail)
4. **Analyser les échecs** : identifier les patterns dans ce qui a échoué et pourquoi
5. **Proposer l'amélioration** : réécrire la skill avec les corrections
6. **Re-tester** : exécuter à nouveau, comparer le taux de réussite
7. **Accepter si meilleur** : sauvegarder la version améliorée si le taux augmente

## Format des critères d'évaluation

Ajouter au frontmatter YAML de n'importe quelle skill :
```yaml
eval_criteria:
  - "output contient un chemin de fichier concret"
  - "output ne contient pas 'je ne peux pas'"
  - "output fait moins de 500 mots"
  - "output inclut un exemple de code"
  - "output a un HANDOFF JSON valide"
```

## Exemple

"Améliore la skill code-review en testant sur 3 PRs récentes"

1. Lire `.claude/skills/code-review.md` et ses `eval_criteria`
2. Identifier 3 PRs récentes (`git log --merges -3`)
3. Exécuter code-review sur chaque PR
4. Évaluer contre les critères → score: 2/3 pass
5. Analyser l'échec : "PR #8 n'a pas produit de suggestions de sécurité"
6. Améliorer : ajouter une section sécurité obligatoire
7. Re-tester → score: 3/3 pass → sauvegarder

## Output

```json
{
  "skill": "code-review",
  "pass_rate_before": "66%",
  "pass_rate_after": "100%",
  "improvements": ["Added mandatory security review section"],
  "test_cases": 3,
  "accepted": true
}
```
