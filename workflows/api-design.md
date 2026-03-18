# Workflow: API Design

## DÉCLENCHEUR
Intent classifié comme `api-design` par le hook UserPromptSubmit.
Commande directe : "design l'API", "nouvel endpoint", "API first", "contrat API", "définis le schéma", "ajoute un endpoint".

## AGENTS IMPLIQUÉS
1. **Architect** — design du contrat, patterns, cohérence
2. **Reviewer** — backwards compatibility, conventions, breaking changes
3. **Tester** — contract tests, génération des cas de test
4. **Doc Writer** — documentation générée depuis le spec

---

## ÉTAPE 1 — Design du contrat (avant tout code)

**Règle absolue : le contrat est défini et validé AVANT toute implémentation.**

### 1.1 — Analyser le contexte

Invoquer `architect` avec :
```
Demande : [description du nouvel endpoint / feature API]
API existante : [liste des endpoints actuels ou lien vers la spec]
Stack : [manifest stack — REST/GraphQL/gRPC]
Conventions actuelles : [naming, versioning, pagination, auth]
```

L'architect répond avec :
- Le design proposé (resources, actions, structure)
- Les trade-offs (REST CRUD vs commands, versioning, etc.)
- Les risques de breaking changes

### 1.2 — Choisir la stratégie selon le style d'API

**REST (OpenAPI)**
```yaml
# openapi.yaml — ajouter le nouvel endpoint
paths:
  /api/v1/orders:
    post:
      summary: Create a new order
      operationId: createOrder
      tags: [orders]
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Order created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '422':
          $ref: '#/components/responses/UnprocessableEntity'
```

**GraphQL (schema SDL)**
```graphql
# schema.graphql
type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
}

input CreateOrderInput {
  items: [OrderItemInput!]!
  shippingAddressId: ID!
  paymentMethodId: ID!
}

type CreateOrderPayload {
  order: Order
  errors: [UserError!]!
}
```

**gRPC (proto3)**
```protobuf
// orders.proto
service OrderService {
  rpc CreateOrder (CreateOrderRequest) returns (CreateOrderResponse);
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc ListOrders (ListOrdersRequest) returns (ListOrdersResponse);
}

message CreateOrderRequest {
  repeated OrderItem items = 1;
  string shipping_address_id = 2;
  string payment_method_id = 3;
}
```

---

## ÉTAPE 2 — Conventions à respecter

### Naming (REST)
```
Ressources : noms pluriels → /users, /orders, /products
Actions CRUD : GET (list/get) / POST (create) / PUT|PATCH (update) / DELETE
Actions non-CRUD : POST /orders/{id}/cancel (verbe dans le sous-chemin)
IDs : UUID ou slugs → jamais d'IDs numériques séquentiels dans l'URL publique
```

### Versioning
```
URL path (recommandé pour les APIs publiques) : /api/v1/...
Header (pour les APIs internes) : API-Version: 2024-01-01
Jamais de versioning par query param : /api/endpoint?version=2
```

### Pagination
```json
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true,
    "total": 1234
  }
}
```

### Erreurs (format standardisé)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body is invalid.",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address."
      }
    ]
  }
}
```

### Authentification
```
Nouveaux endpoints : auth requise par défaut (opt-out explicite pour les endpoints publics)
Scope de permission : documenter le scope requis dans le spec
```

---

## ÉTAPE 3 — Gate : Review du contrat

Invoquer `reviewer` avec :
```
Spec : [fichier openapi.yaml / schema.graphql / .proto modifié]
API existante : [spec version précédente]
Focus : backwards compatibility, cohérence, breaking changes cachés
```

Le reviewer vérifie :
- **Backwards compatibility** : les clients existants continuent de fonctionner
  - Ajout de champ optionnel dans la réponse → compatible
  - Renommer un champ → breaking change
  - Changer le type d'un champ → breaking change
  - Supprimer un champ → breaking change
  - Rendre un champ optionnel obligatoire → breaking change
- **Cohérence** avec les conventions existantes
- **Sécurité** : auth sur tous les endpoints qui le requièrent, validation des inputs

Gate :
- `VERDICT: APPROVED` → continuer
- `VERDICT: CHANGES REQUESTED` → modifier le spec, soumettre à nouveau

---

## ÉTAPE 4 — Mock server depuis le spec

Démarrer un mock server pour permettre au(x) client(s) de développer en parallèle.

```bash
# REST / OpenAPI — Prism (Microsoft)
npm install -g @stoplight/prism-cli
prism mock openapi.yaml
# Accessible sur http://localhost:4010

# REST / OpenAPI — Mockoon (GUI + CLI)
npm install -g @mockoon/cli
mockoon-cli start --data mockoon-config.json

# GraphQL — Apollo Server avec mocks
# Dans server.js :
# const server = new ApolloServer({ typeDefs, mocks: true });

# gRPC — grpc-mock
npm install -g grpc-mock
grpc-mock --proto orders.proto --host 0.0.0.0 --port 50051
```

Partager l'URL du mock avec l'équipe frontend / clients API.

---

## ÉTAPE 5 — Implémentation guidée par le contrat

### 5.1 — Générer les contract tests depuis le spec

```bash
# REST — Schemathesis (Python) : teste automatiquement tous les endpoints contre le spec
pip install schemathesis
schemathesis run openapi.yaml --base-url http://localhost:8000 --checks all

# REST — Dredd : valide l'implémentation contre le spec OpenAPI
npm install -g dredd
dredd openapi.yaml http://localhost:8000

# GraphQL — graphql-inspector : vérifie la conformité du schéma
npx graphql-inspector validate schema.graphql
```

### 5.2 — Valider les inputs conformément au spec

```python
# Python / FastAPI — validation automatique depuis le spec
from fastapi import FastAPI
from pydantic import BaseModel

class CreateOrderRequest(BaseModel):
    items: list[OrderItem]
    shipping_address_id: str
    payment_method_id: str

@app.post("/api/v1/orders", response_model=Order, status_code=201)
async def create_order(body: CreateOrderRequest, user: User = Depends(get_current_user)):
    ...
```

```typescript
// Node / Express — validation avec zod
import { z } from 'zod';

const CreateOrderSchema = z.object({
  items: z.array(OrderItemSchema).min(1),
  shippingAddressId: z.string().uuid(),
  paymentMethodId: z.string().uuid(),
});

app.post('/api/v1/orders', authenticate, async (req, res) => {
  const body = CreateOrderSchema.parse(req.body);  // throws if invalid
  ...
});
```

### 5.3 — Générer les tests depuis le spec

Invoquer `tester` avec :
```
Mode : contract
Spec : [openapi.yaml / schema.graphql]
Endpoints à tester : [liste]
```

---

## ÉTAPE 6 — Vérification de conformité implémentation vs spec

```bash
# Dredd — teste tous les exemples du spec contre l'implémentation réelle
dredd openapi.yaml http://localhost:8000 \
  --hookfiles dredd-hooks.js \
  --reporter html \
  --output dredd-report.html

# Schemathesis — fuzzing basé sur le spec
schemathesis run openapi.yaml \
  --base-url http://localhost:8000 \
  --auth-type bearer \
  --auth $TEST_TOKEN \
  --checks all \
  --stateful links  # teste les liens entre endpoints

# GraphQL — valider que l'implémentation correspond au schema
npx graphql-inspector diff schema.graphql http://localhost:4000/graphql
```

Gate :
- Tous les tests Dredd/Schemathesis passent → continuer
- Échec → **STOP**. Corriger l'implémentation pour qu'elle soit conforme au spec.

---

## ÉTAPE 7 — Documentation générée depuis le spec

Invoquer `doc-writer` avec :
```
Spec : [openapi.yaml / schema.graphql]
Type : API reference
Format : Swagger UI / Redoc / GraphQL Playground
```

```bash
# REST — Swagger UI (serveur de doc local)
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/openapi.yaml \
  -v $(pwd)/openapi.yaml:/openapi.yaml \
  swaggerapi/swagger-ui

# REST — Redoc (plus lisible pour les utilisateurs externes)
npx redoc-cli serve openapi.yaml --port 8081

# REST — générer une doc HTML statique
npx redoc-cli bundle openapi.yaml -o docs/api.html

# GraphQL — GraphQL Playground (inclus dans Apollo Server)
# Accessible sur http://localhost:4000/graphql en mode dev
```

---

## ÉTAPE 8 — Versioning si breaking change

Si le changement est un breaking change identifié en Étape 3 :

```bash
# Option A : nouveau chemin de version (/api/v2/)
# - Créer la nouvelle spec openapi-v2.yaml
# - Maintenir v1 jusqu'à la dépréciation (date communiquée aux clients)
# - Ajouter un header Deprecation: date="2025-01-01" sur les endpoints v1

# Option B : versioning par date (style Stripe)
# - L'utilisateur passe API-Version: 2024-06-01 dans ses requêtes
# - Le serveur adapte la réponse selon la version demandée

# Documenter la stratégie de dépréciation
# Notifier les clients API existants (email, changelog, header Sunset)
```

---

## CONTRAT DE SORTIE

```
API DESIGN: [nom de la feature / endpoint(s)]
STYLE: REST / GraphQL / gRPC
SPEC FILE: [chemin vers le fichier spec]

ENDPOINTS:
  [METHOD] [path] — [description]
  [METHOD] [path] — [description]

BREAKING CHANGES: none / [liste]
VERSIONING: none required / bump to v[N] required

GATES:
  Architect: APPROVED
  Reviewer: APPROVED (backwards compatible: yes/no)
  Contract tests: PASS ([N tests])
  Dredd/Schemathesis: PASS
  Implementation matches spec: yes

MOCK SERVER: running on [port] / not required
DOCUMENTATION: generated at [url/path]

IMPLEMENTATION STATUS: spec only / in progress / complete
```

**HANDOFF JSON (pour orchestrateur) :**
```json
{
  "api_name": "...",
  "spec_path": "...",
  "endpoints": 0,
  "breaking_changes": false,
  "mock_ready": false,
  "review": "approved|pending"
}
```
