---
paths:
  - "src/**/*.py"
  - "src/**/*.ts"
  - "src/**/*.js"
  - "**/*.go"
  - "**/*.rs"
---
# Security Rules

- Never use `eval()`, `exec()`, or `Function()` constructor with user input
- Never interpolate user input into SQL queries — use parameterized queries
- Never use `innerHTML` or `dangerouslySetInnerHTML` with unsanitized input
- Never log secrets, tokens, passwords, or API keys — even in debug mode
- Always validate and sanitize user input at system boundaries
- Use `secrets.compare_digest()` for timing-safe comparisons (Python)
- Prefer `subprocess.run()` over `os.system()` — never pass unsanitized input to shell
- Use HTTPS for all external API calls
- Set secure, httpOnly, sameSite flags on cookies
