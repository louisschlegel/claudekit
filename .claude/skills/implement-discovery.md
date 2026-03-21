---
description: Implement an accepted feature from pending-features.md
triggers:
  - /implement-discovery
---

Implémente une feature acceptée depuis pending-features.md.

Usage: /implement-discovery <id>  (ex: /implement-discovery context7-mcp)

## Steps

1. **Lire pending-features.md** et trouver l'item dont le `id:` correspond à l'argument fourni.

2. **Analyser** la description et l'`implementation_hint` de l'item.

3. **Router vers le workflow approprié** selon la catégorie de l'item :

   | Catégorie | Action |
   |-----------|--------|
   | `hook`     | Créer le script hook dans `.claude/hooks/`, mettre à jour `settings.local.json` (section permissions/hooks) |
   | `mcp`      | Ajouter l'entrée dans `CLAUDE.md` (section MCP servers) et dans `.claude/docs/mcp-catalog.md` si existant |
   | `workflow` | Créer `workflows/<nom>.md` en suivant le format des workflows existants, mettre à jour `.claude/docs/workflows-table.md` |
   | `agent`    | Créer `.claude/agents/<nom>.md` en suivant le format des agents existants, mettre à jour `.claude/docs/agents-table.md` |
   | `skill`    | Créer `.claude/skills/<nom>.md` avec frontmatter `description` + `triggers` |
   | `cli`      | Documenter le flag/env var dans `.claude/rules/claude-code-env.md` |
   | `security` | Évaluer avec `devils-advocate` avant d'implémenter, puis ajouter dans `.claude/docs/security-layers.md` si pertinent |
   | `other`    | Analyser et choisir le meilleur emplacement selon la nature de la feature |

4. **Après implémentation** :
   - Déplacer l'item dans la section `## Implémenté` de `pending-features.md` (ajouter la date : `— done: YYYY-MM-DD`)
   - Mettre à jour `learning.md` avec le pattern ou la décision technique apprise
   - Lancer les tests ou un lint si applicable

## Règles

- Ne jamais implémenter sans avoir lu l'item complet et compris l'`implementation_hint`
- Pour les catégories `hook` ou `security` : invoquer `devils-advocate` avant de coder
- Pour les nouveaux agents ou workflows : lire un fichier existant du même type comme modèle avant d'écrire
- Si l'item semble incomplet ou ambigu : poser une question ciblée avant d'agir
- Solution minimale : ne pas sur-ingénierer, respecter le style existant du template
