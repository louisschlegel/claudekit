# Command: /new-entity

Génère une entité de données complète : model, migration, CRUD, tests, seed.

## Usage
`/new-entity <EntityName> [field:type field:type ...]`

Exemple : `/new-entity Product name:string price:decimal category_id:uuid:fk active:boolean`

## Protocole

1. **Parser les champs** : nom, type, contraintes (fk, nullable, unique, default)
2. **Générer selon le stack** :
   - **Model** : SQLAlchemy / Django ORM / Prisma / TypeORM
   - **Migration** : Alembic / Django makemigrations / Prisma migrate
   - **Schema** : Pydantic / Zod / class-validator (Create, Update, Response)
   - **CRUD endpoints** : router avec GET (list+detail), POST, PUT/PATCH, DELETE
   - **Tests** : 1 test par opération CRUD + edge cases (404, validation error)
   - **Seed data** : 5-10 entrées réalistes pour le développement
3. **Enregistrer** dans le routeur principal
4. **Appliquer** la migration (`alembic upgrade head` / `python manage.py migrate`)
