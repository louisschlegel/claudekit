# Command: /setup-rules

Analyser le codebase et générer automatiquement les fichiers `.claude/rules/` adaptés.

## Protocole

1. **Scanner le codebase** :
   - Détecter les langages (extensions de fichiers)
   - Détecter les frameworks (imports, config files)
   - Détecter les patterns existants (naming, structure)

2. **Générer les rules** :
   - `security.md` — règles de sécurité adaptées au stack
   - `testing.md` — conventions de test du projet
   - `code-style.md` — style de code détecté (naming, imports, etc.)
   - `api-design.md` — conventions API si endpoints détectés
   - `database.md` — conventions DB si ORM détecté

3. **Path scoping** :
   - Chaque rule file a un `paths:` YAML frontmatter
   - Les paths sont basés sur la structure réelle du projet

4. **Validation** :
   - Relire les rules générées
   - Supprimer les doublons avec CLAUDE.md
   - Demander confirmation à l'utilisateur
