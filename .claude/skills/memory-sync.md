---
name: memory-sync
description: Promote stable patterns from learning.md into CLAUDE.md custom_rules when seen 3+ times
triggers:
  - "sync la mémoire"
  - "consolide les patterns"
  - "memory sync"
  - "promote patterns"
---

# Skill: /memory-sync

Promeut les patterns stables de `learning.md` dans les `custom_rules` du manifest.

## Protocole

1. **Lire `learning.md`** — trouver les patterns qui apparaissent 3+ fois ou sont marqués high-confidence
2. **Vérifier** si déjà dans `project.manifest.json` > `context.custom_rules[]`
3. **Pour chaque nouveau pattern** : proposer l'ajout à `custom_rules`
4. **Utilisateur confirme** → écrire dans `project.manifest.json` → `manifest-regen.sh` auto-regen
5. **Marquer** les entrées promues dans `learning.md` (ou les supprimer)

## Heuristiques de promotion

- Pattern mentionné 3+ fois dans learning.md → candidat promotion
- Pattern avec `confidence: high` dans auto-learn → candidat
- Corrections de l'approche de Claude répétées 2+ fois → signal fort
- Pattern validé explicitement par l'utilisateur ("oui c'est la bonne approche")

## Ce qu'on NE promeut PAS

- Solutions spécifiques à un bug (le fix est dans le code)
- Chemins de fichiers ou noms de fonctions (changent trop vite)
- Historique git ou activité récente (éphémère)
- Tout ce qui est déjà dans CLAUDE.md

## Output

```
Patterns promus (3) :
  ✓ "Toujours utiliser des UUID v7 pour les primary keys" → custom_rules
  ✓ "Préférer les cursor-based pagination aux offsets" → custom_rules
  ✓ "Ne jamais logger les tokens/secrets même en debug" → custom_rules

Entrées nettoyées dans learning.md : 9 lignes supprimées
Config régénérée automatiquement.
```
