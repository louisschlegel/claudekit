---
name: headless
description: Run Claude Code in non-interactive mode for CI, scripts, and automation pipelines
effort: low
user-invocable: true
triggers:
  - "headless"
  - "mode ci"
  - "non-interactive"
  - "pipe mode"
  - "batch mode"
  - "automatise avec claude"
---

# Skill: /headless

Utiliser Claude Code en mode non-interactif pour CI, scripts, et pipelines.

## Exemples de commandes headless

### One-shot
```bash
claude -p "Explique ce que fait ce projet" 
claude -p "Liste tous les endpoints API" --output-format json
claude -p "Fix les erreurs de lint" --allowedTools "Edit,Bash(npm run lint *)"
```

### Fan-out (traitement batch)
```bash
# Migrer 100 fichiers en parallèle
for file in $(cat files-to-migrate.txt); do
  claude -p "Migre $file de React class vers hooks fonctionnels" \
    --allowedTools "Edit,Read" &
done
wait
```

### CI pipeline
```yaml
# .github/workflows/claude-review.yml
- name: Claude Code Review
  run: |
    claude -p "Review les changements dans ce PR. 
    Liste les problèmes par sévérité (BLOCKER/WARNING/SUGGESTION).
    Output format JSON." \
    --output-format json > review.json
```

### Cron / loop
```bash
# Vérifier la santé du projet toutes les heures
claude -p "Run les tests et reporte les failures" --output-format json
```

## Flags utiles

| Flag | Usage |
|------|-------|
| `-p "prompt"` | Mode non-interactif (print mode) |
| `--output-format json` | Sortie JSON parseable |
| `--output-format stream-json` | Streaming JSON pour pipelines |
| `--allowedTools "Edit,Bash(npm *)"` | Limiter les outils disponibles |
| `--model sonnet` | Choisir le modèle (économie) |
| `--dangerously-skip-permissions` | Bypass permissions (sandbox only!) |
| `--continue` | Reprendre la dernière session |
| `--resume` | Choisir une session à reprendre |
| `--verbose` | Debug output |
