---
name: configure
description: Modify claudekit settings via natural language — toggle hooks, add/remove MCP servers, change guards, etc.
effort: medium
user-invocable: true
triggers:
  - "désactive les notifs"
  - "active les notifs"
  - "disable notifications"
  - "enable notifications"
  - "désactive le lint"
  - "active le lint"
  - "ajoute le mcp"
  - "remove mcp"
  - "change la langue des commits"
  - "set commit language"
  - "désactive l'observabilité"
  - "active l'observabilité"
  - "configure claudekit"
  - "change les options"
  - "modifie le manifest"
---

# Skill: /configure

Interface naturelle pour modifier `project.manifest.json` et régénérer la config.

## Protocol

1. **Lire le manifest actuel** : `Read project.manifest.json`
2. **Identifier le changement** demandé
3. **Éditer `project.manifest.json`** avec la valeur correcte
4. **`manifest-regen.sh` se déclenche automatiquement** (hook PostToolUse) et régénère la config
5. **Confirmer** le changement appliqué

## Mappings naturel → manifest

| Demande | Champ manifest | Valeur |
|---------|---------------|--------|
| "désactive les notifs" | `automation.notifications` | `false` |
| "active les notifs" | `automation.notifications` | `true` |
| "désactive subagent logging" | `automation.subagent_logging` | `false` |
| "désactive observability" | `automation.observability` | `false` |
| "active le lint" | `guards.lint` | `true` |
| "désactive le lint" | `guards.lint` | `false` |
| "active type-check" | `guards.type_check` | `true` |
| "commits en français" | `workflow.commit_language` | `"fr"` |
| "commits en anglais" | `workflow.commit_language` | `"en"` |
| "ajoute MCP github" | `mcp_servers[]` | ajoute `"github"` |
| "retire MCP X" | `mcp_servers[]` | retire l'entrée |
| "self-improve toutes les 5 sessions" | `automation.self_improve_every_n_sessions` | `5` |
| "désactive les guards" | `guards.*` | tout à `false` |

## Exemple

Utilisateur : "désactive les notifications et active le type-check"

```
1. Read project.manifest.json
2. Edit: automation.notifications → false, guards.type_check → true
3. manifest-regen.sh se déclenche → settings.local.json régénéré
4. "✓ Notifications désactivées, type-check activé. Config régénérée."
```

## Note

Après un changement de `mcp_servers[]`, un **redémarrage de Claude Code** est nécessaire pour que les nouveaux serveurs MCP soient chargés.
