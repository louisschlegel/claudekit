---
description: Quick security scan — runs semgrep, secret detection, dep audit
triggers:
  - /security-scan
  - /sec-scan
---

# Security Scan rapide

Lance un scan de sécurité rapide du codebase en cours. Ne remplace pas un audit complet mais couvre les problemes les plus courants en quelques secondes.

## Steps

### 1. Semgrep OWASP Top 10

```bash
semgrep --config=p/owasp-top-ten . --quiet 2>/dev/null \
  && echo "Semgrep scan completed" \
  || echo "Semgrep not installed — skip (install: pip install semgrep)"
```

### 2. Secret detection

```bash
# Essayer gitleaks en priorité, fallback sur trufflehog, puis grep manuel
if command -v gitleaks &>/dev/null; then
  gitleaks detect --source . --no-git --report-format json --report-path /dev/stdout 2>/dev/null
elif command -v trufflehog &>/dev/null; then
  trufflehog filesystem . --json 2>/dev/null
else
  echo "No secret scanner installed — running manual grep patterns"
  # Fallback : patterns critiques
  grep -rn 'AKIA[0-9A-Z]\{16\}' . --include='*.py' --include='*.js' --include='*.ts' --include='*.go' --include='*.yaml' --include='*.yml' --include='*.json' --include='*.env' 2>/dev/null
  grep -rn 'BEGIN.*PRIVATE KEY' . --include='*.pem' --include='*.key' --include='*.py' --include='*.js' 2>/dev/null
  grep -rn 'password\s*=\s*["\x27][^"\x27]\{8,\}' . --include='*.py' --include='*.js' --include='*.ts' --include='*.go' 2>/dev/null
fi
```

### 3. Dependency audit

```bash
# Detecter la stack et lancer l'audit approprié
if [ -f requirements.txt ] || [ -f pyproject.toml ]; then
  pip-audit 2>/dev/null || safety check 2>/dev/null || echo "pip-audit/safety not installed"
fi
if [ -f package-lock.json ] || [ -f package.json ]; then
  npm audit --audit-level=high 2>/dev/null || echo "npm audit failed"
fi
if [ -f go.sum ]; then
  govulncheck ./... 2>/dev/null || echo "govulncheck not installed"
fi
if [ -f Cargo.lock ]; then
  cargo audit 2>/dev/null || echo "cargo-audit not installed"
fi
```

### 4. Trivy filesystem scan (si disponible)

```bash
trivy fs . --severity HIGH,CRITICAL --quiet 2>/dev/null \
  || echo "Trivy not installed — skip (install: brew install trivy)"
```

### 5. Rapport

Resumer les findings par criticite :
- **CRITICAL** : proposer immediatement un fix inline
- **HIGH** : decrire le probleme et le fix recommande
- **MEDIUM/LOW** : lister pour reference

Format de sortie :
```
QUICK SCAN RESULTS
==================
Secrets:     N findings
OWASP:       N findings
Deps:        N vulnerabilities
Total:       N (N critical, N high, N medium, N low)

[Details par finding CRITICAL/HIGH]
```
