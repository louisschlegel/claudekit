# Workflow: Self-Improve

## DÉCLENCHEUR
Intent classifié comme `improve-template` par le hook UserPromptSubmit.
Commande : "améliore le template", "self-improve", "mets-toi à jour".
Automatique : `stop.sh` détecte que le seuil d'auto-amélioration est atteint.

## AGENTS IMPLIQUÉS
1. **Template Improver** — analyse et applique les améliorations

---

## PRINCIPE

Ce workflow est méta : il améliore le template lui-même, pas le projet.
L'agent `template-improver` est le seul autorisé à modifier les fichiers du template.

---

## ÉTAPE 1 — Vérifier les données disponibles

```bash
# Combien d'observations dans improvements.log ?
wc -l .template/improvements.log 2>/dev/null || echo "0 observations"

# Version actuelle du template
cat .template/version.json 2>/dev/null
```

Si moins de 3 observations → informer l'utilisateur qu'il n'y a pas assez de données.
Continuer quand même si l'utilisateur le demande explicitement.

---

## ÉTAPE 2 — Invoquer template-improver

Invoquer `template-improver` avec :
```
Fichiers de données :
- .template/improvements.log (observations)
- .template/known-patterns.json (patterns en attente)
- .template/version.json (version actuelle)
- learning.md (contexte projet)

Demande : analyser, classer, appliquer selon la matrice confiance/risque
```

---

## ÉTAPE 3 — Revue des améliorations proposées

Le template-improver présente :

**Améliorations AUTO (appliquées directement) :**
```
Ces changements ont été appliqués automatiquement.
[liste avec fichiers modifiés]
```

**Améliorations APPROVAL_REQUIRED (attendent ta validation) :**
```
Pour chaque amélioration :
- Description du changement
- Justification
- Diff proposé

[Approuver/Rejeter chaque changement]
```

**Améliorations PR (trop risquées pour appliquer directement) :**
```
Ces changements ont été créés sur une branch pour review :
- Branch : template-improvement/vX.Y.Z
[Créer PR si demandé]
```

---

## ÉTAPE 4 — Validation des améliorations approuvées

Après application :
```bash
# Vérifier que le template fonctionne encore
python3 scripts/gen.py  # doit s'exécuter sans erreur
bash .claude/hooks/session-start.sh  # doit s'exécuter sans erreur
```

Si une amélioration casse le template → la reverter immédiatement.

---

## ÉTAPE 5 — Version bump et commit

```bash
python3 scripts/version-bump.py [patch/minor/major]

git add .claude/ scripts/ workflows/ .template/
git commit -m "chore(template): self-improve vOLD → vNEW

Improvements applied:
- [liste]"
```

---

## ÉTAPE 6 — Nettoyer les observations traitées

```bash
python3 scripts/self-improve.py --clear-processed
```

---

## CONTRAT DE SORTIE

```
TEMPLATE VERSION: [avant] → [après]
DATE: YYYY-MM-DD

IMPROVEMENTS APPLIED: N
  AUTO: N (détail)
  APPROVED: N (détail)

IMPROVEMENTS PENDING APPROVAL: N
IMPROVEMENTS QUEUED (low confidence): N

TEMPLATE HEALTH:
  gen.py: ✓ working
  session-start.sh: ✓ working

NEXT AUTO-IMPROVE: dans [N] sessions
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "version_from": "...",
  "version_to": "...",
  "improvements_applied": 0,
  "type": "AUTO|APPROVAL|PR",
  "learning_entries_added": 0
}
```
