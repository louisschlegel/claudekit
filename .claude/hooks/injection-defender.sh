#!/bin/bash
# Hook: PostToolUse — Injection Defender
# Scans tool OUTPUTS for prompt injection attempts.
# Exit 0 = clean, Exit 2 = injection detected (block)

INPUT=$(cat)

python3 - "$INPUT" << 'PYEOF' 2>/dev/null
import json, sys, re

raw = sys.argv[1] if len(sys.argv) > 1 else ""
if not raw.strip():
    sys.exit(0)

try:
    event = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(0)

tool_name = event.get("tool_name", "")
SCAN_TOOLS = {"Read", "Bash", "WebFetch", "WebSearch"}
if tool_name not in SCAN_TOOLS:
    sys.exit(0)

# Extract output content
resp = event.get("tool_response", {})
if isinstance(resp, dict):
    content = resp.get("content", "") or resp.get("output", "") or str(resp)
elif isinstance(resp, str):
    content = resp
else:
    content = str(resp)

if not content or len(content) < 10:
    sys.exit(0)

# Skip claudekit source files
file_path = event.get("tool_input", {}).get("file_path", "") or ""
SKIP = [".claude/hooks/", "injection-defender", "user-prompt-submit", "tests/test_", "learning.md", "scripts/gen.py"]
if any(s in file_path for s in SKIP):
    sys.exit(0)

sample = content[:5000].lower()

# ── Category 1: Instruction Override ──
OVERRIDE = [
    r"ignore previous instructions", r"disregard all", r"forget everything",
    r"new task:", r"system prompt:", r"you are now", r"pretend you are",
    r"your new instructions", r"ignore all prior", r"ignore the above",
    r"disregard previous", r"forget prior", r"your instructions are now",
    r"from now on you", r"reset your instructions", r"override.*instruction",
    r"\bjailbreak\b",
]

# ── Category 2: Role-Playing / DAN ──
DAN = [
    r"\bdan mode\b", r"developer mode enabled", r"do anything now",
    r"without restrictions", r"no restrictions", r"unrestricted mode",
    r"\bstan mode\b", r"pretend.*no rules", r"imagine.*no restrictions",
]

# ── Category 3: Context Manipulation ──
CONTEXT = [
    r"important:\s*ignore", r"urgent:\s*new directive", r"critical:\s*override",
    r"\bsystem:\s+you", r"\badmin:\s+", r"\broot access:", r"\bsudo:\s+",
    r"\[system\]", r"\[admin\]", r"<system>", r"<admin>", r"\[override\]",
]

# ── Category 4: Encoding / Obfuscation ──
ENCODING = [
    r"base64.*decode.*instruct", r"eval\s*\(\s*atob", r"exec\s*\(\s*base64",
]

# ── Category 5: Instruction Smuggling ──
SMUGGLING = [
    r"<!--\s*inject", r"<!--inject", r"<!--.*instruct.*-->", r"<!--.*ignore.*-->",
    r"<!--.*override.*-->", r"data:text/html.*instruct",
]

def check(patterns, text):
    for p in patterns:
        if re.search(p, text, re.IGNORECASE | re.MULTILINE):
            return p
    return None

# Check zero-width chars
ZWCHARS = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u2060']
zw_count = sum(content[:5000].count(c) for c in ZWCHARS)

detected = category = None

m = check(OVERRIDE, sample)
if m: detected, category = m, "instruction_override"
if not detected:
    m = check(DAN, sample)
    if m: detected, category = m, "roleplay_dan"
if not detected:
    m = check(CONTEXT, sample)
    if m: detected, category = m, "context_manipulation"
if not detected:
    if zw_count > 5:
        detected, category = f"zero_width({zw_count})", "encoding_obfuscation"
    else:
        m = check(ENCODING, sample)
        if m: detected, category = m, "encoding_obfuscation"
if not detected:
    m = check(SMUGGLING, sample)
    if m: detected, category = m, "instruction_smuggling"

if detected:
    print(json.dumps({"decision": "block", "reason": f"Prompt injection [{category}]: '{detected}' in {tool_name} output"}))
    sys.exit(2)

sys.exit(0)
PYEOF

exit $?
