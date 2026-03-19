---
name: epic-merge
description: Merge a completed epic worktree back to main — run full validation, create PR, clean up worktree.
triggers:
  - "epic-merge"
  - "finish epic"
  - "merge epic"
  - "close epic"
---

# Skill: Epic Merge

Safely merge a completed epic worktree back to the main branch.

## Pre-merge checklist

1. **Run full validation**
   ```bash
   make validate  # or equivalent for the stack
   ```

2. **Review changes**
   ```bash
   git diff main...HEAD --stat
   git log main...HEAD --oneline
   ```

3. **Push and create PR**
   ```bash
   git push -u origin HEAD
   gh pr create --title "feat: [epic title] (closes #[ISSUE_NUMBER])" \
     --body "Closes #[ISSUE_NUMBER]\n\n## Changes\n[summary]"
   ```

4. **After PR merge, clean up worktree**
   ```bash
   cd [project-root]
   git worktree remove .claude/worktrees/[worktree-name]
   git branch -d feat/issue-[NUMBER]-$SLUG
   ```

5. **Close issue** (auto-closed by "closes #N" in PR, but verify)
   ```bash
   gh issue view [NUMBER]
   ```

## Rules
- Never force-merge without CI passing
- Always delete the worktree after merge (prevents stale branches)
- Update learning.md if the epic surfaced important patterns
