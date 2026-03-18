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

# Copy files
copy_files() {
  local src="$1"
  local dst="$2"

  mkdir -p "$dst/.claude/hooks" "$dst/.claude/agents" "$dst/workflows" "$dst/scripts" "$dst/.template"

  cp -r "$src/.claude/agents/" "$dst/.claude/agents/"
  cp -r "$src/workflows/" "$dst/workflows/"
  cp "$src/scripts/gen.py" "$dst/scripts/gen.py"
  cp "$src/scripts/auto-learn.py" "$dst/scripts/auto-learn.py"
  cp "$src/scripts/self-improve.py" "$dst/scripts/self-improve.py"
  cp "$src/scripts/version-bump.py" "$dst/scripts/version-bump.py"
  cp "$src/scripts/changelog-gen.py" "$dst/scripts/changelog-gen.py"
  cp "$src/.claude/hooks/session-start.sh" "$dst/.claude/hooks/session-start.sh"
  cp "$src/.claude/hooks/user-prompt-submit.sh" "$dst/.claude/hooks/user-prompt-submit.sh"
  cp "$src/CLAUDE.md" "$dst/CLAUDE.md"
  cp "$src/learning.md.template" "$dst/learning.md.template"

  # Init template meta files
  if [ ! -f "$dst/.template/version.json" ]; then
    cp "$src/.template/version.json" "$dst/.template/version.json"
  fi
  if [ ! -f "$dst/.template/known-patterns.json" ]; then
    cp "$src/.template/known-patterns.json" "$dst/.template/known-patterns.json"
  fi

  chmod +x "$dst/.claude/hooks/session-start.sh"
  chmod +x "$dst/.claude/hooks/user-prompt-submit.sh"
  chmod +x "$dst/scripts/gen.py"
}

if [ "$IS_LOCAL" = true ]; then
  copy_files "$SOURCE_DIR" "$TARGET_DIR"
else
  # Download from GitHub
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
ENTRIES=".template/improvements.log\n.mcp.json"
if [ -f "$GITIGNORE" ]; then
  for entry in ".template/improvements.log" ".mcp.json"; do
    if ! grep -qF "$entry" "$GITIGNORE"; then
      echo "$entry" >> "$GITIGNORE"
    fi
  done
else
  printf "$ENTRIES\n" > "$GITIGNORE"
fi

echo ""
echo -e "${GREEN}✓ claudekit installed successfully!${NC}"
echo ""
echo -e "Next step:"
echo -e "  ${YELLOW}cd $TARGET_DIR && claude${NC}"
echo ""
echo -e "Claude will auto-detect your stack and configure everything."
echo ""
