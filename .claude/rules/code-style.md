---
paths:
  - "src/**/*"
  - "lib/**/*"
  - "app/**/*"
---
# Code Style Rules

- Prefer early returns over deeply nested conditionals
- Maximum function length: ~50 lines (extract if longer)
- Maximum file length: ~400 lines (split if longer)
- No commented-out code — use version control instead
- Imports ordered: stdlib → third-party → local (with blank lines between)
- No magic numbers — use named constants
- One class per file (except small DTOs/dataclasses)
- Function names should describe what they do, not how they do it
