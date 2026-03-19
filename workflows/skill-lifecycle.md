# Workflow: Skill Lifecycle

Détecter un pattern appris → extraire une skill → évaluer → intégrer → auto-load.

## Étapes

### 1. Détection
- Observer les corrections récurrentes dans `learning.md`
- Identifier les workarounds découverts pendant le debug
- Repérer les patterns validés par l'utilisateur ("oui exactement", "parfait")
- Seuil : pattern vu 3+ fois ou explicitement demandé

### 2. Extraction
- Créer `.claude/skills/<name>/SKILL.md` avec :
  ```yaml
  ---
  name: skill-name
  description: One-line description
  triggers: ["keyword1", "keyword2"]
  ---
  ```
- Rédiger les instructions concrètes et actionnables
- Inclure des exemples d'input/output
- Ajouter `eval_criteria` pour l'auto-évaluation

### 3. Évaluation (via /auto-research)
- Définir 3-5 cas de test
- Exécuter la skill sur chaque cas
- Évaluer avec critères binaires PASS/FAIL
- Taux de réussite minimum : 80%

### 4. Intégration
- Si pass rate >= 80% : merger dans `.claude/skills/`
- Mettre à jour l'index des skills
- Supprimer les entrées correspondantes de `learning.md`
- Logger dans `.template/improvements.log`

### 5. Monitoring
- Suivre l'utilisation de la skill (via agent-events.jsonl)
- Si jamais utilisée après 30 jours → candidat à la suppression
- Si corrections fréquentes → re-évaluer

## HANDOFF JSON

```json
{
  "workflow": "skill-lifecycle",
  "status": "complete",
  "skill_name": "cursor-pagination",
  "source": "learning.md pattern (seen 4 times)",
  "eval_results": {"pass_rate": "100%", "test_cases": 3},
  "integrated": true,
  "learning_md_cleaned": true
}
```

## CONTRAT DE SORTIE

- [ ] Pattern identifié avec au moins 3 occurrences
- [ ] SKILL.md créé avec frontmatter valide
- [ ] Évaluation exécutée avec taux >= 80%
- [ ] Skill intégrée dans `.claude/skills/`
- [ ] learning.md nettoyé des entrées promues
- [ ] HANDOFF JSON produit
