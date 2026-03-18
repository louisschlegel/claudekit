# Contributing to claudekit

Thanks for your interest in improving claudekit!

## Ways to contribute

- **New agent** — add a specialist for a domain not yet covered
- **New workflow** — document a recurring sequence of steps
- **Stack coverage** — add permissions for a language/framework in `gen.py`
- **Bug fix** — something broken? Open an issue first, then a PR
- **Documentation** — improve clarity or add examples

## Development setup

```bash
git clone https://github.com/louisschlegel/claudekit
cd claudekit
```

No dependencies to install — the template is pure shell + Python stdlib.

## Validation

Before submitting a PR, make sure:

```bash
# Scripts compile
python3 -m py_compile scripts/gen.py
python3 -m py_compile scripts/auto-learn.py
python3 -m py_compile scripts/self-improve.py
python3 -m py_compile scripts/version-bump.py
python3 -m py_compile scripts/changelog-gen.py

# Hooks are valid bash
bash -n .claude/hooks/session-start.sh
bash -n .claude/hooks/user-prompt-submit.sh
```

These same checks run in CI on every PR.

## Adding an agent

1. Create `.claude/agents/your-agent.md`
2. Follow the structure of an existing agent (RÔLE, QUAND T'INVOQUER, CONTEXTE REQUIS, PROCESSUS, CONTRAT DE SORTIE, HANDOFF JSON, SPÉCIALISATIONS PAR TYPE DE PROJET, PÉRIMÈTRE)
3. Add the agent to the table in `CLAUDE.md`
4. Add the agent to the table in `README.md`
5. Register it in `project.manifest.EXAMPLE.json` under `agents`

## Adding a workflow

1. Create `workflows/your-workflow.md`
2. Add intent keywords to `.claude/hooks/user-prompt-submit.sh` → `INTENT_RULES`
3. Add the routing entry to `CLAUDE.md` → routing table
4. Add it to `README.md` → Workflows table
5. Add it to the setup interview list in `CLAUDE.md` (question 15)

## Adding stack support

Edit `scripts/gen.py`:
- Add the language to `STACK_PERMISSIONS`
- Add detection markers to `make_session_start()` (Cas 1 block)
- Add framework detection to the framework scan section

## Commit style

```
feat: add X agent
fix: correct Y in session-start hook
docs: update README with Z
refactor: simplify gen.py permission builder
```

## PR checklist

- [ ] CI passes (scripts compile + hooks valid bash)
- [ ] README updated if new agent/workflow/stack added
- [ ] CLAUDE.md routing table updated if new workflow
- [ ] No secrets or `.env` files committed
