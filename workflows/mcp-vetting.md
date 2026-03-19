# Workflow: MCP Vetting

Évaluer et approuver un nouveau serveur MCP avant de l'ajouter au projet.

## Étapes

### 1. Recherche (5 min)
- Trouver le repo GitHub du serveur MCP
- Vérifier : auteur, stars, dernière activité, issues ouvertes, license
- Lire le README : quels outils expose-t-il ? Quelles permissions demande-t-il ?
- Chercher des CVE ou incidents de sécurité connus

### 2. Revue de sécurité (10 min)
- **Outils exposés** : lister chaque tool avec ses paramètres
- **Permissions réseau** : accède-t-il à internet ? Quels domaines ?
- **Accès filesystem** : lit/écrit quels chemins ?
- **Données sensibles** : accède-t-il à des secrets, tokens, ou données utilisateur ?
- **Code review** : scanner le code source pour des patterns suspects :
  - `eval()`, `exec()`, command injection
  - Exfiltration de données (POST vers URLs externes)
  - Écriture dans des chemins inattendus

### 3. Test sandbox (15 min)
- Ajouter temporairement dans `.mcp.json` :
  ```json
  {"<server-name>": {"command": "...", "args": [...]}}
  ```
- Démarrer une session Claude Code de test
- Tester chaque outil exposé avec des données non-sensibles
- Vérifier que les réponses sont correctes et dans le format attendu
- Mesurer la latence et la fiabilité

### 4. Gate de décision

| Critère | APPROVE | REJECT |
|---------|---------|--------|
| Auteur vérifié | Organisation connue ou contributeur actif | Anonymous, pas de profil |
| Maintenance | Commit < 3 mois | Dernier commit > 1 an |
| Sécurité | Pas de patterns suspects | eval(), exfiltration, perms excessives |
| Fonctionnalité | Fait ce qui est annoncé | Comportement inattendu |
| Performance | Latence < 2s | Timeout fréquents |

Décision : **APPROVE** / **APPROVE_WITH_RESTRICTIONS** / **REJECT**

### 5. Intégration (si approuvé)
1. Ajouter le serveur à `project.manifest.json` > `mcp_servers[]`
2. Exécuter `python3 scripts/gen.py` pour régénérer `.mcp.json`
3. Documenter les restrictions si APPROVE_WITH_RESTRICTIONS
4. Redémarrer Claude Code

## HANDOFF JSON

```json
{
  "workflow": "mcp-vetting",
  "status": "approved|approved_with_restrictions|rejected",
  "server": {
    "name": "server-name",
    "repo": "https://github.com/...",
    "version": "1.2.0",
    "stars": 450,
    "last_commit": "2026-03-15"
  },
  "security": {
    "tools_exposed": 5,
    "network_access": true,
    "filesystem_access": "read-only",
    "suspicious_patterns": []
  },
  "test_results": {
    "tools_tested": 5,
    "tools_passed": 5,
    "avg_latency_ms": 340
  },
  "decision": "approved",
  "restrictions": [],
  "next_steps": ["Add to manifest", "Restart Claude Code"]
}
```

## CONTRAT DE SORTIE

- [ ] Recherche complétée : repo, auteur, stars, license vérifiés
- [ ] Revue de sécurité : tous les outils audités, pas de pattern suspect
- [ ] Test sandbox : tous les outils testés avec succès
- [ ] Décision documentée : APPROVE/REJECT avec justification
- [ ] Si approuvé : ajouté au manifest, config régénérée, Claude redémarré
- [ ] HANDOFF JSON produit
