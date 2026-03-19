---
name: code-review
description: Run 9 specialized review agents in parallel (test runner, linter, security, quality, performance, dependency, test quality, simplification, code reviewer). Returns verdict: Ready to Merge | Needs Attention | Needs Work.
triggers:
  - "review my code"
  - "code review"
  - "review before PR"
  - "is this ready to merge"
---

# Skill: Parallel Code Review (9 Agents)

Launch 9 subagents simultaneously, each focused on a distinct quality dimension.

## Scope detection
- Default: `git diff main...HEAD` (all branch changes)
- Staged only: `git diff --staged`
- Explicit: files/dirs passed by user

## The 9 agents (launch ALL in parallel via Task tool)

1. **Test Runner** — Run the test suite, report pass/fail/error count
2. **Linter & Static Analysis** — Run linting tools, report issues by severity
3. **Code Reviewer** — Up to 5 improvements ranked by impact/effort ratio
4. **Security Reviewer** — Check injections, auth flows, secrets, error handling, OWASP Top 10
5. **Quality & Style Reviewer** — Complexity, duplication, naming conventions, dead code
6. **Test Quality Reviewer** — Coverage ROI, flakiness risks, missing edge cases
7. **Performance Reviewer** — N+1 queries, memory leaks, algorithmic complexity, hot paths
8. **Dependency & Deployment Safety** — Breaking changes, missing migrations, observability gaps
9. **Simplification & Maintainability** — Over-engineering, premature abstractions, unnecessary complexity

## Output format

Synthesize all results into:

```
## Code Review — [branch/scope]

### Verdict: [Ready to Merge | Needs Attention | Needs Work]

### Critical / High (must fix before merge)
- [agent] issue description

### Medium (should fix)
- [agent] issue description

### Low / Optional
- [agent] suggestion

### Passed
- ✓ Tests: X/Y passing
- ✓ No security issues found
- etc.
```

## Rules
- All 9 agents run in parallel — never sequentially
- Critical issues from Security or Test Runner block merge
- Provide specific file:line references when possible
- Keep each agent's scope narrow — no overlap
