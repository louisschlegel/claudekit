# Workflow: Bugfix

## DÉCLENCHEUR
Intent classifié comme `bugfix` par le hook UserPromptSubmit.
Commande directe : "corrige [bug]", "bug : [description]", "ça crash quand...".

## AGENTS IMPLIQUÉS
1. **Debug Detective** — root cause analysis
2. **Tester** — test de régression
3. **Implementer** (Claude orchestrateur) — fix
4. **Reviewer** — validation du fix

---

## ÉTAPE 1 — Reproduire le bug

Vérifier que le bug est reproductible avec une commande/action précise.
Si non reproductible → demander à l'utilisateur :
1. La version exacte du code (commit hash)
2. L'environnement (OS, versions des dépendances)
3. Les données de test qui reproduisent le problème

---

## ÉTAPE 2 — Root Cause Analysis

Invoquer `debug-detective` avec :
```
Bug : [description + message d'erreur complet + stack trace]
Étapes de reproduction : [liste]
Dernier commit fonctionnel : [si connu]
```

Le debug-detective fournit :
- ROOT CAUSE
- AFFECTED FILES
- INTRODUCED BY (commit hash)
- FIX (description)
- REGRESSION TEST (description)

---

## ÉTAPE 3 — Test de régression (avant le fix)

Invoquer `tester` avec :
```
Mode : régression
Description du bug : [root cause]
Test attendu : [REGRESSION TEST du debug-detective]
```

**Règle absolue : le test de régression DOIT échouer avant le fix.**
Si le test passe déjà → le bug est peut-être déjà corrigé ou la reproduction est incorrecte.

---

## ÉTAPE 4 — Fix minimal

Implémenter le changement le plus petit possible qui corrige le bug :
- Pas de refactoring opportuniste
- Pas d'amélioration "tant qu'on est là"
- Un seul bug à la fois

```bash
git checkout -b fix/[nom-court-du-bug]
# Appliquer le fix
git commit -m "fix: [description du fix]

Fixes: [root cause en 1 phrase]
Test: [nom du test de régression ajouté]"
```

---

## ÉTAPE 5 — Vérification

```bash
# Le test de régression doit passer maintenant
pytest tests/test_regression.py -k [nom_test]
# ou
npm test -- --testNamePattern="[nom test]"

# Les tests existants ne doivent pas régresser
pytest  # ou npm test
```

---

## ÉTAPE 6 — Review du fix

Invoquer `reviewer` avec :
```
Diff : git diff main..fix/[nom]
Focus : le fix ne casse rien d'autre
```

Gate : `VERDICT: APPROVED` requis pour merger.

---

## ÉTAPE 7 — Merge et post-mortem

```bash
git checkout main
git merge --no-ff fix/[nom] -m "fix: [description]"
```

Mettre à jour `learning.md` section "Bugs" :
```markdown
### [date] — [nom du bug]
- **Symptôme** : [description]
- **Root cause** : [root cause]
- **Fix** : [fichier:ligne] — [description du changement]
- **Prévention** : [test de régression ajouté]
```

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque bugfix complété, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output du debug-detective → section "Bugs résolus" de learning.md
python3 scripts/auto-learn.py --from-agent debug-detective --input '[JSON_OUTPUT_DEBUG_DETECTIVE]'

# Output du reviewer → vérifier les patterns récurrents → section "Patterns"
python3 scripts/auto-learn.py --from-agent reviewer --input '[JSON_OUTPUT_REVIEWER]'
```

Si `--extract-patterns` retourne des custom_rules candidates avec confiance HIGH → proposer à l'utilisateur de les ajouter dans `project.manifest.json` :

```bash
python3 scripts/auto-learn.py --extract-patterns
```

---

## CONTRAT DE SORTIE

```
BUG: [description]
ROOT CAUSE: [cause racine identifiée]
INTRODUCED BY: [commit hash / inconnu]

FIX:
  File: [fichier:ligne]
  Change: [description]

REGRESSION TEST: added / not applicable
TESTS: all passing

REVIEW: APPROVED
LEARNING.MD: updated (via auto-learn.py)
```
