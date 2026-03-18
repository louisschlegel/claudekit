# Workflow: Dependency Update

## DÉCLENCHEUR
Intent classifié comme `update-dependencies` ou `deps`.
Commande directe : "mets à jour les dépendances", "update deps", "CVE détectée".
Automatique : `security-auditor` identifie des vulnérabilités dans les dépendances.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — identifier les vulnérabilités
2. **Reviewer** — vérifier que les updates ne cassent rien
3. **Tester** — valider après update

---

## ÉTAPE 1 — Audit des dépendances actuelles

```bash
# Python
pip-audit --requirement requirements.txt 2>/dev/null
pip list --outdated 2>/dev/null

# Node
npm audit --audit-level=moderate
npm outdated

# Go
govulncheck ./...
go list -u -m all 2>/dev/null

# Rust
cargo audit
cargo outdated

# Ruby
bundle audit check --update
bundle outdated

# Java/Gradle
./gradlew dependencyUpdates
```

Classer par :
- **CRITIQUE** : CVE active, score CVSS ≥ 7
- **HAUTE** : CVE confirmée, score CVSS 4-7
- **MAINTENANCE** : outdated mais pas de vulnérabilité connue

---

## ÉTAPE 2 — Stratégie de mise à jour

**Rule de base :** toujours tester après chaque update.

```
Pour chaque dépendance à updater :
1. Lire le CHANGELOG entre version actuelle et version cible
2. Identifier les breaking changes
3. Updater une dépendance à la fois (ou par groupe cohérent)
```

**Grouper les updates par risque :**
- Groupe 1 : patch versions (X.Y.Z → X.Y.Z+1) — faible risque
- Groupe 2 : minor versions (X.Y.0 → X.Y+1.0) — vérifier CHANGELOG
- Groupe 3 : major versions (X.Y.Z → X+1.0.0) — update dédiée, révision complète

---

## ÉTAPE 3 — Appliquer les updates

### Python
```bash
# Sécurité urgente
pip install --upgrade [package]==[new_version]
pip freeze > requirements.txt  # ou mettre à jour pyproject.toml

# Toutes les mises à jour
pip install --upgrade [packages...]
```

### Node
```bash
# Patch uniquement (sûr)
npm update

# Specific package
npm install [package]@latest

# Vérifier peer deps
npm install --legacy-peer-deps  # si conflits

# Mettre à jour package-lock.json
npm install
```

### Go
```bash
go get [module]@[version]
go mod tidy
```

### Rust
```bash
cargo update [crate]
# ou dans Cargo.toml
```

---

## ÉTAPE 4 — Vérifier après update

```bash
# Tests complets
[test_command du manifest]

# Build
[build_command si applicable]

# Smoke test
[smoke_tests si définis dans manifest]
```

Si des tests cassent après update → identifier le breaking change dans le CHANGELOG et adapter le code.

---

## ÉTAPE 5 — Review du diff

Invoquer `reviewer` sur :
- Les changements dans les lock files / requirements
- Le code adapté aux breaking changes

Gate : `VERDICT: APPROVED`.

---

## ÉTAPE 6 — Commit et documentation

```bash
# Un commit par groupe d'updates (pas tout en un)
git add requirements.txt package-lock.json go.sum Cargo.lock
git commit -m "chore(deps): update [packages] for security/maintenance

Security fixes:
- [CVE-xxx]: [package] [old] → [new]

Maintenance:
- [package]: [old] → [new]"
```

Mettre à jour `learning.md` si une update a nécessité du code d'adaptation :
```markdown
### [date] — Dependency update [package] [version]
- **Breaking change** : [description]
- **Adaptation** : [fichier:ligne] — [changement fait]
```

---

## CONTRAT DE SORTIE

```
AUDIT: [date]
VULNERABILITIES: N CRITICAL, N HIGH, N MEDIUM

UPDATES APPLIED:
  Security: [liste package: old → new]
  Maintenance: [liste si applicable]

BREAKING CHANGES: none / [liste adaptations]
TESTS: all passing
REVIEW: APPROVED

COMMIT: [hash]
LEARNING.MD: updated / not needed
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "packages_updated": 0,
  "breaking_changes": [],
  "security_fixes": 0,
  "pr_created": false
}
```
