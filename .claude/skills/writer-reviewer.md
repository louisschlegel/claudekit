---
name: writer-reviewer
description: Implement code in a fresh context (Writer), then review it in a separate context (Reviewer) to avoid implementation bias. Use for any feature > 50 lines or touching critical paths.
triggers:
  - "writer reviewer"
  - "implement and review"
  - "bias-free review"
---

# Skill: Writer/Reviewer Pattern

Separate implementation from review to eliminate the "I just wrote this" bias.

## When to use
- Feature > 50 lines of new code
- Touching auth, payments, data mutations, security logic
- When the last review caught nothing (possible bias)

## Phase 1: Writer (current session)
1. Implement the feature following project conventions
2. Write tests
3. Do NOT self-review immediately
4. Commit: `git add -p && git commit`
5. Note the commit SHA

## Phase 2: Reviewer (fresh context)
Start a NEW session (or use `/clear`) with this prompt:
```
Review commit [SHA] as if you didn't write it.
Look specifically for:
- Edge cases the writer might have missed
- Race conditions and concurrency issues
- Consistency with existing patterns (read 3 similar files first)
- Security implications
- Error paths not handled
```

## Output
Reviewer produces a structured report:
- APPROVED / CHANGES_REQUIRED
- Blockers (must fix), Warnings (should fix), Suggestions (optional)
- Run `python3 scripts/auto-learn.py --from-agent reviewer --input '{...}'` to persist findings
