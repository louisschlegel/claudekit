---
name: epic-start
description: Start a GitHub Issue as an isolated epic — create a git worktree, link to the issue, scaffold the work. Use for issues > 1 day of work.
effort: low
triggers:
  - "start epic"
  - "start issue"
  - "epic-start"
  - "begin issue #"
---

# Skill: Epic Start

Start a GitHub Issue in an isolated git worktree for parallel, conflict-free development.

## Steps

1. **Fetch issue details**
   ```bash
   gh issue view [ISSUE_NUMBER] --json title,body,labels,assignees
   ```

2. **Create worktree**
   ```bash
   SLUG=$(echo "[issue-title]" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | cut -c1-40)
   git worktree add .claude/worktrees/issue-[NUMBER]-$SLUG -b feat/issue-[NUMBER]-$SLUG
   ```

3. **Scaffold in worktree**
   - Create `TASK.md` at worktree root with: issue link, acceptance criteria, approach
   - Add TODO checklist from issue body

4. **Start work**
   ```bash
   cd .claude/worktrees/issue-[NUMBER]-$SLUG
   claude  # start new Claude session in this worktree
   ```

## TASK.md template
```markdown
# Issue #[NUMBER]: [title]

Link: [gh issue URL]

## Acceptance Criteria
[from issue body]

## Approach
[your plan]

## Checklist
- [ ] Implementation
- [ ] Tests
- [ ] Documentation
- [ ] PR created
```
