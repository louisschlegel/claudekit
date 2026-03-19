# Command: /check-security

Audit de sécurité rapide du projet.

## Checks effectués

1. **Secrets hardcodés** : grep pour API keys, tokens, passwords dans le code source
2. **Dépendances vulnérables** :
   - Python : `pip-audit` ou `safety check`
   - Node : `npm audit --json`
   - Go : `govulncheck`
3. **OWASP patterns** : SQL injection, XSS, command injection dans le code récent
4. **Fichiers sensibles** : `.env` non gitignored, credentials en clair, clés privées
5. **Permissions** : fichiers world-readable, SUID bits, Docker running as root
6. **Dépendances obsolètes** : packages avec plus de 2 versions de retard

## Output

```
PASS | FAIL — Security Audit Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ No hardcoded secrets found
✗ 2 HIGH vulnerabilities in dependencies
✓ No OWASP patterns detected in recent changes
✗ .env.production not in .gitignore
✓ File permissions OK

Action required: 2 items need attention
```
