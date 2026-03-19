---
paths:
  - "tests/**/*"
  - "test/**/*"
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/test_*.py"
---
# Testing Rules

- Each test should test ONE thing — if the name has "and", split it
- Use descriptive test names: `test_user_cannot_access_admin_without_role`
- Prefer factories/fixtures over hardcoded test data
- Never test implementation details — test behavior
- Mock at system boundaries only (external APIs, databases, file system)
- Each new endpoint/function needs at least one happy path and one error test
- Use `pytest.mark.parametrize` for testing multiple inputs (Python)
- Assertions should have meaningful error messages
