# Workflow: Dependency Audit

**Déclenché par :** `[INTENT:dependency-audit]` — mots-clés : "audit les dépendances", "vérifie les CVE", "scan les vulnérabilités", "dépendances vulnérables", "check npm audit", "pip-audit", "security scan deps", "snyk", "licence check"

**Agents impliqués :** security-auditor → reviewer

> ⚠️ Ce workflow est en **lecture seule** — il audite et rapporte, sans modifier les dépendances.
> Pour mettre à jour les dépendances après l'audit → utiliser `workflows/dependency-update.md`

---

## Vue d'ensemble

```
Lock files + manifests
        ↓
  Scan CVE + GHSA
        ↓
  Analyse licences
        ↓
  Dépendances fantômes + inutilisées
        ↓
  Rapport classé par criticité
        ↓
  Plan d'action priorisé
```

---

## Étape 1 — Inventaire des dépendances

```bash
# Python
pip list --format=json | jq '.[].name' | wc -l
pip list --outdated --format=columns

# Node.js
cat package.json | jq '.dependencies, .devDependencies | keys | length'
npm list --depth=0 2>/dev/null | grep -c "├\|└"

# Go
go list -m all | wc -l
go list -m -u all 2>/dev/null  # versions disponibles

# Rust
cargo tree | wc -l
cargo outdated

# Ruby
gem list | wc -l
bundle outdated
```

---

## Étape 2 — Scan CVE (vulnérabilités connues)

### Python

```bash
# pip-audit — scan CVE depuis OSV + PyPI advisory
pip install pip-audit
pip-audit --output json > audit-results/pip-audit.json
pip-audit --format columns  # vue lisible

# Safety (alternative)
pip install safety
safety check --full-report --output json > audit-results/safety.json

# OSV scanner (Google)
osv-scanner --lockfile requirements.txt
osv-scanner --lockfile poetry.lock
```

### Node.js

```bash
# npm audit — scan GHSA + NVD
npm audit --json > audit-results/npm-audit.json
npm audit --audit-level=moderate  # exit 1 si moderate+

# yarn
yarn audit --json > audit-results/yarn-audit.json

# pnpm
pnpm audit --json > audit-results/pnpm-audit.json

# Snyk (plus complet, nécessite compte)
npx snyk test --json > audit-results/snyk.json
```

### Go

```bash
# govulncheck (officiel Go team)
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck -json ./... > audit-results/govulncheck.json

# Nancy (Sonatype)
go list -json -deps ./... | nancy sleuth
```

### Rust

```bash
cargo install cargo-audit
cargo audit --json > audit-results/cargo-audit.json
```

### Ruby

```bash
gem install bundler-audit
bundle-audit check --update --format json > audit-results/bundler-audit.json
```

### Docker images

```bash
# Trivy — scan image Docker
trivy image --format json --output audit-results/trivy-image.json mon-image:latest
trivy image --severity HIGH,CRITICAL mon-image:latest

# Grype
grype mon-image:latest -o json > audit-results/grype.json
```

---

## Étape 3 — Classification des vulnérabilités

Invoquer **security-auditor** pour analyser les résultats bruts :

```python
# Parsing et classification des résultats

SEVERITY_MAP = {
    "CRITICAL": {"priority": 1, "sla": "patch in 24h", "block_deploy": True},
    "HIGH":     {"priority": 2, "sla": "patch in 7j",  "block_deploy": True},
    "MODERATE": {"priority": 3, "sla": "patch in 30j", "block_deploy": False},
    "LOW":      {"priority": 4, "sla": "next sprint",  "block_deploy": False},
    "INFO":     {"priority": 5, "sla": "backlog",      "block_deploy": False},
}

def classify_vulnerability(vuln: dict) -> dict:
    severity = vuln.get("severity", "LOW").upper()
    cvss = vuln.get("cvss_score", 0.0)

    # Ajustement contextuel
    context_multiplier = 1.0

    # Vulnérabilité dans le code de production vs devDependencies
    if vuln.get("is_dev_dependency"):
        context_multiplier *= 0.5  # moins critique

    # Vecteur d'attaque réseau = plus critique qu'un vecteur local
    if vuln.get("attack_vector") == "NETWORK":
        context_multiplier *= 1.5

    # Pas de fix disponible = noter mais ne pas bloquer
    if not vuln.get("fix_available"):
        context_multiplier *= 0.8

    return {
        **vuln,
        "adjusted_priority": SEVERITY_MAP[severity]["priority"],
        "sla": SEVERITY_MAP[severity]["sla"],
        "block_deploy": SEVERITY_MAP[severity]["block_deploy"] and context_multiplier >= 1.0,
        "context_multiplier": context_multiplier,
    }
```

---

## Étape 4 — Analyse des licences

```bash
# Python — vérifier licences
pip install pip-licenses
pip-licenses --format=json --with-authors > audit-results/licenses-python.json
pip-licenses --format=markdown  # vue lisible

# Node.js
npx license-checker --json > audit-results/licenses-node.json
npx license-checker --onlyAllow "MIT;ISC;BSD-2-Clause;BSD-3-Clause;Apache-2.0;CC0-1.0"

# Go
go-licenses check ./...
go-licenses save ./... --save_path=audit-results/licenses/

# Rust
cargo-license --json > audit-results/licenses-rust.json
```

**Licences et compatibilité :**
```
PERMISSIVES (OK pour code propriétaire) :
  MIT, ISC, BSD-2, BSD-3, Apache-2.0, CC0, Unlicense

COPYLEFT FAIBLE (OK si utilisé comme library) :
  LGPL-2.1, LGPL-3.0, MPL-2.0
  → Vérifier avec le legal si incertitude

COPYLEFT FORT (⚠️ attention pour code propriétaire) :
  GPL-2.0, GPL-3.0, AGPL-3.0
  → Requiert publication du code source si distribué

INTERDITES (❌ ne pas utiliser) :
  PROPRIETARY, UNLICENSED, COMMERCIAL, CC-BY-NC
```

**Alerte automatique :**
```python
FORBIDDEN_LICENSES = ["GPL-2.0", "GPL-3.0", "AGPL-3.0"]
REVIEW_NEEDED = ["LGPL-2.1", "LGPL-3.0", "MPL-2.0"]

def check_license_compliance(licenses: list[dict], project_type: str) -> list[dict]:
    issues = []
    for pkg in licenses:
        lic = pkg["license"]
        if lic in FORBIDDEN_LICENSES and project_type != "open-source":
            issues.append({
                "package": pkg["name"],
                "license": lic,
                "severity": "BLOCKER",
                "reason": "License incompatible avec un projet propriétaire"
            })
        elif lic in REVIEW_NEEDED:
            issues.append({
                "package": pkg["name"],
                "license": lic,
                "severity": "WARNING",
                "reason": "Licence copyleft faible — vérification légale recommandée"
            })
    return issues
```

---

## Étape 5 — Dépendances fantômes et inutilisées

```bash
# Python — dépendances non-utilisées
pip install deptry
deptry . --json-output audit-results/deptry.json

# Node.js — dépendances non-importées
npx depcheck --json > audit-results/depcheck.json

# Go — modules non-utilisés (built-in)
go mod tidy --dry-run  # affiche ce qui serait supprimé

# Modules transitifs mal déclarés (phantom deps)
# = importés directement mais pas dans package.json / requirements.txt
# deptry et depcheck le détectent automatiquement
```

---

## Étape 6 — Rapport de sortie

```markdown
## Rapport d'audit des dépendances — {projet} — {date}

### Résumé

| Catégorie | Count |
|-----------|-------|
| 🔴 CRITICAL CVE | {N} |
| 🟠 HIGH CVE | {N} |
| 🟡 MODERATE CVE | {N} |
| ⚪ LOW CVE | {N} |
| ⚠️ Licences à vérifier | {N} |
| 🚫 Licences interdites | {N} |
| 🗑️ Dépendances inutilisées | {N} |
| 👻 Dépendances fantômes | {N} |

**Statut déploiement :** {✅ CLEAR | ⛔ BLOCKED ({N} critical/high)}

---

### 🔴 CRITICAL — Action dans les 24h

#### {package}@{version}
- **CVE :** {CVE-XXXX-XXXXX}
- **CVSS :** {score} ({vecteur})
- **Description :** {description}
- **Fix disponible :** {version de fix}
- **Action :** `{commande de mise à jour}`
- **Workaround :** {si pas de fix immédiat}

---

### 🟠 HIGH — Action dans les 7 jours

...

### 🟡 MODERATE — Planifier ce sprint

...

### ⚪ LOW — Backlog

...

---

### Licences

#### ⚠️ À vérifier avec le legal
| Package | Licence | Risque |
|---------|---------|--------|
| {nom} | LGPL-3.0 | Copyleft faible |

---

### Dépendances à nettoyer

#### Inutilisées (peuvent être supprimées)
- {package} — dernière utilisation : {date ou "jamais importé"}

#### Fantômes (importées mais non déclarées)
- {package} — importé dans {fichier} mais absent du manifest

---

### Plan d'action

```bash
# 1. Corriger les CRITICAL (aujourd'hui)
{commandes de mise à jour}

# 2. Corriger les HIGH (cette semaine)
{commandes de mise à jour}

# 3. Nettoyer les inutilisées (optionnel, ce sprint)
{commandes de suppression}
```
```

---

## CONTRAT DE SORTIE

```
DÉPENDANCES SCANNÉES: {N} directes, {N} transitives
DATE SCAN: {ISO datetime}

VULNÉRABILITÉS:
  CRITICAL: {N} (→ workflows/dependency-update.md en urgence)
  HIGH:     {N}
  MODERATE: {N}
  LOW:      {N}

LICENCES:
  Interdites: {N}
  À vérifier: {N}
  OK: {N}

DÉPENDANCES INUTILISÉES: {N}
DÉPENDANCES FANTÔMES: {N}

DEPLOY GATE: CLEAR | BLOCKED ({N} critical/high)

RAPPORT: audit-results/report.md
DONNÉES BRUTES: audit-results/*.json
```

**HANDOFF JSON :**
```json
{
  "scan_date": "...",
  "total_dependencies": 0,
  "vulnerabilities": {
    "critical": [],
    "high": [],
    "moderate": [],
    "low": []
  },
  "license_issues": {
    "forbidden": [],
    "review_needed": []
  },
  "unused_dependencies": [],
  "phantom_dependencies": [],
  "deploy_gate": "clear|blocked",
  "report_path": "audit-results/report.md",
  "next_workflow": "dependency-update"
}
```
