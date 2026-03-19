---
name: loop-guard
description: Detect and break infinite correction loops — if same fix attempted 3 times, stop and rethink
triggers:
  - "je tourne en rond"
  - "stuck in loop"
  - "same error again"
  - "ça marche toujours pas"
---

# Skill: /loop-guard

Détecte et casse les boucles de correction infinies.

## Règles

1. Si la MÊME erreur apparaît 3 fois consécutives → STOP
2. Ne pas réessayer la même approche — changer de stratégie :
   - Lire le code source de la dépendance
   - Chercher des issues similaires sur GitHub
   - Essayer une approche complètement différente
   - Demander des clarifications à l'utilisateur
3. Si bloqué après changement de stratégie → `/clear` et reformuler le problème

## Signaux de boucle
- Même fichier édité 3+ fois en 5 minutes
- Même commande bash avec même erreur
- Test qui fail avec le même message
- Lint error qui revient après le fix

## Action
Quand une boucle est détectée :
1. S'arrêter immédiatement
2. Résumer ce qui a été essayé
3. Proposer 3 approches alternatives
4. Demander à l'utilisateur de choisir
