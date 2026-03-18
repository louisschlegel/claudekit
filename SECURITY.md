# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅        |

## Reporting a Vulnerability

If you discover a security vulnerability in claudekit, please **do not open a public issue**.

Instead, report it privately via GitHub: [Security Advisories](https://github.com/louisschlegel/claudekit/security/advisories/new)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (optional)

You will receive a response within 48 hours. If the vulnerability is confirmed, a patch will be released and you will be credited (unless you prefer to remain anonymous).

## Security Design

claudekit has 4 independent security layers:

1. **Permissions whitelist** — `settings.local.json` restricts Bash to only commands needed by your stack
2. **Pre-tool gate** — `pre-bash-guard.sh` blocks destructive patterns before execution
3. **Post-edit quality guards** — `post-edit.sh` runs lint, type-check, and secret scanning after every file edit
4. **Prompt injection detection** — `user-prompt-submit.sh` detects and blocks manipulation attempts

## What claudekit does NOT do

- It never sends your code or data to any external service
- It never commits secrets (`.env`, credentials, private keys)
- It never runs `git push --force` without explicit confirmation
- All hooks are local shell scripts — fully auditable
