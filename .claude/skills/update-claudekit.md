---
name: update-claudekit
description: Check for claudekit updates and apply them to the current project
effort: medium
user-invocable: true
triggers:
  - "update claudekit"
  - "mets à jour claudekit"
  - "update template"
  - "nouvelle version claudekit"
  - "upgrade claudekit"
---

# Skill: /update-claudekit

Vérifie si une nouvelle version de claudekit est disponible et l'applique.

## Protocole

1. **Lire** la version actuelle : `.template/version.json` > `version`
2. **Vérifier** la dernière version sur GitHub :
   ```bash
   curl -fsSL https://api.github.com/repos/louisschlegel/claudekit/releases/latest | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])"
   ```
3. **Comparer** les versions. Si mise à jour disponible :
4. **Afficher** le changelog de la release (features, fixes, breaking changes)
5. **Demander** confirmation à l'utilisateur
6. **Appliquer** la mise à jour :
   ```bash
   curl -fsSL https://raw.githubusercontent.com/louisschlegel/claudekit/main/install.sh | bash
   ```
   Ou si le repo est cloné :
   ```bash
   cd /path/to/claudekit && git pull && bash install.sh /path/to/project
   ```
7. **Après install** :
   - `python3 scripts/migrate-template.py` — migre le manifest si nécessaire
   - `python3 scripts/gen.py` — régénère la config
   - Vérifier que `make validate` passe
8. **Informer** l'utilisateur de redémarrer Claude Code

## Ce qui est préservé lors de la mise à jour
- ✅ `project.manifest.json` — jamais écrasé
- ✅ `learning.md` — jamais touché
- ✅ Agents custom (noms différents des agents claudekit) — préservés
- ✅ Workflows custom — préservés
- ✅ Hooks custom — préservés
- ✅ `.claude/settings.local.json` — géré par gen.py, pas par install.sh
- ✅ `.mcp.json` — géré par gen.py

## Ce qui est mis à jour
- 🔄 Scripts (`scripts/*.py`) — toujours remplacés
- 🔄 Hooks claudekit (`session-start.sh`, etc.) — toujours remplacés
- 🔄 `CLAUDE.md` — remplacé (backup en `.bak` si différent)
- 🔄 `.template/version.json` — mis à jour

## Vérification automatique au démarrage
`session-start.sh` vérifie la dernière version toutes les 24h (cache dans `.template/update-check.json`).
Si une mise à jour est disponible, un message s'affiche dans le contexte de session.
