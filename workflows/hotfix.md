# Workflow: Hotfix

## DÉCLENCHEUR
Intent classifié comme `hotfix` ou `emergency` par le hook UserPromptSubmit.
Commande directe : "hotfix", "urgence prod", "correctif immédiat", "ça crashe en prod".

**Différence avec bugfix :** le hotfix va directement sur la branche de production (`main`/`release`) sans passer par `develop`. Tolérance aux gates plus élevée — vitesse prime.

## AGENTS IMPLIQUÉS
1. **Debug Detective** — root cause analysis (EXPRESS — max 15 min)
2. **Implementer** (Claude orchestrateur) — fix minimal
3. **Reviewer** — review rapide (focus correctness uniquement)
4. **Deployer** — déploiement immédiat

---

## ÉTAPE 0 — Triage (immédiat)

```
Évaluer la sévérité :
- CRITIQUE : service down, perte de données, faille de sécurité active
- ÉLEVÉE : feature principale cassée pour tous les utilisateurs
- MOYENNE → utiliser workflow bugfix normal

Si CRITIQUE → continuer. Si non → rediriger vers bugfix.
```

Notifier l'équipe si `notifications` configuré dans le manifest.

---

## ÉTAPE 1 — Branch hotfix depuis production

```bash
# TOUJOURS partir du tag de production, pas de develop
LAST_TAG=$(git describe --tags --abbrev=0)
git checkout -b hotfix/[description-courte] $LAST_TAG
```

---

## ÉTAPE 2 — Root Cause (EXPRESS)

Invoquer `debug-detective` avec contrainte temps :
```
Mode : EXPRESS (max 15 min)
Bug : [symptôme + erreurs observées + heure d'apparition]
Focus : identifier le fichier et la ligne, pas besoin des 5 whys complets
```

Si la cause n'est pas trouvée en 15 min → escalader à l'humain.

---

## ÉTAPE 3 — Fix minimal

**Règle absolue : le changement le plus petit possible.**
- Pas de refactoring
- Pas d'amélioration
- Pas de cleanup
- Un seul fichier si possible

```bash
git commit -m "hotfix: [description en 1 ligne]

Fixes: [symptôme]
Root cause: [cause]"
```

---

## ÉTAPE 4 — Review rapide

Invoquer `reviewer` en mode **EXPRESS** :
```
Focus : correctness uniquement (est-ce que ça corrige le bug sans casser autre chose ?)
Ignorer : style, documentation, conventions non-critiques
Timeboxe : 5 minutes
```

Gate légère : un seul BLOCKER suffit à rejeter. Les WARNINGs passent.

---

## ÉTAPE 5 — Tests minimum

```bash
# Juste les tests qui couvrent le code modifié
pytest tests/test_[module_modifié].py -q
# ou
npm test -- --testPathPattern="[module]"
```

Si pas de test pour ce code → documenter dans REGRESSION_TEST (à créer après la crise).

---

## ÉTAPE 6 — Déploiement immédiat

Invoquer `deployer` en mode hotfix :
```
Version : hotfix-[timestamp]
Environment : production (skip staging si CRITIQUE)
Rollback plan : git revert [commit] + redéployer
```

---

## ÉTAPE 7 — Merge back (après la crise)

```bash
# Merger dans main ET develop (eviter que le hotfix soit perdu au prochain merge)
git checkout main && git merge hotfix/[nom]
git checkout develop && git merge hotfix/[nom]  # si gitflow
git tag -a v[X.Y.Z+1] -m "Hotfix [description]"
git branch -d hotfix/[nom]
```

---

## ÉTAPE 8 — Post-mortem (dans les 24h)

Mettre à jour `learning.md` :
```markdown
### [date] — Hotfix [description]
- **Incident** : [description de l'impact]
- **Durée** : [heure détection] → [heure résolution]
- **Root cause** : [cause racine]
- **Fix** : [fichier:ligne] — [changement]
- **Prévention** : [test de régression + process à améliorer]
- **Timeline** : [si instructif]
```

---

## CONTRAT DE SORTIE

```
HOTFIX: [description]
SEVERITY: CRITICAL / HIGH
DURATION: [heure début] → [heure résolution]

ROOT CAUSE: [description]
FIX: [fichier:ligne] — [changement]
REVIEW: APPROVED (express)
DEPLOYED: production

MERGE BACK: main ✓ | develop ✓ | tagged: v[X.Y.Z]
REGRESSION TEST: pending (to be written in next session)
POST-MORTEM: learning.md updated
```
