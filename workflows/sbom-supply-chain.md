# Workflow: SBOM & Supply Chain Security

## DÉCLENCHEUR
Intent classifié comme `sbom` par le hook UserPromptSubmit.
Commande directe : "génère un SBOM", "supply chain audit", "vérifie les dépendances vulnérables", "cyclonedx", "spdx".
Automatique : gate dans `workflows/release.md` (pre-release) ou `workflows/dependency-audit.md`.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — scan CVE et analyse des vulnérabilités
2. **Compliance Officer** — validation VEX et conformité réglementaire
3. **Reviewer** — validation finale du rapport

---

## ÉTAPE 1 — Génération du SBOM

Détecter la stack depuis `project.manifest.json`, puis choisir l'outil adapté.

### Python
```bash
pip install cyclonedx-bom
cyclonedx-py environment -o bom.xml --format xml
# ou depuis requirements.txt
cyclonedx-py requirements requirements.txt -o bom.xml
```

### Node.js
```bash
npx @cyclonedx/cyclonedx-npm --output-file bom.json
```

### Go
```bash
go install github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@latest
cyclonedx-gomod app -json -output bom.json .
```

### Multi-stack ou conteneurs (fallback universel)
```bash
trivy sbom . --format cyclonedx --output bom.json
# ou SPDX si demandé explicitement
trivy sbom . --format spdx-json --output sbom.spdx.json
```

**Gate 1 :** le fichier SBOM doit exister et être valide JSON/XML. Si échec → logger et continuer avec trivy comme fallback.

---

## ÉTAPE 2 — Scan CVE

Lancer les scanners adaptés à la stack. Collecter les résultats en JSON pour traitement structuré.

### Python
```bash
pip install pip-audit
pip-audit --output json -o pip-audit-results.json
```

### Node.js
```bash
npm audit --json > npm-audit-results.json
```

### Multi-stack / conteneurs
```bash
trivy fs . --format json --output trivy-results.json --severity CRITICAL,HIGH,MEDIUM,LOW
```

### Traitement des seuils

| Sévérité | Action |
|----------|--------|
| CRITICAL | Bloque la gate — correctif obligatoire avant merge/release |
| HIGH | Warning — correctif recommandé, documenter la décision si skip |
| MEDIUM | Documenter dans `learning.md` — planifier le correctif |
| LOW | Documenter seulement |

**Gate 2 :** si COUNT_CRITICAL > 0 → gate BLOCK. Aller à étape 3 pour le VEX avant de décider du blocage définitif.

---

## ÉTAPE 3 — VEX (Vulnerability Exploitability eXchange)

Pour chaque CVE identifié, évaluer l'exploitabilité réelle dans le contexte du projet.

Pour chaque CVE CRITICAL ou HIGH :

```
CVE-XXXX-YYYY
  Package : [nom@version]
  CVSS : [score]
  Vecteur : [network|local|physical]
  Exploitabilité dans ce projet :
    - Ce code est-il accessible depuis internet ?
    - La fonctionnalité vulnérable est-elle utilisée ?
    - Y a-t-il des contrôles compensatoires ?
  Verdict : EXPLOITABLE | NOT_AFFECTED | IN_TRIAGE | FIXED
  Justification : [texte libre]
```

**Si NOT_AFFECTED ou IN_TRIAGE :** la gate CRITICAL peut être levée avec justification documentée.
**Si EXPLOITABLE :** blocage maintenu — implémenter le fix maintenant.

---

## ÉTAPE 4 — Lifecycle Scripts Lockdown (Node.js uniquement)

Si le projet contient un `package.json`, vérifier les scripts de cycle de vie pour du code suspect.

```bash
# Lister tous les scripts preinstall/postinstall/prepare des dépendances
cat package-lock.json | python3 -c "
import json, sys
lock = json.load(sys.stdin)
packages = lock.get('packages', {})
for name, pkg in packages.items():
    scripts = pkg.get('scripts', {})
    risky = {k: v for k, v in scripts.items() if k in ['preinstall', 'postinstall', 'prepare', 'install']}
    if risky:
        print(f'{name}: {risky}')
"
```

Signaux d'alerte à investiguer :
- Téléchargement réseau dans un script d'installation (`curl`, `wget`, `fetch`)
- Exécution de binaires non tracés dans le dépôt
- Obfuscation (`eval`, `Buffer.from(..., 'base64')`)
- Accès à `~/.ssh`, `~/.aws`, variables d'environnement sensibles

**Gate 3 :** si script suspect trouvé → BLOCK + documenter + invoquer `security-auditor` pour analyse approfondie.

---

## ÉTAPE 5 — Credential Hygiene

Scanner le dépôt pour des secrets exposés.

```bash
# Option 1 : gitleaks (recommandé)
gitleaks detect --source . --report-format json --report-path gitleaks-report.json

# Option 2 : trufflescan
trufflehog filesystem . --json > trufflehog-report.json

# Option 3 : fallback pattern-based
grep -r --include="*.{py,js,ts,go,env,yaml,yml,json,toml}" \
  -E "(api_key|apikey|secret|password|token|credential)\s*=\s*['\"][^'\"]{8,}" \
  --exclude-dir={node_modules,.git,__pycache__} . | head -50
```

**Gate 4 :** si secret hardcodé trouvé → BLOCK immédiat + `git filter-repo` pour purge de l'historique si le secret est dans des commits passés.

---

## ÉTAPE 6 — MCP Server Audit

Si le projet contient un `.mcp.json`, vérifier les serveurs MCP configurés.

```bash
# Lister les serveurs configurés
cat .mcp.json 2>/dev/null | python3 -c "
import json, sys
cfg = json.load(sys.stdin)
servers = cfg.get('mcpServers', {})
for name, config in servers.items():
    cmd = config.get('command', '')
    args = config.get('args', [])
    print(f'  {name}: {cmd} {\" \".join(args)}')
" 2>/dev/null || echo "Pas de .mcp.json"
```

Pour chaque serveur MCP listé, vérifier :
- Est-il dans la liste officielle Anthropic (filesystem, github, postgres, sqlite, brave-search, etc.) ?
- Si custom : le code source est-il auditable ? Où est-il hébergé ?
- A-t-il accès à des ressources sensibles (filesystem root, credentials) ?

Référence : `workflows/mcp-vetting.md` pour un audit approfondi d'un serveur spécifique.

**Gate 5 :** MCP non reconnu avec accès étendu → warning + demander confirmation à l'utilisateur.

---

## ÉTAPE 7 — Rapport et auto-apprentissage

Consolider tous les résultats dans un rapport structuré.

```bash
# Archiver les artefacts
mkdir -p .sbom/$(date +%Y-%m-%d)
mv bom.* .sbom/$(date +%Y-%m-%d)/ 2>/dev/null
mv *-results.json .sbom/$(date +%Y-%m-%d)/ 2>/dev/null
mv *-report.json .sbom/$(date +%Y-%m-%d)/ 2>/dev/null
```

Passer les findings à auto-learn :
```bash
python3 scripts/auto-learn.py --from-agent security-auditor --input '[JSON_OUTPUT]'
```

---

## CONTRAT DE SORTIE

```
SBOM GENERATED: bom.json / bom.xml
DATE: YYYY-MM-DD
STACK: [python|node|go|multi]

CVE FINDINGS:
  CRITICAL: N (N avec VEX NOT_AFFECTED, N EXPLOITABLE)
  HIGH:     N
  MEDIUM:   N
  LOW:      N

VEX VERDICTS:
  EXPLOITABLE:   N → correctifs appliqués
  NOT_AFFECTED:  N → justifiés
  IN_TRIAGE:     N → suivi dans learning.md

LIFECYCLE SCRIPTS: CLEAN / SUSPICIOUS (N found)
CREDENTIAL SCAN:   CLEAN / BLOCKED (N secrets)
MCP AUDIT:         CLEAN / WARNING (N serveurs non reconnus)

RELEASE_GATE: PASS / BLOCK
SBOM_PATH: .sbom/YYYY-MM-DD/bom.json
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "sbom_path": ".sbom/YYYY-MM-DD/bom.json",
  "sbom_format": "cyclonedx|spdx",
  "cve_counts": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "vex_verdicts": {
    "exploitable": 0,
    "not_affected": 0,
    "in_triage": 0
  },
  "lifecycle_scripts_clean": true,
  "credentials_clean": true,
  "mcp_audit_warnings": 0,
  "release_gate": "pass|block",
  "artifacts": [".sbom/YYYY-MM-DD/"]
}
```
