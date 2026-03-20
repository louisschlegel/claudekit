# Command: /context-status

Affiche l'état du contexte Claude Code et recommande des actions.

## Protocole

1. Estimer l'utilisation du contexte (basé sur la longueur de la conversation)
2. Lister les fichiers lus dans cette session
3. Identifier les sources de contexte :
   - CLAUDE.md + @imports
   - `.claude/rules/` chargées
   - Skills actives
   - Hooks context injection
4. Recommander :
   - Si > 70% : `/compact [focus]`
   - Si > 85% : `/clear` et recommencer
   - Si beaucoup de fichiers lus : utiliser des subagents pour les recherches
   - Si conversation longue : faire un `/handoff` avant de clear
