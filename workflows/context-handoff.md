# Workflow: Context Handoff

## Quand utiliser
- Session longue approchant la limite de contexte
- Reprise d'une tâche interrompue
- Handoff entre membres d'équipe

## Étapes

### 1. Générer le brief de handoff
À la fin de la session (ou quand le contexte > 70%), créer `.template/handoff.md` :

```markdown
# Handoff — {date}

## Tâche en cours
{description de ce qui était en train d'être fait}

## État actuel
- Fichiers modifiés : {liste}
- Décisions prises : {liste}
- Problèmes ouverts : {liste}

## Prochaines étapes
1. {étape suivante}
2. ...

## Contexte technique critique
{snippets importants, interfaces, contraintes}
```

### 2. Commiter le handoff
```bash
git add .template/handoff.md
git commit -m "chore: context handoff — {résumé}"
```

### 3. Démarrer la nouvelle session
Le hook `session-start.sh` injecte automatiquement le dernier `handoff.md` s'il existe dans `.template/`.

## Notes
- Max 1 handoff.md actif (l'ancien est archivé en `handoff-{timestamp}.md`)
- Le `pre-compact.sh` hook sauvegarde aussi dans `session-backup.md` automatiquement

---

**HANDOFF JSON (pour orchestrateur) :**
```json
{"status": "completed", "summary": "", "next_action": "", "artifacts": []}
```

## CONTRAT DE SORTIE

```
STATUS: completed
SUMMARY: [résumé des actions effectuées]
ARTIFACTS: [fichiers créés ou modifiés]
NEXT_ACTION: [prochaine étape recommandée ou none]
```
