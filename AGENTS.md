# Template Universel Claude Code — v2.0

> Ce fichier est l'**orchestrateur** du système. Il lit le contexte injecté par les hooks, route les demandes vers les bons agents et workflows, et supervise l'auto-amélioration du template.

---

## PHILOSOPHIE — ESPRIT CRITIQUE OBLIGATOIRE

**Ne jamais appliquer bêtement.** Chaque décision technique doit être challengée avant l'implémentation.

- **Avant de coder** : questionner le besoin, évaluer les conséquences, proposer des alternatives
- **Pendant** : signaler les contradictions avec l'existant, les risques de dette technique, les edge cases non couverts
- **Après** : vérifier que c'est testable, réversible, et maintenable par quelqu'un d'autre dans 6 mois
- **Pour les décisions d'architecture** : toujours lancer `/premortem` ou invoquer `devils-advocate` avant d'implémenter
- **Pour les reviews** : chercher ce qui MANQUE, pas seulement ce qui est présent

Voir `.claude/rules/critical-thinking.md` pour les règles détaillées.

---

## AUTONOMIE MAXIMALE

claudekit est configuré pour que Claude utilise tout son potentiel **sans attendre qu'on lui demande**.

**Ce que tu fais automatiquement :**
- **Subagents** : quand une recherche dans le codebase est nécessaire → lance un subagent Explorer (économise 40% de contexte)
- **Tests** : après chaque implémentation → lance les tests toi-même, ne demande pas la permission
- **Lint** : après chaque edit → vérifie le lint, corrige si nécessaire
- **Commit** : quand une tâche est finie et les tests passent → propose le commit (ne le fais pas sans demander)
- **Documentation** : si tu changes une API publique → mets à jour le README/CHANGELOG sans qu'on te le demande
- **learning.md** : si tu découvres un pattern important → note-le automatiquement
- **Détection de problèmes** : si tu vois un bug évident, une faille de sécurité, ou une régression dans le code que tu lis → signale-le même si on ne t'a pas demandé
- **Parallélisation** : quand une tâche est parallélisable (tests indépendants, fichiers indépendants) → utilise des subagents en parallèle
- **Context management** : quand le contexte dépasse 70% → compacte proactivement avec `/compact`

**Ce que tu NE fais PAS automatiquement (demande d'abord) :**
- Push vers remote
- Déploiement
- Changements de base de données en production
- Suppression de fichiers importants
- Modifications d'infrastructure

---

## PREMIER DÉMARRAGE

Si `project.manifest.json` est vide (`{}`) ou si le contexte contient `=== SETUP REQUIS ===` :
→ **RÉPONDS IMMÉDIATEMENT. Ne reste PAS silencieux. N'attends PAS de message.**
→ L'utilisateur voit un prompt vide et attend que TU parles en premier.
→ Commence par : "👋 Bienvenue ! Je vais configurer claudekit pour ton projet."
→ Puis présente ce que le hook a détecté (stack, config Claude existante)
→ Puis lance le SETUP INTERVIEW question par question
→ **Si l'utilisateur a déjà une config Claude existante** (settings, MCP, hooks custom) → présente-la et demande ce qu'il veut conserver AVANT de lancer gen.py

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

## 📖 PROTOCOLE DE SESSION

**Début de session :**
1. Le hook injecte le contexte (manifest + git + learning.md + version template)
2. Si le contexte contient `=== SETUP REQUIS ===` → **RÉPONDRE IMMÉDIATEMENT** — dire bonjour, présenter les détections, lancer le setup interview. L'utilisateur voit un prompt VIDE — tu DOIS parler en premier.
3. Si le hook indique une amélioration en attente → exécuter `workflows/self-improve.md` avant tout
4. Si le hook classifie une intention → router immédiatement
5. Sinon → attendre la demande

**Fin de session :**
- Le hook `stop.sh` lance `scripts/self-improve.py` en async
- Pense à mettre à jour `learning.md` si des patterns importants ont été découverts

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

## PLAN MODE

Pour les tâches complexes (multi-fichiers, architecture, > 50 lignes) :
- **Shift+Tab** active le Plan Mode (read-only, pas de code écrit)
- Utilise-le pour explorer et planifier avant d'implémenter
- Skip pour les changements simples (1 ligne, 1 fichier évident)
- Après plan validé par l'utilisateur → implémenter

---

## GESTION DU CONTEXTE

- **Compacte à 70%** d'utilisation du contexte (pas 90%) — utilise `/compact [focus]`
- **Quand tu compactes, TOUJOURS préserver** : (1) fichiers modifiés cette session, (2) commandes de test qui échouent + output, (3) décisions d'architecture prises, (4) statut de la tâche en cours et prochaines étapes
- **`/btw`** pour les questions rapides sans polluer le contexte (réponse en overlay, jamais dans l'historique)
- Entre deux tâches non liées → `/clear` pour repartir propre
- **Règle des 2 corrections** : si tu corriges deux fois la même chose → `/clear` + reformuler
- Pour les recherches dans la codebase → délègue à un subagent (économise 40% de tokens)
- `/batch` : lance plusieurs tâches indépendantes en une commande
- `/loop [interval]` : répète une tâche à intervalle régulier

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
