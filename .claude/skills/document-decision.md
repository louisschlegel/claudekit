---
name: document-decision
description: Document a technical decision with rationale, alternatives, and consequences — auto-creates ADR + updates relevant docs
effort: medium
user-invocable: true
triggers:
  - "documente cette décision"
  - "document this decision"
  - "create adr"
  - "pourquoi ce choix"
  - "decision record"
  - "documente l'architecture"
---

# Skill: /document-decision

Documenter une décision technique avec contexte, alternatives, et conséquences.

## Protocole

1. **Identifier la décision** : quelle question technique a été tranchée ?
2. **Documenter** via `/generate-adr` :
   - Contexte : pourquoi cette question se pose maintenant
   - Décision : ce qui a été choisi
   - Alternatives : ce qui a été considéré et rejeté (avec raisons)
   - Conséquences : positives, négatives, neutres
3. **Mettre à jour les fichiers impactés** :
   - `learning.md` : ajouter le pattern si applicable
   - `CHANGELOG.md` : ajouter sous `[Unreleased]` si visible par l'utilisateur
   - `README.md` : mettre à jour si l'interface publique change
   - Code comments : ajouter un `// ADR-XXX: <raison>` au code impacté
4. **Vérifier la cohérence** :
   - La décision ne contredit pas un ADR existant ?
   - Les custom_rules du manifest sont cohérentes ?

## Quand utiliser cette skill

- Choix de technologie (DB, framework, lib)
- Changement d'architecture (monolith → microservices, REST → GraphQL)
- Pattern de design (event sourcing, CQRS, saga)
- Stratégie de déploiement (blue-green, canary, rolling)
- Choix de sécurité (auth method, encryption, key management)

## Output

- ADR créé dans `docs/architecture/adr-XXX-<titre>.md`
- Fichiers connexes mis à jour
- Référence ADR ajoutée dans le code si applicable
