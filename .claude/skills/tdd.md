---
name: tdd
description: Enforce Red-Green-Refactor TDD cycle — write failing test first, then implement, then clean up
triggers:
  - "tdd"
  - "test driven"
  - "red green refactor"
  - "write tests first"
  - "test-first"
---

# Skill: /tdd

Enforce strict Red-Green-Refactor cycle.

## Protocol

### Phase 1: RED — Write a failing test
1. Understand the requirement
2. Write a test that expresses the desired behavior
3. Run the test — it MUST fail (if it passes, the test is wrong or feature exists)
4. **Gate**: test must fail before proceeding

### Phase 2: GREEN — Minimal implementation
1. Write the MINIMUM code to make the test pass
2. No extra features, no cleanup, no optimization
3. Run the test — it MUST pass
4. **Gate**: test must pass before proceeding

### Phase 3: REFACTOR — Clean up
1. Improve code quality (naming, duplication, structure)
2. Run ALL tests — they must still pass
3. No new functionality in this phase

## Rules
- Never write implementation before a failing test
- Never refactor while tests are failing
- Each cycle should take < 15 minutes
- If stuck > 15 min, the scope is too big — break it down

## Anti-patterns to avoid
- Writing tests after implementation ("test-after" is not TDD)
- Making tests pass by deleting the test
- Writing more than one failing test at a time
- Skipping the refactor phase
