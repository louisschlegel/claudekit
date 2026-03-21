# Workflow: Remote Development

Contrôler Claude Code depuis ton téléphone ou un navigateur pendant que le terminal local travaille.

## Modes

### Mode 1 — Mid-session (le plus simple)
Depuis une session Claude Code active :
```
/remote-control
```
Scanne le QR code avec ton téléphone → claude.ai/code → session connectée.

### Mode 2 — Serveur dédié
```bash
claude remote-control --name "Mon Projet" --spawn worktree --capacity 8
```
- Chaque connexion remote crée un worktree isolé
- Jusqu'à 8 sessions parallèles
- Nommé pour retrouver facilement dans claude.ai/code

### Mode 3 — Toujours actif
Dans `/config` → "Enable Remote Control for all sessions" → `true`
Chaque session est automatiquement accessible depuis claude.ai/code.

## Cas d'usage

| Scénario | Comment |
|----------|---------|
| Lancer un task overnight | `claude "migrate all components"` → `/rc` → surveiller depuis le lit |
| Review depuis le train | `/rc` → lire le diff sur mobile → approver/corriger |
| Debug urgent en soirée | Ouvrir claude.ai/code → reprendre la session → hotfix |
| Pair programming remote | Partager le lien → le collègue voit la session en live |

## HANDOFF JSON

```json
{
  "workflow": "remote-dev",
  "status": "configured",
  "mode": "server|mid-session|always-on",
  "sessions_active": 3,
  "worktree_isolation": true
}
```

## CONTRAT DE SORTIE

- [ ] Remote control configuré et testé
- [ ] Session accessible depuis claude.ai/code ou mobile
- [ ] HANDOFF JSON produit
