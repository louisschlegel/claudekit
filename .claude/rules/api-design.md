---
paths:
  - "src/api/**/*"
  - "src/routes/**/*"
  - "src/controllers/**/*"
  - "src/endpoints/**/*"
  - "**/router*.py"
  - "**/views*.py"
---
# API Design Rules

- Use plural nouns for resource URLs: `/users`, `/products`
- Return appropriate HTTP status codes: 201 for creation, 204 for deletion, 422 for validation
- Use cursor-based pagination over offset-based for large datasets
- Always return a consistent error format (RFC 7807 Problem Details recommended)
- Version APIs in the URL path: `/v1/users`
- Include `Content-Type` header in all responses
- Rate limit all public endpoints
- Validate request bodies with schemas (Pydantic, Zod, JSON Schema)
