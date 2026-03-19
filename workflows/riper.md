# Workflow: RIPER — Research → Innovate → Plan → Execute → Review

A structured 5-phase methodology for complex tasks that require careful planning before action.

## When to use
- Tasks spanning > 3 files or > 1 day of work
- Architectural decisions with significant trade-offs
- Tasks where the approach is unclear

## Phases

### Phase 1 — RESEARCH (READ-ONLY)
**Goal:** Understand the problem space without proposing solutions yet.

Actions:
- Read all relevant files
- Run existing tests to understand current behavior
- Explore similar patterns in the codebase
- Check git history for context

Output: Summary of current state, constraints discovered, unknowns identified.

**Gate:** Do not proceed to Innovate until Research is complete.

---

### Phase 2 — INNOVATE (THINK-ONLY)
**Goal:** Generate 2-3 candidate approaches, evaluate trade-offs.

Actions:
- Propose approaches (no code yet)
- For each: pros, cons, complexity estimate, risk level
- Identify the simplest viable approach

Output: Approach comparison table, recommended option with justification.

**Gate:** Get user confirmation on chosen approach before proceeding.

---

### Phase 3 — PLAN (DESIGN-ONLY)
**Goal:** Create a detailed implementation plan.

Actions:
- List every file that will be created/modified
- Define interfaces and data structures
- Identify test cases needed
- Estimate: S/M/L/XL

Output: Step-by-step implementation checklist.

**Gate:** User approval of plan before any code is written.

---

### Phase 4 — EXECUTE (CODE)
**Goal:** Implement the plan exactly as designed.

Actions:
- Follow the checklist from Phase 3 step by step
- Write tests alongside implementation
- Run tests after each logical chunk
- If you discover a reason to deviate from the plan → STOP and surface it

Output: Working implementation with passing tests.

---

### Phase 5 — REVIEW (VALIDATE)
**Goal:** Verify the implementation meets the original requirements.

Actions:
- Run full test suite
- Use `/skill:code-review` for parallel review
- Check acceptance criteria from Phase 1
- Update learning.md with patterns discovered

Output: Verdict (ship / needs fixes) + learning.md update.

---

**HANDOFF JSON (pour orchestrateur) :**
```json
{"status": "completed", "summary": "", "next_action": "", "artifacts": []}
```

## CONTRAT DE SORTIE

```
STATUS: completed
SUMMARY: [résumé des actions effectuées]
ARTIFACTS: [fichiers créés ou modifiés]
NEXT_ACTION: [prochaine étape recommandée ou none]
```
