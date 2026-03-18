# Workflow: Security Audit

## DÉCLENCHEUR
Intent classifié comme `audit` par le hook UserPromptSubmit.
Commande directe : "audit sécurité", "vérifie la sécurité", "scan".
Automatique : gate dans `workflows/release.md`.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — scan principal
2. **Reviewer** — validation des fixes
3. **Debug Detective** — analyse des vulnérabilités complexes (si besoin)

---

## ÉTAPE 1 — Définir le scope

Scope par défaut : tous les fichiers modifiés depuis le dernier tag.
Scope élargi si demande explicite : tout le codebase.

```bash
# Fichiers modifiés depuis le dernier tag
git diff $(git describe --tags --abbrev=0)..HEAD --name-only
```

---

## ÉTAPE 2 — Audit principal

Invoquer `security-auditor` avec :
```
Scope : [liste des fichiers]
Stack : [manifest stack]
Mode : pre-release / full-scan / targeted
```

Le security-auditor effectue les 5 scans :
1. Secrets exposés
2. Injections (adapté au stack)
3. Authentification & Autorisation
4. Dépendances vulnérables
5. Configuration

---

## ÉTAPE 3 — Traitement des findings

### CRITICAL (traitement immédiat obligatoire)
```
Pour chaque finding CRITICAL :
1. Localiser le problème exact (fichier:ligne)
2. Proposer un fix immédiat
3. Implémenter le fix
4. Vérifier que le finding est résolu
```

### HIGH (traitement avant release)
```
Même process que CRITICAL.
Si le fix est complexe → créer une branch fix/security-[cwe]
```

### MEDIUM (à planifier)
```
Créer une issue ou TODO avec :
- Référence CWE
- Fichier:ligne
- Fix recommandé
- Délai suggéré
```

### LOW (optionnel)
```
Documenter dans learning.md pour référence future.
Traiter si la maintenance le permet.
```

---

## ÉTAPE 4 — Vérification des fixes

Pour chaque fix CRITICAL/HIGH :
- Re-invoquer `security-auditor` sur le fichier corrigé
- Vérifier : finding disparu
- Invoquer `reviewer` sur le diff du fix

---

## ÉTAPE 5 — Rapport final

Documenter dans `learning.md` section "Bugs" :
```markdown
### [date] — Audit sécurité vX.Y.Z
- **Findings** : N CRITICAL, N HIGH, N MEDIUM, N LOW
- **Resolus** : N
- **Patterns à éviter** : [liste]
```

---

## ÉTAPE FINALE — Auto-apprentissage

Après chaque audit sécurité complété, passer les outputs JSON des agents à auto-learn.py :

```bash
# Output du security-auditor → findings HIGH/CRITICAL → section "Bugs résolus" [SÉCURITÉ]
python3 scripts/auto-learn.py --from-agent security-auditor --input '[JSON_OUTPUT_SECURITY_AUDITOR]'

# Si des vulnérabilités complexes ont nécessité debug-detective
python3 scripts/auto-learn.py --from-agent debug-detective --input '[JSON_OUTPUT_DEBUG_DETECTIVE]'

# Output du reviewer sur les fixes → vérifier patterns récurrents
python3 scripts/auto-learn.py --from-agent reviewer --input '[JSON_OUTPUT_REVIEWER]'
```

Si `--extract-patterns` retourne des custom_rules candidates avec confiance HIGH → proposer à l'utilisateur de les ajouter dans `project.manifest.json` :

```bash
python3 scripts/auto-learn.py --extract-patterns
```

---

## CONTRAT DE SORTIE

```
AUDIT SCOPE: [N fichiers]
DATE: YYYY-MM-DD

FINDINGS:
  CRITICAL: N (N resolved)
  HIGH: N (N resolved)
  MEDIUM: N (tracked)
  LOW: N (documented)

RELEASE_GATE: PASS / BLOCK

FIXES APPLIED:
  [liste des fixes]

PENDING:
  [liste des findings MEDIUM/LOW avec tracking]

LEARNING.MD: updated (via auto-learn.py)
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "scope": "...",
  "findings": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "secrets_found": false,
  "deploy_gate": "pass|fail",
  "report_path": "..."
}
```
