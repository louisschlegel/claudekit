# Workflow: Security Audit

## DÉCLENCHEUR
Intent classifié comme `audit` par le hook UserPromptSubmit.
Commande directe : "audit sécurité", "vérifie la sécurité", "scan".
Automatique : gate dans `workflows/release.md`.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — scan principal
2. **Reviewer** — validation des fixes
3. **Debug Detective** — analyse des vulnérabilités complexes (si besoin)

---

## ÉTAPE 1 — Définir le scope

Scope par défaut : tous les fichiers modifiés depuis le dernier tag.
Scope élargi si demande explicite : tout le codebase.

```bash
# Fichiers modifiés depuis le dernier tag
git diff $(git describe --tags --abbrev=0)..HEAD --name-only
```

---

## ÉTAPE 2 — Audit principal

Invoquer `security-auditor` avec :
```
Scope : [liste des fichiers]
Stack : [manifest stack]
Mode : pre-release / full-scan / targeted
```

Le security-auditor effectue les 5 scans :
1. Secrets exposés
2. Injections (adapté au stack)
3. Authentification & Autorisation
4. Dépendances vulnérables
5. Configuration

---

## ÉTAPE 2b — Static Analysis avancée

### Tools disponibles (selon stack)

**CodeQL** (GitHub Advanced Security) :
```bash
# Créer une database CodeQL
codeql database create codeql-db --language=python  # ou javascript, java, go, cpp
# Analyser avec les queries security-extended
codeql database analyze codeql-db --format=sarif-latest --output=results.sarif \
  codeql/python-queries:codeql-suites/python-security-extended.qls
```

**Semgrep** :
```bash
# Scan avec les règles de sécurité officielles
semgrep --config=p/security-audit --config=p/secrets --config=p/owasp-top-ten \
  --sarif --output=semgrep-results.sarif .
# Règles custom pour patterns spécifiques au projet
semgrep --config=p/semgrep-rules .
```

**Bandit** (Python) :
```bash
bandit -r . -f json -o bandit-report.json
```

**gosec** (Go) :
```bash
gosec -fmt=json -out=gosec-report.json ./...
```

**ESLint security** (JS/TS) :
```bash
npx eslint --plugin security --rule 'security/detect-object-injection: warn' .
```

**SARIF parsing** (résultats unifiés) :
```bash
# Parser les résultats SARIF pour extraire HIGH/CRITICAL
python3 -c "
import json, sys
with open('results.sarif') as f:
    sarif = json.load(f)
for run in sarif.get('runs', []):
    for result in run.get('results', []):
        level = result.get('level', 'none')
        if level in ('error', 'warning'):
            msg = result.get('message', {}).get('text', '')
            loc = result.get('locations', [{}])[0]
            uri = loc.get('physicalLocation', {}).get('artifactLocation', {}).get('uri', '')
            line = loc.get('physicalLocation', {}).get('region', {}).get('startLine', '?')
            print(f'[{level.upper()}] {uri}:{line} — {msg}')
"
```

### Secrets Detection (dedicated tools)

```bash
# gitleaks — scan du repo entier incluant l'historique git
gitleaks detect --source . --report-format json --report-path gitleaks-report.json 2>/dev/null

# trufflehog — détection haute entropie + patterns connus
trufflehog git file://. --json > trufflehog-report.json 2>/dev/null
```

### SBOM & Supply Chain

```bash
# Trivy — scan multi-stack (vulnérabilités + misconfigs + secrets)
trivy fs . --format json --output trivy-report.json 2>/dev/null

# Générer un SBOM CycloneDX
trivy sbom . --format cyclonedx --output sbom.json 2>/dev/null
```

### Pattern Trail of Bits — Audit Context Building

1. **Analyse First Principles** : pour chaque composant critique, demander "Pourquoi ce code fait ce qu'il fait ?" (5 Whys appliqués à la sécurité)
2. **Variant Analysis** : quand un bug est trouvé, chercher des patterns similaires dans tout le codebase :
   ```bash
   # Exemple : trouver tous les appels similaires au pattern vulnérable
   semgrep --pattern '$FUNC($USER_INPUT)' --lang python .
   ```
3. **Entry-point analysis** : cartographier tous les points d'entrée de données non fiables (routes HTTP, CLI args, file uploads, message queues, webhooks)
4. **Trust boundary mapping** : identifier où les données passent d'un niveau de confiance à un autre (user -> server, server -> DB, service -> service)
5. **Fix verification** : après chaque fix, re-scanner uniquement le fichier modifié pour confirmer la résolution

### Intégration CI/CD (recommandation)

```yaml
# .github/workflows/security.yml (exemple)
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Semgrep
        run: semgrep --config=p/security-audit --error .
      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep-results.sarif
```

Si des outils ne sont pas installés, noter "outil non disponible — vérification manuelle requise" et continuer avec les outils présents.

---

## ÉTAPE 3 — Traitement des findings

### CRITICAL (traitement immédiat obligatoire)
```
Pour chaque finding CRITICAL :
1. Localiser le problème exact (fichier:ligne)
2. Proposer un fix immédiat
3. Implémenter le fix
4. Vérifier que le finding est résolu
```

### HIGH (traitement avant release)
```
Même process que CRITICAL.
Si le fix est complexe → créer une branch fix/security-[cwe]
```

### MEDIUM (à planifier)
```
Créer une issue ou TODO avec :
- Référence CWE
- Fichier:ligne
- Fix recommandé
- Délai suggéré
```

### LOW (optionnel)
```
Documenter dans learning.md pour référence future.
Traiter si la maintenance le permet.
```

---

## ÉTAPE 4 — Vérification des fixes

Pour chaque fix CRITICAL/HIGH :
- Re-invoquer `security-auditor` sur le fichier corrigé
- Vérifier : finding disparu
- Invoquer `reviewer` sur le diff du fix

---

## ÉTAPE 5 — Rapport final

Documenter dans `learning.md` section "Bugs" :
```markdown
### [date] — Audit sécurité vX.Y.Z
- **Findings** : N CRITICAL, N HIGH, N MEDIUM, N LOW
- **Resolus** : N
- **Patterns à éviter** : [liste]
```

### Export SARIF vers GitHub Security tab

Si des résultats SARIF ont été générés (Semgrep, CodeQL, Trivy) :
```bash
# Upload via gh CLI (nécessite GitHub Advanced Security)
gh api repos/{owner}/{repo}/code-scanning/sarifs \
  -X POST \
  -F "sarif=@results.sarif" \
  -F "ref=$(git rev-parse HEAD)" \
  -F "commit_sha=$(git rev-parse HEAD)" 2>/dev/null \
  && echo "SARIF uploaded to GitHub Security tab" \
  || echo "SARIF upload skipped — GitHub Advanced Security may not be enabled"
```
Les findings apparaissent ensuite dans l'onglet Security > Code scanning alerts du repo.

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque audit sécurité complété, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output du security-auditor → findings HIGH/CRITICAL → section "Bugs résolus" [SÉCURITÉ]
python3 scripts/auto-learn.py --from-agent security-auditor --input '[JSON_OUTPUT_SECURITY_AUDITOR]'

# Si des vulnérabilités complexes ont nécessité debug-detective
python3 scripts/auto-learn.py --from-agent debug-detective --input '[JSON_OUTPUT_DEBUG_DETECTIVE]'

# Output du reviewer sur les fixes → vérifier patterns récurrents
python3 scripts/auto-learn.py --from-agent reviewer --input '[JSON_OUTPUT_REVIEWER]'
```

Si `--extract-patterns` retourne des custom_rules candidates avec confiance HIGH → proposer à l'utilisateur de les ajouter dans `project.manifest.json` :

```bash
python3 scripts/auto-learn.py --extract-patterns
```

---

## CONTRAT DE SORTIE

```
AUDIT SCOPE: [N fichiers]
DATE: YYYY-MM-DD

FINDINGS:
  CRITICAL: N (N resolved)
  HIGH: N (N resolved)
  MEDIUM: N (tracked)
  LOW: N (documented)

RELEASE_GATE: PASS / BLOCK

FIXES APPLIED:
  [liste des fixes]

PENDING:
  [liste des findings MEDIUM/LOW avec tracking]

LEARNING.MD: updated (via auto-learn.py)
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "scope": "...",
  "findings": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "secrets_found": false,
  "deploy_gate": "pass|fail",
  "report_path": "..."
}
```
