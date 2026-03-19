# Template Universel Claude Code — v2.0

> Ce fichier est l'**orchestrateur** du système. Il lit le contexte injecté par les hooks, route les demandes vers les bons agents et workflows, et supervise l'auto-amélioration du template.

---

## PREMIER DÉMARRAGE

Si `project.manifest.json` est vide (`{}`) → **lance le setup** (section SETUP ci-dessous).
Si rempli → lis le contexte injecté par le hook `session-start` et commence à orchestrer.

---

## DETECTION AUTOMATIQUE (projets legacy)

Le hook scanne automatiquement les markers de stack (package.json, pyproject.toml, go.mod, Cargo.toml, *.tf, *.ipynb, etc.) et les monorepos/cloud/CI.
Présente les détections et confirme avant d'écrire le manifest.

---

## SETUP INTERVIEW

Questions **une par une** :

**Bloc 1 — Identité** : nom, description, langue commits/comments (fr/en)

**Bloc 2 — Stack** : langages, frameworks, bases de données, infrastructure, tests

**Bloc 3 — Workflow** : stratégie git, CI/CD, cible déploiement, auto-deploy

**Bloc 4 — Automatisations Claude**
- MCP servers (à installer) : `filesystem`, `github`, `postgres`, `sqlite`, `brave-search`, `slack`, `linear`, `notion`, `playwright`, `desktop-commander`
- Intégrations natives Claude.ai (zéro config) : `gmail`, `google-calendar`, `canva`, `claude-in-chrome`
- Guards : lint ? type-check ? test auto ? migrations ? i18n ?
- Workflows à activer (voir liste complète dans `.claude/docs/workflows-table.md`)
- Agents à activer (voir liste complète dans `.claude/docs/agents-table.md`)
- Type de projet : `web-app`, `api`, `mobile`, `desktop`, `data-pipeline`, `ml`, `library`, `monorepo`, `iac`, `cli`
- Auto-amélioration : toutes les N sessions ? (défaut: 10)
- Fichier de mémoire (défaut: `learning.md`)

**Après le setup :** écrire `project.manifest.json` → `python3 scripts/gen.py` → créer `learning.md` → redémarrer Claude Code.

---

## ORCHESTRATEUR — ROUTING

@.claude/docs/workflows-table.md

**Mise à jour template :** "mets-toi à jour" / "update template" → `workflows/self-improve.md` (ou `python3 scripts/gen.py`)

---

## PROTOCOLE DE SESSION

**Début :** le hook injecte manifest + git + learning.md + handoff (si présent). Si amélioration en attente → `workflows/self-improve.md` d'abord. Si intention classifiée → router. Sinon → attendre.

**Fin :** `stop.sh` lance `scripts/self-improve.py` async. Mettre à jour `learning.md` si patterns importants détectés.

---

@.claude/docs/agents-table.md

---

@.claude/docs/security-layers.md

---

## REGLES DE BASE

Ces règles s'appliquent **toujours**, aucun agent ne peut les override.

### Code
- Lire avant de modifier
- Solution minimale correcte — pas d'over-engineering
- Pas de commentaires sur du code évident
- Ne pas créer de fichiers si un existant peut être modifié

### Git
- `git status` + `git diff` avant tout commit
- Messages de commit selon `workflow.commit_language` du manifest
- Jamais `git push --force` sans confirmation explicite

### Sécurité
- Jamais committer `.env`, credentials, tokens, clés privées
- Valider les inputs aux frontières système uniquement
- Pas de `eval()`, injection de commandes, XSS, SQL injection

### Communication
- Réponses courtes et directes
- Pas de récap après chaque action — l'utilisateur voit le diff
- Questions précises plutôt que suppositions

---

## LEGACY PROJECT SETUP

Étape 0 : Auditer `.claude/settings.local.json`, `.mcp.json`, `.claude/hooks/` custom avant de copier quoi que ce soit.

```bash
cd mon-projet-existant/
cp -r ~/Desktop/template/.claude/ ./.claude/
mkdir -p scripts workflows .template
cp ~/Desktop/template/scripts/{gen,self-improve,version-bump,changelog-gen,auto-learn}.py ./scripts/
cp -r ~/Desktop/template/.claude/agents/ ./.claude/agents/
cp -r ~/Desktop/template/workflows/ ./workflows/
cp ~/Desktop/template/CLAUDE.md ./CLAUDE.md
echo '{}' > project.manifest.json && claude
# Après setup : python3 scripts/gen.py --diff | --preserve-custom | (écraser)
```

---

## STRUCTURE

```
project/
├── CLAUDE.md / project.manifest.json / learning.md / CHANGELOG.md / .mcp.json
├── .claude/
│   ├── settings.local.json   ← Permissions (généré)
│   ├── docs/                 ← Tables agents/workflows (@imports)
│   ├── hooks/                ← Scripts hooks
│   ├── agents/               ← Agents spécialisés
│   └── skills/               ← Skills promus (auto-learn --evolve)
├── workflows/                ← Pipelines end-to-end
├── scripts/                  ← gen.py, auto-learn.py, etc.
└── .template/                ← version.json, known-patterns.json, handoff.md
```
