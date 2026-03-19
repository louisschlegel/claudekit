---
name: review-architecture
description: Deep architecture review — challenge every design decision with trade-off analysis
effort: high
user-invocable: true
triggers:
  - "review architecture"
  - "critique l'architecture"
  - "review the design"
  - "analyse l'architecture"
  - "architecture review"
---

# Skill: /review-architecture

Revue d'architecture approfondie avec analyse de trade-offs.

## Protocol

1. **Cartographier** l'architecture actuelle :
   - Composants et leurs responsabilités
   - Flux de données (qui parle à qui, comment)
   - Points de défaillance (single points of failure)
   - Dépendances externes

2. **Challenger chaque composant** :
   - Est-il nécessaire ? Peut-on le supprimer/simplifier ?
   - Est-il au bon niveau d'abstraction ?
   - Respecte-t-il le Single Responsibility Principle ?
   - Est-il testable de manière isolée ?

3. **Analyser les trade-offs** :
   Pour chaque décision architecturale majeure :
   ```
   Décision : [ex: PostgreSQL vs MongoDB]
   Avantages : [...]
   Inconvénients : [...]
   Alternatives considérées : [...]
   Contexte de la décision : [pourquoi ce choix à ce moment]
   Toujours valide ? [oui/non + justification]
   ```

4. **Identifier les patterns problématiques** :
   - God service (fait trop de choses)
   - Distributed monolith (microservices sans les bénéfices)
   - Shared mutable state
   - Circular dependencies
   - Missing boundaries
   - Over-abstraction

5. **Recommandations** :
   Pour chaque finding :
   - Impact : HIGH/MEDIUM/LOW
   - Effort de correction : jours/semaines/mois
   - Urgence : maintenant/prochain sprint/backlog
   - Proposition concrète (pas juste "il faudrait améliorer")

## Output

ADR (Architecture Decision Record) pour chaque recommandation acceptée.
