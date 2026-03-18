# Workflow: Release

## DÉCLENCHEUR
Intent classifié comme `release` par le hook UserPromptSubmit.
Commande directe : "release", "prépare une version", "tag vX.Y.Z".

## AGENTS IMPLIQUÉS
1. **Security Auditor** — gate sécurité
2. **Release Manager** — orchestration
3. **Doc Writer** — changelog
4. **Deployer** — déploiement

---

## ÉTAPE 1 — Déterminer le type de release

L'utilisateur spécifie ou le release-manager infère depuis les commits :
```
patch  → corrections de bugs, pas de nouvelle feature
minor  → nouvelles features, rétrocompatible
major  → breaking changes
```

Si ambiguïté → demander confirmation avant de continuer.

---

## ÉTAPE 2 — Gate : Tests complets

```bash
# Lancer la suite complète
[test_command du manifest]
```

Si des tests échouent → **STOP**. Corriger avant de continuer (workflow bugfix).

---

## ÉTAPE 3 — Gate : Security Audit

Invoquer `security-auditor` avec :
```
Scope : tous les fichiers modifiés depuis le dernier tag
Stack : [manifest stack]
```

Gate stricte :
- `RELEASE_GATE: PASS` → continuer
- `RELEASE_GATE: BLOCK` → **STOP**. Corriger les CRITICAL/HIGH avant de continuer.

---

## ÉTAPE 4 — Gate : Code Review (si non déjà effectuée)

Invoquer `reviewer` sur le diff complet depuis le dernier tag.
Gate : `VERDICT: APPROVED`.

---

## ÉTAPE 5 — Préparer la release

Invoquer `release-manager` avec :
```
Type : patch/minor/major
Commits : [git log depuis dernier tag]
```

Le release-manager :
- Bumpe la version dans les fichiers appropriés
- Génère l'entrée CHANGELOG.md
- Crée le commit de release
- Crée le tag git signé

---

## ÉTAPE 6 — Documentation

Invoquer `doc-writer` pour :
- Vérifier que le README est à jour (version, nouvelles features)
- Valider que toutes les fonctions publiques sont documentées

---

## ÉTAPE 7 — Déploiement (si `workflow.auto_deploy: true`)

Invoquer `deployer` avec :
```
Version : vX.Y.Z
Environment : staging (puis production après validation)
```

Si `auto_deploy: false` → instruire l'utilisateur pour déployer manuellement.

---

## ÉTAPE 8 — Post-release

```bash
# Push tag
git push origin vX.Y.Z
git push origin main
```

Si `workflow.github_releases: true` :
```bash
gh release create vX.Y.Z --notes-file CHANGELOG_ENTRY.md
```

Mettre à jour `project.manifest.json` → `project.version`.

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque release, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output du security-auditor → findings HIGH/CRITICAL → section "Bugs résolus" [SÉCURITÉ]
python3 scripts/auto-learn.py --from-agent security-auditor --input '[JSON_OUTPUT_SECURITY_AUDITOR]'

# Output du reviewer → BLOCKERs récurrents → section "Patterns"
python3 scripts/auto-learn.py --from-agent reviewer --input '[JSON_OUTPUT_REVIEWER]'
```

Si `--extract-patterns` retourne des custom_rules candidates avec confiance HIGH → proposer à l'utilisateur de les ajouter dans `project.manifest.json` :

```bash
python3 scripts/auto-learn.py --extract-patterns
```

---

## CONTRAT DE SORTIE

```
RELEASE: vX.Y.Z (patch/minor/major)
DATE: YYYY-MM-DD

GATES:
  ✓ Tests (N passed, 0 failed)
  ✓ Security (PASS)
  ✓ Review (APPROVED)

CHANGELOG:
  [entrée générée]

TAG: vX.Y.Z created
DEPLOY: staging OK / production OK / pending

ARTIFACTS:
  - CHANGELOG.md updated
  - project.manifest.json version updated
  - GitHub Release: [url si applicable]
  - LEARNING.MD: updated (via auto-learn.py)
```
