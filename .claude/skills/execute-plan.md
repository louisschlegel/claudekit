---
name: execute-plan
description: Batch execution of a plan with human checkpoints — each task is small (2-5 min), verified, and committed before moving to the next
effort: high
user-invocable: true
triggers:
  - "exécute le plan"
  - "execute the plan"
  - "lance le plan"
  - "run the plan"
  - "implémente le plan"
  - "batch execute"
---

# Skill: /execute-plan

Exécution batch d'un plan avec checkpoints humains.

## Protocole

### 1. Lire le plan
- Lire le fichier plan (`.template/plan.md`, ADR, ou le plan dans le contexte)
- Extraire les tâches individuelles
- Vérifier que chaque tâche est atomique (2-5 min max)
- Si une tâche est trop grosse → la découper

### 2. Présenter le plan d'exécution
```
📋 Plan d'exécution — <nom>
━━━━━━━━━━━━━━━━━━━━━━━━
□ 1. [Tâche 1] (~3 min)
□ 2. [Tâche 2] (~2 min)
□ 3. [Tâche 3] (~5 min)
  ⟶ CHECKPOINT : validation humaine
□ 4. [Tâche 4] (~3 min)
□ 5. [Tâche 5] (~4 min)
  ⟶ CHECKPOINT : validation humaine

Total : 5 tâches, ~17 min estimé
```

Demander confirmation avant de commencer.

### 3. Exécuter tâche par tâche
Pour chaque tâche :
1. Annoncer la tâche en cours
2. Implémenter (code minimal, test first si TDD activé)
3. Vérifier : tests passent, lint OK, pas de régression
4. Résumer ce qui a été fait
5. Passer à la suivante

### 4. Checkpoints humains
À chaque checkpoint (toutes les 2-3 tâches) :
- Résumer ce qui a été fait
- Montrer les fichiers modifiés
- Demander validation avant de continuer
- L'utilisateur peut : continuer, corriger, arrêter, replanifier

### 5. Finaliser
- Résumé complet des tâches exécutées
- Tests finaux (tous doivent passer)
- Proposer un commit avec message descriptif
- Mettre à jour learning.md si des patterns ont été découverts

## Règles
- Jamais plus de 5 min par tâche — si ça prend plus, stopper et redécouper
- Chaque tâche doit être vérifiable indépendamment
- Un checkpoint au minimum toutes les 3 tâches
- Si un test échoue → corriger AVANT de passer à la suite (pas de dette)
