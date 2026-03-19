---
paths: []
---
# Claude Code Environment Variables & Settings Reference

## Environment Variables

### Context & Performance
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` — trigger compaction earlier (default ~83%)
- `MAX_THINKING_TOKENS=8000` — limit thinking for simpler tasks (cost savings)
- `ENABLE_TOOL_SEARCH=auto:5` — defer MCP tool descriptions when exceeding N% of context

### Agent Teams
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` — enable agent teams coordination
- `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1` — disable background task functionality

### Hooks & Plugins
- `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS=10000` — extend SessionEnd hook timeout
- `CLAUDE_CODE_PLUGIN_SEED_DIR=/path/to/plugins` — seed directory for plugins (`:` separated)
- `CLAUDE_CODE_DISABLE_CRON=1` — disable cron jobs mid-session

### Debugging
- `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1` — prevent terminal title changes
- `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS=1` — remove built-in git instructions from system prompt

### Model
- `ANTHROPIC_CUSTOM_MODEL_OPTION=my-model` — add custom model to /model picker
- `ANTHROPIC_CUSTOM_MODEL_OPTION_NAME=My Model` — display name
- `ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION=Custom model` — description

## Useful Settings (settings.json / settings.local.json)
- `autoMemoryDirectory` — custom directory for auto-memory storage
- `modelOverrides` — map model picker entries to custom provider model IDs
- `worktree.sparsePaths` — sparse checkout paths for `--worktree` in large monorepos
- `claudeMdExcludes` — skip irrelevant CLAUDE.md files in monorepos
- `permissions.disableBypassPermissionsMode: "disable"` — prevent `--dangerously-skip-permissions`

## Useful CLI Flags
- `--effort low|medium|high` — set model effort level
- `--worktree` — run in isolated git worktree
- `--agent <name>` — run entire session as a specific subagent
- `--channels` — allow MCP servers to push messages
- `--console` — authenticate via Anthropic Console (API billing)
- `-n "name"` — set session display name
