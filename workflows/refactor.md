# Workflow: Refactor

## DÉCLENCHEUR
Intent classifié comme `refactor` par le hook UserPromptSubmit.
Commande directe : "refactore", "nettoie", "améliore la structure de".

## AGENTS IMPLIQUÉS
1. **Architect** — stratégie de refactoring
2. **Explorer** — cartographie avant refactoring
3. **Implementer** (Claude orchestrateur) — refactoring
4. **Tester** — s'assurer que les tests couvrent le périmètre
5. **Reviewer** — validation

---

## PRINCIPE FONDAMENTAL

**Un refactoring ne change pas le comportement observable.**
Si le comportement change → c'est une feature ou un bugfix, pas un refactoring.

Règle : les tests existants doivent passer avant ET après le refactoring, sans modification.

---

## ÉTAPE 1 — Définir le périmètre et l'objectif

Clarifier avec l'utilisateur :
- [ ] Périmètre exact (fichier, module, package)
- [ ] Objectif : lisibilité / découplage / performance / conventions / dette technique
- [ ] Contrainte : est-ce qu'on peut modifier les interfaces publiques ?

---

## ÉTAPE 2 — Snapshot des tests existants

```bash
# Vérifier que tous les tests passent AVANT de toucher au code
[test_command du manifest]
```

Si des tests échouent avant de commencer → **STOP**. Le refactoring ne peut pas commencer sur une base instable.

---

## ÉTAPE 3 — Cartographie (si périmètre > 3 fichiers)

Invoquer `explorer` sur le périmètre :
```
Scope : [liste des fichiers/modules]
Focus : dépendances inter-modules, points de couplage
```

---

## ÉTAPE 4 — Stratégie de refactoring

Invoquer `architect` avec :
```
Contexte : [rapport de l'explorer]
Problème : [dette technique identifiée]
Contrainte : comportement observable inchangé
Demande : stratégie de refactoring en petites étapes atomiques
```

Décomposer en étapes indépendantes et testables séparément.

---

## ÉTAPE 5 — Refactoring incrémental

Pour chaque étape de la stratégie :
```
1. Appliquer le changement
2. Vérifier que les tests passent
3. Commit atomique : "refactor: [description précise]"
```

**Ne jamais laisser les tests en échec entre deux étapes.**

Patterns de refactoring communs :
- **Extract function/method** : décomposer une fonction trop longue
- **Rename** : améliorer la lisibilité
- **Move** : réorganiser les modules
- **Replace conditional with polymorphism**
- **Introduce parameter object**
- **Remove dead code**

---

## ÉTAPE 6 — Compléter la couverture (si nécessaire)

Invoquer `tester` si certaines parties refactorisées ne sont pas couvertes.
Objectif : avoir suffisamment de tests pour être confiant que le comportement est préservé.

---

## ÉTAPE 7 — Review

Invoquer `reviewer` avec :
```
Diff : git diff [branch-base]..HEAD
Focus : correctness (comportement inchangé), conventions respectées
```

Gate : `VERDICT: APPROVED`.

---

## ÉTAPE 8 — Mettre à jour `learning.md`

Si des patterns ou conventions émergent du refactoring → les documenter dans la section "Patterns".

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque refactoring complété, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output de l'architect → décisions de refactoring → section "Architecture & Décisions"
python3 scripts/auto-learn.py --from-agent architect --input '[JSON_OUTPUT_ARCHITECT]'

# Output du reviewer → patterns émergents → section "Patterns"
python3 scripts/auto-learn.py --from-agent reviewer --input '[JSON_OUTPUT_REVIEWER]'
```

Si `--extract-patterns` retourne des custom_rules candidates avec confiance HIGH → proposer à l'utilisateur de les ajouter dans `project.manifest.json` :

```bash
python3 scripts/auto-learn.py --extract-patterns
```

---

## CONTRAT DE SORTIE

```
REFACTOR: [description]
SCOPE: N fichiers
OBJECTIVE: [objectif atteint]

CHANGES:
  - [fichier] : [changement]
  ...

TESTS:
  Before: N passing
  After: N passing (same)
  Added: N (if coverage gap found)

REVIEW: APPROVED
LEARNING.MD: updated (via auto-learn.py)

BEHAVIOR CHANGE: none (verified)
```
