---
name: handoff
description: Create a structured context handoff for the next session — task state, decisions, files modified, next steps
effort: medium
user-invocable: true
triggers:
  - "handoff"
  - "sauvegarde le contexte"
  - "save context"
  - "session handoff"
  - "prépare le handoff"
---

# Skill: /handoff

Create a structured context handoff file for session continuity.

## Protocol

1. **Read** `.template/session-files.txt` (files modified this session)
2. **Summarize** current task state:
   - What was the goal?
   - What was accomplished?
   - What's left to do?
3. **Capture decisions** made during this session (architecture, trade-offs)
4. **Write** `.template/handoff.md`:

```markdown
# Session Handoff — YYYY-MM-DD HH:MM

## Task
<one-line summary>

## Status
<complete | in-progress | blocked>

## What was done
- <bullet points>

## Files modified
- <list from session-files.txt>

## Key decisions
- <decision>: <rationale>

## Next steps
1. <specific actionable item>
2. <specific actionable item>

## Context to preserve
<anything the next session needs to know that isn't obvious from the code>
```

5. The next `session-start.sh` will auto-inject this handoff into context

## Modes
- **Task** (default): current task progress
- **Bug**: layers investigation context (logs, hypothesis, root cause)
- **Clean**: minimal handoff, just next steps
