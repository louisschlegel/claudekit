#!/bin/bash
# claudekit status line — shows context %, cost, git, rate limits
# Configure: /statusline then point to this script
# Or: claude --statusline "bash scripts/statusline.sh"

# Read JSON from stdin (Claude Code provides session data)
DATA=$(cat)

# Extract fields with Python for reliability
python3 - "$DATA" << 'PYEOF'
import json, sys, os

raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    d = json.loads(raw)
except:
    print("claudekit")
    sys.exit(0)

# Context usage
ctx = d.get("context_window", {})
used_pct = ctx.get("used_percentage", 0)
remaining = ctx.get("remaining_percentage", 100)

# Cost
cost = d.get("cost", {})
total_cost = cost.get("total_cost_usd", 0)
lines_added = cost.get("total_lines_added", 0)
lines_removed = cost.get("total_lines_removed", 0)

# Rate limits (Pro/Max only)
rate = d.get("rate_limits", {})
five_hour = rate.get("five_hour", {}).get("used_percentage", 0) if rate else 0

# Git / worktree
wt = d.get("worktree", {})
wt_name = wt.get("name", "") if wt else ""

# Model
model = d.get("model", "")
short_model = model.replace("claude-", "").replace("-4-6", "").capitalize() if model else ""

# Build status bar
parts = []
if short_model:
    parts.append(short_model)

# Context bar (visual)
bar_len = 10
filled = int(used_pct / 100 * bar_len)
bar = "▓" * filled + "░" * (bar_len - filled)
color = "\033[32m" if used_pct < 60 else "\033[33m" if used_pct < 80 else "\033[31m"
parts.append(f"{color}{bar}\033[0m {used_pct:.0f}%")

if total_cost > 0:
    parts.append(f"${total_cost:.2f}")

if lines_added or lines_removed:
    parts.append(f"+{lines_added}/-{lines_removed}")

if five_hour > 0:
    parts.append(f"rate:{five_hour:.0f}%")

if wt_name:
    parts.append(f"wt:{wt_name}")

print(" │ ".join(parts))
PYEOF
