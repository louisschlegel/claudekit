---
name: two-correction
description: After 2 corrections on the same issue in a session, clear context and restart with an improved prompt. Prevents correction loops that degrade output quality.
triggers:
  - "correction loop"
  - "same issue again"
  - "still wrong"
---

# Skill: Two-Correction Rule

If Claude makes the same mistake twice in a session, the context is degraded. Restart instead of looping.

## Detection
You've corrected the same issue twice if:
- Same error type appears after a fix
- Output regresses to a previous bad state
- You're adding "again" or "still" to your correction

## Protocol
1. **Stop** — don't make a third attempt in the current context
2. **Capture** — note what worked and what failed
3. **Clear** — `/clear` to reset context
4. **Restart** with improved prompt that includes:
   - What you want (be more specific)
   - What NOT to do (the mistake made twice)
   - An example of the desired output
   - Explicit constraints

## Improved prompt template
```
Task: [original task]
Constraint: Do NOT [specific mistake observed twice]
Expected output format: [example]
Context: [minimal relevant context only]
```

## Why this works
Long context with repeated corrections trains Claude toward the wrong answer. Fresh context + better prompt is faster than a 3rd correction.
