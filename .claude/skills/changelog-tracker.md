---
name: changelog-tracker
description: Fetch and analyze Claude Code changelog to identify new features to integrate into claudekit
effort: low
user-invocable: true
triggers:
  - "check changelog"
  - "update from changelog"
  - "new claude code features"
  - "what's new in claude code"
  - "changelog claude code"
  - "mets à jour depuis le changelog"
---

# Skill: /changelog-tracker

Récupère le changelog Claude Code et identifie les nouvelles features à intégrer dans claudekit.

## Protocole

1. **Fetch** le changelog : `https://code.claude.com/docs/en/changelog`
2. **Comparer** avec la version actuelle de claudekit (lire `.template/version.json`)
3. **Identifier** les gaps :
   - Nouveaux hook events non supportés
   - Nouvelles options de frontmatter (skills, agents)
   - Nouveaux settings ou env vars utiles
   - Nouvelles fonctionnalités CLI
   - Changements breaking qui affectent claudekit
4. **Classer** par priorité :
   - P0 : features qui cassent claudekit si pas mises à jour
   - P1 : features très utiles à intégrer
   - P2 : nice-to-have
5. **Proposer** les changements à faire dans claudekit

## Checklist de comparaison

### Hook events supportés par claudekit
Vérifier que `gen.py` > `build_hooks()` couvre tous les events listés dans le changelog.

### Frontmatter fields
Vérifier que les agents et skills utilisent tous les champs frontmatter disponibles :
- Skills : `name`, `description`, `effort`, `user-invocable`, `allowed-tools`, `model`, `context`, `agent`, `hooks`, `disable-model-invocation`
- Agents : `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `isolation`

### Settings
Vérifier que `gen.py` > `build_settings()` inclut les derniers settings :
- `autoMemoryDirectory`, `modelOverrides`, `worktree.sparsePaths`, `claudeMdExcludes`
- `sandbox.*` settings
- `permissions.disableBypassPermissionsMode`

### Environment variables
Documenter les env vars utiles dans CLAUDE.md ou un fichier de référence.

## Output

```json
{
  "skill": "changelog-tracker",
  "latest_version": "2.1.80",
  "claudekit_version": "1.3.1",
  "gaps_found": 5,
  "p0": ["StopFailure hook not wired"],
  "p1": ["effort frontmatter not used", "InstructionsLoaded hook missing"],
  "p2": ["worktree.sparsePaths not documented"],
  "changes_proposed": [...]
}
```
