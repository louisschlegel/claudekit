# Workflow: MCP Vetting

## DÉCLENCHEUR
Intent classifié comme `mcp-vetting` par le hook UserPromptSubmit.
Commande directe : "ajoute ce MCP", "évalue ce serveur MCP", "vette ce MCP", "add MCP server".

## OBJECTIF
Évaluer en sécurité un nouveau serveur MCP avant de l'ajouter définitivement au projet.
Éviter d'exposer des outils dangereux ou des serveurs non maintenus à Claude.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — analyse des permissions et des outils exposés
2. **Explorer** — cartographie du code source du serveur MCP
3. **Orchestrateur** — décision finale APPROVE / REJECT / APPROVE_WITH_RESTRICTIONS

---

## ÉTAPE 1 — Identification du serveur MCP

Collecter les informations de base sur le serveur :
- [ ] URL du dépôt (GitHub, npm, PyPI)
- [ ] Nom du package / image Docker
- [ ] Description des outils exposés
- [ ] Auteur / organisation

```bash
# Exemples de sources MCP
# npm: @modelcontextprotocol/server-github
# pip: mcp-server-postgres
# GitHub: https://github.com/org/mcp-server-name
```

---

## ÉTAPE 2 — Research Phase (due diligence)

Évaluer la santé et la crédibilité du projet.

### 2a — Métriques GitHub
```bash
gh repo view [owner/repo] --json stargazerCount,pushedAt,openIssuesCount,forkCount
gh repo view [owner/repo] --json licenseInfo
```

Critères d'évaluation :

| Métrique | Vert | Jaune | Rouge |
|----------|------|-------|-------|
| Étoiles | > 100 | 10-100 | < 10 |
| Dernier commit | < 3 mois | 3-12 mois | > 12 mois |
| Issues ouvertes | < 20 | 20-100 | > 100 ou 0 (abandonné) |
| Auteur | Organisation connue | Individu actif | Inconnu |
| Licence | MIT, Apache 2.0 | BSD, ISC | Propriétaire, absente |

### 2b — Historique des releases
```bash
gh release list --repo [owner/repo] --limit 5
```

Chercher : releases régulières, changelog, politique de versioning sémantique.

### 2c — Vérification npm/PyPI
```bash
# npm
npm info @scope/package-name

# pip
pip index versions package-name 2>/dev/null | head -5
```

**Gate 2 :** si score global est ROUGE sur 2+ critères -> REJECT immédiat sans continuer.

---

## ÉTAPE 3 — Security Review

Invoquer `security-auditor` avec :
```
Cible : [URL repo ou package]
Demande : analyse les outils exposés, les permissions requises, les risques OWASP
```

### 3a — Inventaire des outils exposés
Lire le code source du serveur MCP (fichier principal, README, schema JSON) :
- Lister chaque outil (`name`, `description`, `inputSchema`)
- Identifier les opérations sensibles : write filesystem, exec shell, réseau externe, auth tokens

### 3b — Permissions système requises
Documenter ce que le serveur MCP demande à l'OS :
```
Filesystem access : [read-only | read-write | aucun]
Network access    : [domaines autorisés | tout | aucun]
Env vars requises : [liste]
Process execution : [oui | non]
Database access   : [oui — schéma exposé? | non]
```

### 3c — Vecteurs d'attaque potentiels
Vérifier :
- [ ] Injection de commandes via les paramètres des outils
- [ ] Path traversal dans les outils filesystem
- [ ] Exfiltration de données via les outils réseau
- [ ] Tokens/secrets exposés dans les logs ou réponses
- [ ] Dépendances vulnérables

```bash
# Si code disponible localement dans /tmp/mcp-sandbox-[name]/
npm audit 2>/dev/null || pip-audit 2>/dev/null
grep -r "exec\|eval\|shell\|spawn" --include="*.js" --include="*.ts" --include="*.py" . \
  | grep -v "test\|spec\|node_modules"
```

**Gate 3 :** si un vecteur d'attaque critique est identifié -> REJECT avec rapport détaillé.

---

## ÉTAPE 4 — Sandbox Test

Tester le serveur MCP dans un environnement isolé avant de l'ajouter définitivement.

### 4a — Installation temporaire
```bash
# Créer un backup du .mcp.json actuel
cp .mcp.json .mcp.json.bak-$(date +%Y%m%d)

# Ajouter temporairement le serveur MCP sous un nom sandbox
python3 -c "
import json
mcp = json.load(open('.mcp.json'))
mcp['mcpServers']['[name]-sandbox'] = {
  'command': '[commande]',
  'args': ['[args]'],
  'env': {}
}
json.dump(mcp, open('.mcp.json', 'w'), indent=2)
print('Added [name]-sandbox to .mcp.json')
"
```

### 4b — Session de test isolée
Ouvrir une nouvelle session Claude Code et exécuter les cas de test suivants :
- [ ] Le serveur démarre correctement (aucune erreur au démarrage)
- [ ] Les outils listés correspondent à la documentation officielle
- [ ] Les outils fonctionnent avec des paramètres valides
- [ ] Aucun outil non documenté n'est exposé
- [ ] Les erreurs sont gérées proprement (pas de crash, pas de fuite de données)

Cas de test à exécuter :
```
Test 1 — Happy path : appeler le premier outil avec des paramètres valides
Test 2 — Validation : appeler un outil avec des paramètres invalides -> doit retourner une erreur propre
Test 3 — Sécurité : tenter un path traversal ou injection dans les paramètres -> doit être rejeté
Test 4 — Scope : vérifier que le serveur n'expose que les outils documentés (list tools)
```

### 4c — Restauration si problème
```bash
# Si le test échoue ou révèle des problèmes
cp .mcp.json.bak-$(date +%Y%m%d) .mcp.json
echo "Rolled back .mcp.json to pre-test state"
```

**Gate 4 :** si le serveur ne démarre pas, expose des outils non documentés, ou échoue les tests de sécurité -> REJECT.

---

## ÉTAPE 5 — Décision et intégration

### 5a — Decision Gate

Agréger les résultats des étapes 2, 3, 4 et choisir :

| Décision | Critères |
|----------|----------|
| `APPROVE` | Tous les critères verts, tous les tests OK, aucun vecteur d'attaque |
| `APPROVE_WITH_RESTRICTIONS` | Critères jaunes, ou outils dangereux à bloquer, tests OK |
| `REJECT` | Un ou plusieurs critères rouges, ou test échoué, ou vecteur critique |

**Si APPROVE_WITH_RESTRICTIONS :** documenter explicitement les restrictions dans `.mcp.json` :
```json
{
  "mcpServers": {
    "[name]": {
      "command": "[commande]",
      "args": ["[args]"],
      "env": {},
      "_allowed_tools": ["tool1", "tool2"],
      "_blocked_tools": ["tool3"],
      "_vetting_note": "tool3 expose le filesystem en écriture — non nécessaire pour ce projet"
    }
  }
}
```

### 5b — Intégration permanente (si APPROVE ou APPROVE_WITH_RESTRICTIONS)

```bash
# 1. Mettre à jour project.manifest.json
python3 -c "
import json
manifest = json.load(open('project.manifest.json'))
servers = manifest.setdefault('mcp_servers', [])
if '[name]' not in servers:
    servers.append('[name]')
    json.dump(manifest, open('project.manifest.json', 'w'), indent=2)
    print('Added [name] to mcp_servers in manifest')
"

# 2. Régénérer la config (settings.local.json + .mcp.json définitif)
python3 scripts/gen.py

# 3. Nettoyer le backup et l'entrée sandbox
python3 -c "
import json
mcp = json.load(open('.mcp.json'))
mcp['mcpServers'].pop('[name]-sandbox', None)
json.dump(mcp, open('.mcp.json', 'w'), indent=2)
"
rm -f .mcp.json.bak-*
```

### 5c — Si REJECT

```bash
# Restaurer .mcp.json propre
cp .mcp.json.bak-$(date +%Y%m%d) .mcp.json
rm -f .mcp.json.bak-*
```

---

## CONTRAT DE SORTIE

```
MCP SERVER: [name]
VERSION: [version testée]
DECISION: APPROVE | APPROVE_WITH_RESTRICTIONS | REJECT

RESEARCH:
  Stars: N
  Last commit: [date relative]
  Licence: [licence]
  Maintainer: [org/user]

SECURITY:
  Tools exposed: N ([liste des noms])
  Sensitive operations: [liste ou "none"]
  Vulnerabilities found: N
  Critical vectors: [liste ou "none"]

SANDBOX TEST: PASS | FAIL
  Test cases passed: N/4

RESTRICTIONS (si applicable):
  Allowed tools: [liste]
  Blocked tools: [liste]

INTEGRATED: yes | no
MANIFEST UPDATED: yes | no
LEARNING.MD UPDATED: yes
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "mcp_server": "[name]",
  "version": "[version]",
  "decision": "approve|approve_with_restrictions|reject",
  "stars": 0,
  "last_commit_days_ago": 0,
  "licence": "[licence]",
  "tools_exposed": [],
  "sensitive_operations": [],
  "vulnerabilities_count": 0,
  "critical_vectors": [],
  "sandbox_test_passed": true,
  "sandbox_test_cases": 4,
  "sandbox_test_passed_count": 4,
  "restrictions": {
    "allowed_tools": [],
    "blocked_tools": []
  },
  "integrated": false,
  "manifest_updated": false,
  "learning_updated": true
}
```
