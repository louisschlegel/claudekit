# Workflow: Feature

## DÉCLENCHEUR
Intent classifié comme `feature` par le hook UserPromptSubmit.
Commande directe : "implémente [feature]", "ajoute [feature]", "crée [feature]".

## AGENTS IMPLIQUÉS
1. **Architect** — conception
2. **Implementer** (Claude orchestrateur) — code
3. **Tester** — tests
4. **Reviewer** — review
5. **Doc Writer** — documentation

---

## ÉTAPE 1 — Clarification (si nécessaire)

Avant de commencer, vérifier que la feature est suffisamment définie :
- [ ] Objectif clair et mesurable ?
- [ ] Cas d'usage principal identifié ?
- [ ] Contraintes connues (perf, sécu, compatibilité) ?

Si non → poser les 3 questions manquantes maximum. Ne pas bloquer si la feature est simple.

---

## ÉTAPE 2 — Architecture (si feature > 2 fichiers modifiés)

Invoquer `architect` avec :
```
Contexte : [description de la feature]
Contraintes : [ce qui est connu]
Demande : propose 2-3 approches avec ADR
```

Gate : attendre la recommandation de l'architecte avant d'implémenter.
Si feature simple (1-2 fichiers) → passer directement à l'implémentation.

---

## ÉTAPE 3 — Implémentation

Créer une branch feature :
```bash
git checkout -b feat/[nom-feature]
```

Implémenter selon l'ADR validé :
- Commits atomiques et conventionnels (`feat: ...`, `fix: ...`)
- Pas de code mort ou TODO sans ticket
- Respecter les conventions du manifest et de `learning.md`

---

## ÉTAPE 4 — Tests

Invoquer `tester` avec :
```
Fichiers modifiés : [liste]
Framework : [stack.testing du manifest]
Régression : non (feature)
```

Seuil minimum : couverture des happy paths + 1 edge case par fonction.

---

## ÉTAPE 5 — Review

Invoquer `reviewer` avec :
```
Diff : git diff main..feat/[nom-feature]
Manifest : [stack + conventions]
```

Gate :
- `VERDICT: CHANGES_REQUIRED` → retour à l'implémentation (étape 3)
- `VERDICT: APPROVED` → continuer

Maximum 2 boucles implémentation → review avant escalade à l'humain.

---

## ÉTAPE 6 — Documentation

Invoquer `doc-writer` pour :
- Docstrings des nouvelles fonctions/classes publiques
- Mise à jour README si interface publique modifiée
- Mise à jour `learning.md` section "Travail en cours" → "Patterns"

---

## ÉTAPE 7 — Merge

```bash
git checkout main
git merge --no-ff feat/[nom-feature] -m "feat: [description]"
git branch -d feat/[nom-feature]
```

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque feature mergée, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output de l'architect → section "Architecture & Décisions" de learning.md
python3 scripts/auto-learn.py --from-agent architect --input '[JSON_OUTPUT_ARCHITECT]'

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
FEATURE: [nom]
STATUS: COMPLETE / BLOCKED

IMPLEMENTATION:
  Files modified: [liste]
  Tests added: N
  Coverage: X%

REVIEW: APPROVED
DOCS: updated / not applicable

BRANCH: merged / pending
LEARNING.MD: updated (via auto-learn.py)
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "feature": "...",
  "status": "complete|blocked",
  "files_modified": [],
  "tests_added": 0,
  "coverage_pct": 0,
  "review": "approved|pending",
  "branch": "...",
  "learning_updated": false
}
```
