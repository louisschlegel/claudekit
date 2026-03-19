---
name: premortem
description: Imagine the project has failed — work backwards to identify what went wrong and prevent it
effort: medium
user-invocable: true
triggers:
  - "premortem"
  - "pré-mortem"
  - "what could go wrong"
  - "risk analysis"
  - "analyse de risques"
  - "challenge this"
  - "critique ça"
  - "devil's advocate"
---

# Skill: /premortem

Exercice de pré-mortem : imaginer que le projet/feature a ÉCHOUÉ, puis identifier pourquoi.

## Protocole

### Étape 1 — Définir le scénario
"On est dans 3 mois. Cette feature est un échec. Les utilisateurs ne l'utilisent pas / elle casse en prod / elle est impossible à maintenir. Pourquoi ?"

### Étape 2 — Lister les causes d'échec
Chaque participant (ou Claude) génère au moins 5 raisons d'échec :
- **Techniques** : performance, sécurité, scalabilité, bugs
- **Architecture** : couplage, complexité, dette technique
- **Produit** : mauvaise UX, feature pas utilisée, pas de feedback loop
- **Opérationnel** : déploiement raté, pas de monitoring, pas de rollback
- **Humain** : bus factor, documentation manquante, onboarding impossible

### Étape 3 — Classer par probabilité × impact

| Risque | Probabilité | Impact | Score | Action |
|--------|------------|--------|-------|--------|
| ...    | HIGH       | HIGH   | 🔴    | BLOQUER et résoudre |
| ...    | MEDIUM     | HIGH   | 🟡    | Mitiger avant de lancer |
| ...    | LOW        | HIGH   | 🟡    | Plan de contingence |
| ...    | *          | LOW    | 🟢    | Accepter le risque |

### Étape 4 — Actions préventives
Pour chaque risque 🔴 et 🟡 :
1. Action concrète pour prévenir
2. Owner et deadline
3. Critère de succès (comment sait-on que le risque est mitigé ?)

## Output

Produit un document structuré avec tous les risques identifiés et les actions préventives.
S'utilise AVANT de commencer l'implémentation, pas après.
