---
name: brainstorming
description: Structured Socratic dialogue to refine rough ideas into concrete designs — explore alternatives, challenge assumptions, present in digestible sections
effort: high
user-invocable: true
triggers:
  - "brainstorm"
  - "réfléchis à"
  - "explore les options"
  - "design session"
  - "think through"
  - "j'ai une idée"
  - "let's brainstorm"
---

# Skill: /brainstorm

Dialogue socratique structuré pour transformer une idée brute en design concret.

## Protocole

### Phase 1 — Comprendre l'idée (pas de jugement)
1. Écouter l'idée initiale sans interrompre
2. Reformuler pour confirmer la compréhension
3. Poser 3 questions de clarification :
   - Quel problème ça résout ? Pour qui ?
   - Quelles sont les contraintes (temps, budget, stack) ?
   - À quoi ressemble le succès ?

### Phase 2 — Explorer les alternatives
Pour chaque aspect clé, présenter au moins 3 approches :
1. **L'approche évidente** — ce qui vient naturellement
2. **L'approche minimaliste** — le MVP absolu
3. **L'approche créative** — quelque chose de non conventionnel

Pour chaque approche :
- Avantages / inconvénients
- Complexité estimée (jours/semaines)
- Risques principaux

### Phase 3 — Challenger (via devils-advocate)
- "Que se passe-t-il si cette hypothèse est fausse ?"
- "Qui d'autre a résolu ce problème et comment ?"
- "Qu'est-ce qu'on va regretter dans 6 mois ?"

### Phase 4 — Converger
1. Synthétiser les meilleures idées de chaque approche
2. Proposer un design hybride
3. Présenter en sections digestes :
   - Vue d'ensemble (1 paragraphe)
   - Architecture (composants + flux)
   - Trade-offs acceptés (et pourquoi)
   - Prochaines étapes concrètes
4. Sauvegarder dans `docs/design/` ou créer un ADR

### Phase 5 — Valider
- "Est-ce que ça répond au problème initial ?"
- "Est-ce qu'on peut commencer avec la moitié de ça ?"
- "Qu'est-ce qui doit être décidé MAINTENANT vs plus tard ?"

## Output
Design document ou ADR avec les décisions et alternatives explorées.
