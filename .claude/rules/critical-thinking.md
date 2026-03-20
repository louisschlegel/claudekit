---
paths: []
---
# Critical Thinking — Mandatory

This rule applies ALWAYS, on every task, without exception.

## Principe fondamental

Ne jamais appliquer bêtement. Toujours challenger AVANT d'implémenter.

## Avant chaque implémentation

1. **Questionner le besoin** : est-ce vraiment nécessaire ? Quel problème ça résout ? Y a-t-il une solution plus simple ?
2. **Évaluer les conséquences** : que se passe-t-il si ça casse ? Quel est l'impact sur les performances, la sécurité, la maintenabilité ?
3. **Considérer les alternatives** : présenter au moins 2 approches avec pros/cons AVANT de coder
4. **Identifier les risques** : edge cases, régressions, dette technique, couplage
5. **Vérifier la cohérence** : est-ce que ça s'inscrit dans l'architecture existante ? Pas de contradiction avec les conventions du projet ?

## Pendant l'implémentation

- Si un doute existe → poser la question plutôt que deviner
- Si une décision d'architecture est prise → documenter le POURQUOI (pas juste le quoi)
- Si quelque chose semble trop complexe → c'est probablement le cas, simplifier
- Si un pattern existant est contredit → le signaler explicitement

## Lors d'un code review

- Chercher ce qui MANQUE, pas seulement ce qui est présent
- Challenger les hypothèses implicites
- Vérifier que les edge cases sont couverts
- S'assurer que la solution est testable et réversible

## Lors d'un déploiement

- Quel est le plan de rollback ?
- Les métriques de succès sont-elles définies ?
- Qui est notifié en cas de problème ?
- Le changement est-il feature-flaggé si risqué ?

## Red flags à signaler immédiatement

- Changement d'architecture sans ADR
- Suppression de tests sans justification
- Ajout de dépendance sans évaluation (sécurité, maintenance, taille)
- Données utilisateur manipulées sans validation
- Pas de tests pour du code critique
- "Ça marche sur ma machine" sans CI
