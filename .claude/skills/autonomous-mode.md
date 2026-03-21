---
name: autonomous-mode
description: Configure Claude Code for maximum autonomy — sandbox + acceptEdits + auto-approve, so you can leave and come back later
effort: low
user-invocable: true
triggers:
  - "mode autonome"
  - "autonomous mode"
  - "laisse moi tranquille"
  - "travaille tout seul"
  - "work autonomously"
  - "je reviens"
  - "run without me"
  - "hands off"
---

# Skill: /autonomous-mode

Configure Claude Code pour travailler en autonomie totale — sandbox, auto-approval, et boucle de travail.

## 3 niveaux d'autonomie

### Niveau 1 — Accept Edits (recommandé pour commencer)
Claude peut éditer les fichiers sans confirmation, mais demande encore pour bash.
```bash
claude --permission-mode acceptEdits
```
Ou dans `settings.local.json` :
```json
{"permissions": {"defaultMode": "acceptEdits"}}
```

### Niveau 2 — Sandbox + Auto-approve
Claude travaille dans un sandbox OS — peut tout faire librement dans les limites du sandbox.
```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true
  }
}
```
Le sandbox empêche : accès réseau non autorisé, écriture hors du projet, accès aux credentials.

### Niveau 3 — Full bypass (⚠️ UNIQUEMENT en sandbox sans internet)
```bash
claude --dangerously-skip-permissions
```

## Workflow autonome recommandé

1. **Configurer** : `/autonomous-mode` → choisir le niveau
2. **Donner la tâche** avec des critères de vérification clairs :
   ```
   Implémente la feature X. 
   Critères de succès : tous les tests passent, lint OK, pas de régression.
   Quand c'est fini, commit avec un message descriptif.
   ```
3. **Partir** — Claude travaille seul
4. **Revenir** — vérifier le résultat : `git log`, `git diff`, tests

## Bonnes pratiques pour le mode autonome

- **Toujours donner des critères de vérification** (tests, lint, build)
- **Limiter le scope** — une feature, un bug, pas "refactore tout"
- **Activer le sandbox** — protection contre les erreurs destructives
- **Utiliser `/loop`** pour les tâches répétitives : `/loop 5m pytest tests/`
- **Utiliser les agent teams** pour les tâches complexes parallélisables
- **Vérifier au retour** : `git log --oneline -10` + `git diff HEAD~5`

## Ce que gen.py peut configurer automatiquement

Ajouter dans `project.manifest.json` :
```json
"automation": {
  "permission_mode": "acceptEdits",
  "sandbox": true
}
```
Puis `python3 scripts/gen.py` génère les settings appropriés.
