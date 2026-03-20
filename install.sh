#!/bin/bash
# claudekit — Install on an existing project
# Usage: curl -fsSL https://raw.githubusercontent.com/louisschlegel/claudekit/main/install.sh | bash
# Or:    bash install.sh (from inside a cloned claudekit repo)

set -e

REPO="https://github.com/louisschlegel/claudekit"
BRANCH="main"
TARGET_DIR="${1:-.}"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         claudekit installer          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════╝${NC}"
echo ""

# Detect if running from a local clone or via curl
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || echo "")"
IS_LOCAL=false
if [ -f "$SCRIPT_DIR/scripts/gen.py" ] && [ -f "$SCRIPT_DIR/CLAUDE.md" ]; then
  IS_LOCAL=true
  SOURCE_DIR="$SCRIPT_DIR"
fi

# Target directory
if [ "$TARGET_DIR" = "." ]; then
  TARGET_DIR="$(pwd)"
fi

echo -e "Installing claudekit into: ${YELLOW}$TARGET_DIR${NC}"
echo ""

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Error: python3 is required${NC}"; exit 1; }
command -v git >/dev/null 2>&1 || { echo -e "${RED}Error: git is required${NC}"; exit 1; }

if ! command -v claude >/dev/null 2>&1; then
  echo -e "${YELLOW}Warning: Claude Code CLI not found. Install it from https://claude.ai/claude-code${NC}"
fi

# ── Known claudekit hooks (used by both audit and copy) ──────────────────────
KNOWN_HOOKS="session-start.sh user-prompt-submit.sh pre-bash-guard.sh post-edit.sh stop.sh pre-push.sh pre-compact.sh notification.sh subagent-stop.sh observability.sh injection-defender.sh context-monitor.sh live-handoff.sh stop-guard.sh session-end.sh permission-auto.sh tool-failure.sh test-filter.sh manifest-regen.sh"

# ── Audit existing Claude config ──────────────────────────────────────────────
audit_existing() {
  local dst="$1"
  EXISTING_SETTINGS=""
  EXISTING_MCP=""
  EXISTING_CUSTOM_HOOKS=""
  EXISTING_CUSTOM_AGENTS=""
  EXISTING_CUSTOM_WORKFLOWS=""
  EXISTING_CLAUDE_MD=""
  HAS_EXISTING=false

  # settings.local.json — géré par gen.py, jamais touché par install.sh
  if [ -f "$dst/.claude/settings.local.json" ]; then
    PERM_COUNT=$(python3 -c "
import json
d = json.load(open('$dst/.claude/settings.local.json'))
print(len(d.get('permissions', {}).get('allow', [])))
" 2>/dev/null || echo "?")
    EXISTING_SETTINGS="$PERM_COUNT permissions"
    HAS_EXISTING=true
  fi

  # .mcp.json — géré par gen.py, jamais touché par install.sh
  if [ -f "$dst/.mcp.json" ]; then
    MCP_SERVERS=$(python3 -c "
import json
d = json.load(open('$dst/.mcp.json'))
print(', '.join(d.get('mcpServers', {}).keys()))
" 2>/dev/null || echo "?")
    EXISTING_MCP="$MCP_SERVERS"
    HAS_EXISTING=true
  fi

  # Hooks custom (tout ce qui n'est pas géré par claudekit)
  if [ -d "$dst/.claude/hooks" ]; then
    for hook in "$dst/.claude/hooks"/*.sh; do
      [ -f "$hook" ] || continue
      hname=$(basename "$hook")
      is_known=0
      for known in $KNOWN_HOOKS; do [ "$hname" = "$known" ] && is_known=1 && break; done
      [ "$is_known" -eq 0 ] && EXISTING_CUSTOM_HOOKS="$EXISTING_CUSTOM_HOOKS $hname" && HAS_EXISTING=true
    done
  fi

  # Agents custom (noms différents des agents claudekit)
  CLAUDEKIT_AGENTS="architect reviewer tester deployer explorer security-auditor debug-detective doc-writer performance-analyst release-manager data-engineer ml-engineer devops-engineer cost-analyst spec-reader template-improver memory-curator compliance-officer ai-engineer realtime-architect data-modeler schema-designer devils-advocate"
  if [ -d "$dst/.claude/agents" ]; then
    for agent in "$dst/.claude/agents"/*.md; do
      [ -f "$agent" ] || continue
      aname=$(basename "$agent" .md)
      is_known=0
      for known in $CLAUDEKIT_AGENTS; do [ "$aname" = "$known" ] && is_known=1 && break; done
      [ "$is_known" -eq 0 ] && EXISTING_CUSTOM_AGENTS="$EXISTING_CUSTOM_AGENTS $aname.md" && HAS_EXISTING=true
    done
  fi

  # Workflows custom
  CLAUDEKIT_WORKFLOWS="feature bugfix hotfix release security-audit dependency-update dependency-audit refactor onboard onboarding self-improve db-migration incident-response performance-baseline publish-package api-design a-b-test data-quality llm-eval spec-to-project code-review monitoring-setup cost-optimization multi-agent-worktrees context-handoff notebook-review cost-dashboard riper mcp-vetting agent-teams cost-audit skill-lifecycle"
  if [ -d "$dst/workflows" ]; then
    for wf in "$dst/workflows"/*.md; do
      [ -f "$wf" ] || continue
      wname=$(basename "$wf" .md)
      is_known=0
      for known in $CLAUDEKIT_WORKFLOWS; do [ "$wname" = "$known" ] && is_known=1 && break; done
      [ "$is_known" -eq 0 ] && EXISTING_CUSTOM_WORKFLOWS="$EXISTING_CUSTOM_WORKFLOWS $wname.md" && HAS_EXISTING=true
    done
  fi

  # CLAUDE.md existant
  if [ -f "$dst/CLAUDE.md" ]; then
    EXISTING_CLAUDE_MD=true
    HAS_EXISTING=true
  fi
}

# ── Copy files (avec protection des éléments custom) ──────────────────────────
copy_files() {
  local src="$1"
  local dst="$2"

  mkdir -p "$dst/.claude/hooks" "$dst/.claude/agents" "$dst/.claude/skills" "$dst/.claude/commands" "$dst/.claude/rules" "$dst/.claude/docs" "$dst/workflows" "$dst/scripts" "$dst/.template"

  # Scripts claudekit — toujours mis à jour (ce sont des outils, pas du contenu user)
  cp "$src/scripts/gen.py" "$dst/scripts/gen.py"
  cp "$src/scripts/auto-learn.py" "$dst/scripts/auto-learn.py"
  cp "$src/scripts/self-improve.py" "$dst/scripts/self-improve.py"
  cp "$src/scripts/version-bump.py" "$dst/scripts/version-bump.py"
  cp "$src/scripts/changelog-gen.py" "$dst/scripts/changelog-gen.py"
  cp "$src/scripts/claudekit.py" "$dst/scripts/claudekit.py"
  cp "$src/scripts/migrate-template.py" "$dst/scripts/migrate-template.py"

  # Hooks claudekit — copier TOUS les hooks gérés (gen.py les régénère de toute façon)
  for hook in "$src/.claude/hooks"/*.sh; do
    [ -f "$hook" ] || continue
    hname=$(basename "$hook")
    # Only copy claudekit-managed hooks, not custom ones
    is_managed=0
    for known in $KNOWN_HOOKS; do [ "$hname" = "$known" ] && is_managed=1 && break; done
    if [ "$is_managed" -eq 1 ]; then
      cp "$hook" "$dst/.claude/hooks/$hname"
      chmod +x "$dst/.claude/hooks/$hname"
    fi
  done
  # Les hooks custom (non-claudekit) dans hooks/ ne sont pas touchés

  # Skills — toujours mis à jour (claudekit skills, pas du contenu user)
  for skill in "$src/.claude/skills"/*.md; do
    [ -f "$skill" ] || continue
    cp "$skill" "$dst/.claude/skills/$(basename "$skill")"
  done

  # Commands — toujours mis à jour
  for cmd in "$src/.claude/commands"/*.md; do
    [ -f "$cmd" ] || continue
    cp "$cmd" "$dst/.claude/commands/$(basename "$cmd")"
  done

  # Rules — ne pas écraser les règles existantes (user may have customized)
  for rule in "$src/.claude/rules"/*.md; do
    [ -f "$rule" ] || continue
    rname=$(basename "$rule")
    [ ! -f "$dst/.claude/rules/$rname" ] && cp "$rule" "$dst/.claude/rules/$rname"
  done

  # Docs (agents-table, workflows-table, security-layers) — toujours mis à jour
  for doc in "$src/.claude/docs"/*.md; do
    [ -f "$doc" ] || continue
    cp "$doc" "$dst/.claude/docs/$(basename "$doc")"
  done

  # Plugin manifest
  if [ -d "$src/.claude-plugin" ]; then
    mkdir -p "$dst/.claude-plugin"
    cp "$src/.claude-plugin/plugin.json" "$dst/.claude-plugin/plugin.json" 2>/dev/null
  fi

  # Agents — cp -n : n'écrase pas les agents existants (custom ou modifiés)
  for agent in "$src/.claude/agents"/*.md; do
    [ -f "$agent" ] || continue
    aname=$(basename "$agent")
    if [ -f "$dst/.claude/agents/$aname" ]; then
      PRESERVED_AGENTS="${PRESERVED_AGENTS} $aname"
    else
      cp "$agent" "$dst/.claude/agents/$aname"
    fi
  done

  # Workflows — cp -n : n'écrase pas les workflows existants (custom ou modifiés)
  for wf in "$src/workflows"/*.md; do
    [ -f "$wf" ] || continue
    wname=$(basename "$wf")
    if [ -f "$dst/workflows/$wname" ]; then
      PRESERVED_WORKFLOWS="${PRESERVED_WORKFLOWS} $wname"
    else
      cp "$wf" "$dst/workflows/$wname"
    fi
  done

  # CLAUDE.md — backup si existant et différent, puis mise à jour
  if [ -f "$dst/CLAUDE.md" ]; then
    if ! diff -q "$src/CLAUDE.md" "$dst/CLAUDE.md" >/dev/null 2>&1; then
      cp "$dst/CLAUDE.md" "$dst/CLAUDE.md.bak"
      CLAUDE_MD_BACKED_UP=true
    fi
  fi
  cp "$src/CLAUDE.md" "$dst/CLAUDE.md"

  cp "$src/learning.md.template" "$dst/learning.md.template"

  # Template meta files — jamais écrasés
  if [ ! -f "$dst/.template/version.json" ]; then
    cp "$src/.template/version.json" "$dst/.template/version.json"
  fi
  if [ ! -f "$dst/.template/known-patterns.json" ]; then
    cp "$src/.template/known-patterns.json" "$dst/.template/known-patterns.json"
  fi

  chmod +x "$dst/.claude/hooks/session-start.sh"
  chmod +x "$dst/.claude/hooks/user-prompt-submit.sh"
  chmod +x "$dst/.claude/hooks/pre-push.sh"
  chmod +x "$dst/scripts/gen.py"
  chmod +x "$dst/scripts/claudekit.py"
}

# ── Run ────────────────────────────────────────────────────────────────────────

# Audit avant toute modification
audit_existing "$TARGET_DIR"

# Afficher le rapport d'audit si config existante
if [ "$HAS_EXISTING" = true ]; then
  echo -e "${CYAN}Existing Claude config detected:${NC}"
  [ -n "$EXISTING_SETTINGS" ]          && echo -e "  ${YELLOW}→ .claude/settings.local.json${NC} ($EXISTING_SETTINGS) — will NOT be touched (managed by gen.py)"
  [ -n "$EXISTING_MCP" ]               && echo -e "  ${YELLOW}→ .mcp.json${NC} (servers: $EXISTING_MCP) — will NOT be touched (managed by gen.py)"
  [ -n "$EXISTING_CUSTOM_HOOKS" ]      && echo -e "  ${YELLOW}→ Custom hooks${NC}:$EXISTING_CUSTOM_HOOKS — will NOT be touched"
  [ -n "$EXISTING_CUSTOM_AGENTS" ]     && echo -e "  ${YELLOW}→ Custom agents${NC}:$EXISTING_CUSTOM_AGENTS — will NOT be overwritten"
  [ -n "$EXISTING_CUSTOM_WORKFLOWS" ]  && echo -e "  ${YELLOW}→ Custom workflows${NC}:$EXISTING_CUSTOM_WORKFLOWS — will NOT be overwritten"
  [ -n "$EXISTING_CLAUDE_MD" ]         && echo -e "  ${YELLOW}→ CLAUDE.md${NC} — will be updated (backup saved as CLAUDE.md.bak if different)"
  echo ""
fi

PRESERVED_AGENTS=""
PRESERVED_WORKFLOWS=""
CLAUDE_MD_BACKED_UP=false

if [ "$IS_LOCAL" = true ]; then
  copy_files "$SOURCE_DIR" "$TARGET_DIR"
else
  echo -e "Downloading from ${BLUE}$REPO${NC}..."
  TMP_DIR=$(mktemp -d)
  trap "rm -rf $TMP_DIR" EXIT

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP_DIR" --strip-components=1
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$REPO/archive/refs/heads/$BRANCH.tar.gz" | tar -xz -C "$TMP_DIR" --strip-components=1
  else
    echo -e "${RED}Error: curl or wget is required${NC}"
    exit 1
  fi

  copy_files "$TMP_DIR" "$TARGET_DIR"
fi

# Init manifest if missing
if [ ! -f "$TARGET_DIR/project.manifest.json" ]; then
  echo '{}' > "$TARGET_DIR/project.manifest.json"
  echo -e "${GREEN}✓${NC} Created project.manifest.json"
fi

# Add .gitignore entries
GITIGNORE="$TARGET_DIR/.gitignore"
if [ -f "$GITIGNORE" ]; then
  for entry in ".template/improvements.log" ".mcp.json"; do
    if ! grep -qF "$entry" "$GITIGNORE"; then
      echo "$entry" >> "$GITIGNORE"
    fi
  done
else
  printf ".template/improvements.log\n.mcp.json\n" > "$GITIGNORE"
fi

# ── Auto-regen settings if manifest exists and is not empty ───────────────────
MANIFEST_CONTENT=$(cat "$TARGET_DIR/project.manifest.json" 2>/dev/null | tr -d '[:space:]')
if [ "$MANIFEST_CONTENT" != "{}" ] && [ -n "$MANIFEST_CONTENT" ]; then
  echo -e "${CYAN}Regenerating config from existing manifest...${NC}"
  cd "$TARGET_DIR" && python3 scripts/gen.py --preserve-custom --quiet 2>/dev/null && \
    echo -e "${GREEN}✓${NC} Config regenerated (settings.local.json, hooks, .mcp.json)" || \
    echo -e "${YELLOW}⚠${NC} gen.py failed — run manually: python3 scripts/gen.py --preserve-custom"
fi

# ── Résumé ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}✓ claudekit installed successfully!${NC}"
echo ""

if [ -n "$PRESERVED_AGENTS" ]; then
  echo -e "  ${CYAN}Preserved existing agents${NC}:$PRESERVED_AGENTS"
fi
if [ -n "$PRESERVED_WORKFLOWS" ]; then
  echo -e "  ${CYAN}Preserved existing workflows${NC}:$PRESERVED_WORKFLOWS"
fi
if [ "$CLAUDE_MD_BACKED_UP" = true ]; then
  echo -e "  ${CYAN}CLAUDE.md backup saved${NC} → CLAUDE.md.bak"
fi
if [ -n "$EXISTING_SETTINGS" ] || [ -n "$EXISTING_MCP" ]; then
  echo -e "  ${CYAN}Existing settings/MCP preserved${NC} — run ${YELLOW}python3 scripts/gen.py --preserve-custom${NC} after setup"
fi

echo ""
echo -e "Next step:"
echo -e "  ${YELLOW}cd $TARGET_DIR && claude \"setup claudekit\"${NC}"
echo ""
echo -e "Claude will detect your stack and configure everything via an interactive interview."
echo -e "If you had custom permissions, run: ${YELLOW}python3 scripts/gen.py --preserve-custom${NC}"
echo ""
