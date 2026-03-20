---
paths: []
---
# Documentation Rules — Mandatory

La documentation fait partie du livrable. Du code sans documentation est du code incomplet.

## À chaque feature / changement significatif

1. **README.md** : mettre à jour si l'interface publique, l'installation, ou l'usage change
2. **CHANGELOG.md** : ajouter une entrée sous `[Unreleased]` pour tout changement visible par l'utilisateur
3. **Version** : bumper dans tous les fichiers de version si c'est une release
4. **ADR** : créer un Architecture Decision Record (`/generate-adr`) pour toute décision d'architecture non triviale
5. **Commentaires dans le code** : uniquement quand le POURQUOI n'est pas évident — jamais pour le QUOI

## À chaque release

- [ ] CHANGELOG.md à jour avec toutes les entrées depuis la dernière release
- [ ] Version bumpée dans : version.json, project.manifest.json, plugin.json, README badge
- [ ] README.md reflète l'état actuel (features, counts, installation)
- [ ] Tag git créé + GitHub Release avec release notes

## À chaque décision technique

- Documenter le POURQUOI dans un ADR ou un commentaire inline
- Inclure les alternatives considérées et les raisons du rejet
- Si le choix est controversé : invoquer `devils-advocate` d'abord

## Documentation technique automatique

- **`learning.md`** : alimenté automatiquement par `auto-learn.py` (stop hook)
- **`agent-events.jsonl`** : trace d'audit des outils utilisés (observability hook)
- **Handoff JSON** : chaque agent produit un rapport structuré
- **Session state** : `live-handoff.sh` trace les fichiers modifiés

## Ce qui ne doit PAS être documenté

- Code évident (pas de `// increment i` sur `i++`)
- Historique git (c'est le rôle de `git log`)
- Solutions temporaires de debug (le fix est dans le code)
