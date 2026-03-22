---
name: evolve
description: Lance le cycle d'evolution Homunculus — clustering d'instincts et proposition de promotion en skills ou regles CLAUDE.md
triggers:
  - /evolve
  - /homunculus
  - "lance le cycle homunculus"
  - "evolve instincts"
  - "promouvoir les instincts"
---

# Skill: /evolve

Lance le cycle d'auto-evolution claudekit (pattern Homunculus).

## Protocole

1. Recalcule les clusters d'instincts par domaine :
   `python3 scripts/instinct-loop.py --cluster`

2. Affiche les clusters candidats a promotion (maturite >= 0.6, >= 3 instincts) :
   `python3 scripts/instinct-loop.py --show-candidates`

3. Si des candidats existent, genere les propositions :
   `python3 scripts/instinct-loop.py --generate-proposal`

4. Presente les resultats a l'utilisateur :
   - Propositions de fichiers `.claude/skills/instinct-{domain}.md`
   - Propositions de blocs a inserer dans `CLAUDE.md`

5. L'utilisateur valide et copie ce qu'il veut integrer.
   Aucune modification automatique — la validation est obligatoire.

## Raccourci complet

```bash
bash scripts/evolve.sh
```

## Ajouter une observation manuellement

```bash
python3 scripts/instinct-loop.py --add-observation "trigger" "action" "domain"
```

Domaines disponibles : testing, security, git, style, architecture, performance,
documentation, workflow, ml, data, devops, refactor, review, other.

## Voir le rapport complet

```bash
python3 scripts/instinct-loop.py --report
```

## Output attendu

```json
{
  "clusters_recalculated": 3,
  "candidates": 1,
  "proposals_generated": ["instinct-testing.md", "CLAUDE.md block: testing"]
}
```
