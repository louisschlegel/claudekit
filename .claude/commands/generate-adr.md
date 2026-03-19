# Command: /generate-adr

Génère un Architecture Decision Record (ADR) selon le modèle C4.

## Usage
`/generate-adr <titre de la décision>`

## Protocole

1. **Numérotation** : lire `docs/architecture/` et trouver le prochain numéro (adr-001, adr-002, etc.)
2. **Créer le fichier** `docs/architecture/adr-XXX-<slug>.md` avec ce template :

```markdown
# ADR-XXX: <Titre>

**Statut** : Proposé | Accepté | Déprécié | Remplacé par ADR-YYY
**Date** : YYYY-MM-DD
**Décideurs** : @auteur

## Contexte

Quel est le problème ou l'opportunité qui motive cette décision ?

## Décision

Quelle est la décision prise et pourquoi ?

## Conséquences

### Positives
- ...

### Négatives
- ...

### Neutres
- ...

## Alternatives considérées

### Alternative 1 : <nom>
- Avantages : ...
- Inconvénients : ...
- Raison du rejet : ...

## Références
- Liens vers docs, issues, ou discussions
```

3. **Mettre à jour l'index** si `docs/architecture/README.md` existe
