---
paths:
  - "**/models/**/*"
  - "**/migrations/**/*"
  - "**/schema*"
  - "**/*model*"
  - "**/*migration*"
---
# Database Rules

- Always create reversible migrations (include rollback)
- Never delete columns in the same migration that creates new ones
- Add indexes on foreign keys and frequently-queried fields
- Use UUIDs for public-facing IDs, auto-increment for internal
- Soft delete with `deleted_at` timestamp, never hard delete user data
- Always set `NOT NULL` with a default, avoid nullable columns
- Name migrations descriptively: `add_index_on_users_email`, not `migration_042`
- Test migrations against a copy of production data before deploying
