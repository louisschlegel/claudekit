# Workflow: Notebook Review

## Quand utiliser
- Review d'un notebook avant merge/publication
- Debug d'un notebook avec des résultats inattendus
- Validation de reproductibilité

## Vérifications automatiques

### Ordre d'exécution
```bash
jupyter nbconvert --to script notebook.ipynb --stdout | python3 -c "
import sys
code = sys.stdin.read()
# Vérifier imports en haut, pas de side effects globaux, etc.
print('OK')
"
```

### Reproductibilité
- Toutes les cells sont-elles dans l'ordre ?
- Pas de références à des chemins absolus
- Seeds fixées pour numpy/torch/random
- Pas de cellules avec sortie mais sans code visible

### Qualité
- Docstring/markdown expliquant le but de chaque section
- Pas de code mort (cellules vides ou commentées)
- Visualisations avec titres et labels

## Agent recommandé
Invoquer `data-engineer` + `reviewer` en séquence.
