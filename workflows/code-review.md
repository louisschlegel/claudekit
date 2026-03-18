# Workflow: Code Review

**Déclenché par :** `[INTENT:code-review]` — mots-clés : "review cette PR", "relis ce code", "code review", "analyse ces changements", "review le diff", "donne moi un review", "relecture"

**Agents impliqués :** explorer → security-auditor → reviewer → architect (si design concern)

---

## Vue d'ensemble

```
Diff / PR / Fichiers
        ↓
  [explorer] — Cartographie de l'impact
        ↓
  [security-auditor] — Scan vulnérabilités
        ↓
  [reviewer] — Review ligne par ligne
        ↓
  [architect] — Concerns design (si L/XL)
        ↓
  Rapport structuré BLOCKER/WARNING/SUGGESTION
        ↓
  Commentaires PR (gh pr review)
```

---

## Étape 1 — Identifier ce qui est à reviewer

```
SOURCES POSSIBLES :
□ PR GitHub ouverte → gh pr diff [PR_NUMBER]
□ Branche locale → git diff main...HEAD
□ Fichiers spécifiques → lire les fichiers mentionnés
□ Diff collé directement dans le chat

Si PR GitHub :
  gh pr view [PR_NUMBER] --json title,body,files,additions,deletions
  gh pr diff [PR_NUMBER]

Si branche locale :
  git diff main...HEAD --stat        # vue d'ensemble
  git diff main...HEAD               # diff complet
  git log main...HEAD --oneline      # commits inclus
```

**Taille du changement :**
```
□ S (< 100 lignes) → review complète en un passage
□ M (100-500 lignes) → review par module
□ L (500-2000 lignes) → review par couche (API, business logic, data, tests)
□ XL (> 2000 lignes) → demander à splitter en PRs plus petites + review partielle
```

---

## Étape 2 — Cartographie d'impact (explorer)

**Invoquer l'agent explorer** pour analyser l'impact du changement :

```
Analyser :
- Quels modules/packages sont touchés ?
- Y a-t-il des fichiers de test correspondants ?
- Quelles dépendances pourraient être affectées (imports, exports) ?
- Y a-t-il des changements de schéma (migrations) ?
- Y a-t-il des changements d'API publique (breaking changes potentiels) ?
- Fichiers de config modifiés (risque opérationnel) ?
```

**Signaux d'alerte immédiats :**
```python
HIGH_RISK_PATTERNS = [
    "auth", "login", "password", "token", "secret", "key",  # sécurité
    "migration", "schema", "alter table",                     # db
    "settings", "config", ".env",                            # config
    "deploy", "Dockerfile", "ci.yml", "cd.yml",              # infra
    "package.json", "requirements.txt", "go.mod",            # dépendances
    "middleware", "interceptor", "hook",                      # cross-cutting
]
```

---

## Étape 3 — Scan sécurité (security-auditor)

**Invoquer l'agent security-auditor** sur le diff :

Vérifications prioritaires :
```
□ Secrets hardcodés (API keys, tokens, passwords dans le code)
□ SQL injection (queries construites par concaténation de strings)
□ XSS (données utilisateur non-échappées dans le HTML)
□ IDOR (accès ressources sans vérification d'autorisation)
□ Path traversal (../../../etc/passwd)
□ Insecure deserialization (pickle.loads, eval, exec sur input)
□ SSRF (URLs construites depuis input utilisateur)
□ Mass assignment (binding de request body entier sur modèle)
□ Missing rate limiting sur endpoints sensibles
□ JWT / session : algo none, pas de vérification signature
□ Dépendances ajoutées : vérifier CVEs connus
```

**Classification sécurité :**
```
CRITICAL — Exploitable immédiatement, données en danger → BLOQUER la PR
HIGH     — Exploitable avec effort, vecteur d'attaque clair → BLOCKER
MEDIUM   — Exploitable dans certaines conditions → WARNING
LOW      — Bonne pratique de sécurité manquante → SUGGESTION
```

---

## Étape 4 — Review code (reviewer)

**Invoquer l'agent reviewer** pour la review ligne par ligne.

Structure de review par catégorie :

### 🚫 BLOCKER — Doit être corrigé avant merge

```markdown
**[BLOCKER] Ligne {N} — {fichier}**
> ```{langage}
> {code problématique}
> ```
**Problème :** {explication précise}
**Impact :** {ce qui peut se passer si mergé}
**Fix :** {correction suggérée avec code}
```

### ⚠️ WARNING — Fortement recommandé de corriger

```markdown
**[WARNING] Ligne {N} — {fichier}**
> ```{langage}
> {code concerné}
> ```
**Problème :** {explication}
**Risque :** {risque potentiel}
**Suggestion :** {amélioration}
```

### 💡 SUGGESTION — Amélioration optionnelle

```markdown
**[SUGGESTION] Ligne {N} — {fichier}**
> ```{langage}
> {code actuel}
> ```
**Idée :** {amélioration de lisibilité/perf/maintenabilité}
**Alternative :**
> ```{langage}
> {code amélioré}
> ```
```

### ✅ BIEN — Ce qui est fait correctement (positif)

```markdown
**[✅] {fichier} — {ce qui est bien fait}**
{pourquoi c'est une bonne pratique}
```

**Checklist reviewer :**
```
□ Nommage : variables, fonctions, classes explicites ?
□ Fonctions : font une seule chose, < 50 lignes ?
□ DRY : duplication évitée ?
□ Error handling : cas d'erreur gérés explicitement ?
□ Types : annotations/types corrects (si TypeScript/Python typé) ?
□ Tests : tests correspondants ajoutés/modifiés ?
□ Tests : cas limites couverts (null, vide, limites) ?
□ Logs : logs utiles sans données sensibles ?
□ Documentation : fonctions publiques documentées ?
□ Performance : N+1 queries ? loops imbriquées ? allocations inutiles ?
□ Migrations : backward compatible ? rollback possible ?
□ Breaking changes : changelog mis à jour ?
```

---

## Étape 5 — Review architecture (architect, si L/XL)

Si le changement est L ou XL, ou s'il touche des couches structurantes :

**Invoquer l'agent architect** pour :
```
□ Le design respecte-t-il les patterns établis dans learning.md ?
□ Introduction de nouvelles abstractions : sont-elles justifiées ?
□ Couplage : le changement augmente-t-il le couplage entre modules ?
□ Cohésion : chaque module reste-t-il focalisé ?
□ Extensibilité : le design permet-il les évolutions probables ?
□ SOLID : principes respectés ?
□ Performance : hotpaths identifiés, structures de données adaptées ?
```

---

## Étape 6 — Synthèse et publication

### Rapport de synthèse

```markdown
## Code Review — {titre PR ou branche}

**Reviewer :** Claude ({date})
**Scope :** {N fichiers, +{additions} / -{deletions} lignes}
**Durée de review :** {estimation}

### Verdict

| Catégorie | Count |
|-----------|-------|
| 🚫 BLOCKER | {N} |
| ⚠️ WARNING | {N} |
| 💡 SUGGESTION | {N} |
| ✅ Points positifs | {N} |

**→ Statut : {APPROVED / REQUEST CHANGES / COMMENT}**

---

### 🚫 BLOCKERs (must fix)
{liste des blockers}

### ⚠️ WARNINGs (should fix)
{liste des warnings}

### 💡 SUGGESTIONs (nice to have)
{liste des suggestions}

### ✅ Bien fait
{liste des points positifs}

---

### Résumé
{1-3 phrases sur la qualité globale et les principaux axes d'amélioration}
```

### Publication sur GitHub (optionnel, confirmer avec l'utilisateur)

```bash
# Review avec commentaires inline
gh pr review [PR_NUMBER] \
  --request-changes \
  --body "$(cat review-report.md)"

# Si approved
gh pr review [PR_NUMBER] \
  --approve \
  --body "LGTM. {commentaire positif}"

# Commentaires inline sur des lignes spécifiques
gh api repos/{owner}/{repo}/pulls/{PR_NUMBER}/comments \
  --method POST \
  --field body="{commentaire}" \
  --field commit_id="{sha}" \
  --field path="{fichier}" \
  --field position={ligne}
```

⚠️ **Toujours confirmer avec l'utilisateur avant de publier** — la review devient publique.

---

## CONTRAT DE SORTIE

```
PR/DIFF REVIEWÉ: [titre ou hash]
SCOPE: [N fichiers, +adds/-dels]

VERDICT: APPROVED | REQUEST CHANGES | COMMENT

BLOCKERS:   [N] (liste)
WARNINGS:   [N] (liste)
SUGGESTIONS:[N] (liste)
POSITIFS:   [N] (liste)

SÉCURITÉ: CLEAN | {N} findings ({severities})
TESTS: COUVERTS | MANQUANTS ({liste})
BREAKING CHANGES: OUI | NON

PUBLIÉ SUR GITHUB: OUI | NON (en attente confirmation)
```

**HANDOFF JSON :**
```json
{
  "pr_number": null,
  "branch": "...",
  "scope": {"files": 0, "additions": 0, "deletions": 0},
  "verdict": "approved|request_changes|comment",
  "blockers": [{"file": "...", "line": 0, "issue": "..."}],
  "warnings": [{"file": "...", "line": 0, "issue": "..."}],
  "suggestions": [{"file": "...", "line": 0, "idea": "..."}],
  "security_findings": [{"severity": "HIGH", "type": "...", "location": "..."}],
  "missing_tests": ["..."],
  "breaking_changes": false,
  "published_to_github": false
}
```
