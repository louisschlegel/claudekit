## Couches de sécurité

Le système a 4 couches de défense indépendantes :

1. **Whitelist de permissions** — `settings.local.json` : seules les commandes nécessaires au stack sont autorisées
2. **Pre-tool gate** — `pre-bash-guard.sh` : bloque les commandes destructives avant exécution
3. **Post-edit quality guards** — `post-edit.sh` : lint, type-check, scan de secrets après chaque fichier édité
4. **Prompt injection detection** — `user-prompt-submit.sh` : détecte les tentatives de manipulation

**Fichiers protégés** (tout agent qui veut les modifier doit avoir une confirmation explicite) :
- `.claude/settings.local.json`
- `scripts/gen.py`
- `.template/version.json`
