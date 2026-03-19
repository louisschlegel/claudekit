# Command: /new-module

Scaffold un nouveau module/feature adapté au stack détecté.

## Usage
`/new-module <nom-du-module>`

## Protocole

1. **Détecter le stack** depuis `project.manifest.json`
2. **Créer la structure** adaptée :

### FastAPI
```
src/<module>/
├── __init__.py
├── router.py      # APIRouter avec endpoints CRUD
├── schemas.py     # Pydantic models (Create, Update, Response)
├── models.py      # SQLAlchemy models
├── service.py     # Business logic
└── tests/
    ├── __init__.py
    └── test_<module>.py
```

### Express/NestJS
```
src/<module>/
├── <module>.controller.ts
├── <module>.service.ts
├── <module>.module.ts
├── dto/
│   ├── create-<module>.dto.ts
│   └── update-<module>.dto.ts
└── <module>.spec.ts
```

### Django
```
<module>/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
└── tests.py
```

3. **Enregistrer** le module dans le routeur/app principal
4. **Créer les tests** de base (1 test par endpoint CRUD)
