# MCP Server Catalog 2026

> Référence complète des serveurs MCP recommandés pour claudekit.
> Mis à jour : mars 2026

---

## Servers officiels Anthropic / natifs Claude.ai (zéro config)

Ces intégrations sont disponibles directement dans Claude.ai sans installation.

| Nom | Ce que ça apporte | Cas d'usage |
|-----|-------------------|-------------|
| `gmail` | Lecture et envoi d'emails depuis Claude | Triage, réponses automatisées, résumés |
| `google-calendar` | Accès aux événements et disponibilités | Planification, rappels, extraction d'agenda |
| `canva` | Génération de visuels depuis Claude | Créer des slides, bannières, assets marketing |
| `claude-in-chrome` | Claude lit la page ouverte dans le navigateur | Analyser une doc, un formulaire, un dashboard |

---

## Déjà inclus dans le template

Ces serveurs sont référencés dans le setup interview et gérés par `gen.py`.

| Nom | Package | Usage principal |
|-----|---------|----------------|
| `filesystem` | `@modelcontextprotocol/server-filesystem` | Lecture/écriture fichiers hors cwd |
| `github` | `@modelcontextprotocol/server-github` | PRs, issues, repos GitHub |
| `postgres` | `@modelcontextprotocol/server-postgres` | Requêtes SQL sur PostgreSQL |
| `sqlite` | `@modelcontextprotocol/server-sqlite` | Base SQLite locale |
| `brave-search` | `@modelcontextprotocol/server-brave-search` | Recherche web (clé API Brave) |
| `slack` | `@modelcontextprotocol/server-slack` | Canaux, messages, utilisateurs Slack |
| `linear` | `@linear/mcp-server` | Issues, projets, cycles Linear |
| `notion` | `@modelcontextprotocol/server-notion` | Pages, bases de données Notion |
| `playwright` | `@modelcontextprotocol/server-playwright` | Automatisation navigateur, tests E2E |
| `desktop-commander` | `desktop-commander` | Contrôle du bureau, apps macOS/Windows |

---

## Développement — Documentation & Anti-hallucination

### Context7
- **Package** : `@upstash/context7-mcp`
- **Installation** : `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest`
- **Ce que ça apporte** : injecte la documentation officielle version-spécifique d'une librairie directement dans le contexte, en temps réel — élimine les hallucinations d'API obsolètes.
- **Cas d'usage** : ajouter `use context7` dans un prompt pour obtenir la vraie doc de React 19, Next.js 15, etc.

---

## Développement — Bases de données

Les serveurs `postgres` et `sqlite` sont déjà inclus dans le template. Pour d'autres bases :

| Nom | Package | Notes |
|-----|---------|-------|
| `mysql` | `@modelcontextprotocol/server-mysql` | MySQL / MariaDB |
| `mongodb` | `@khalidx/mongodb-mcp` | Collections MongoDB |
| `redis` | `@modelcontextprotocol/server-redis` | Clés Redis, pub/sub |

---

## Développement — Tests & Qualité

Le serveur `playwright` (déjà inclus) couvre les tests E2E. Pas de serveur MCP dédié aux tests unitaires — les outils natifs (Jest, pytest, etc.) sont préférables via bash.

---

## Raisonnement & Cognition

### Sequential Thinking
- **Package** : `@modelcontextprotocol/server-sequential-thinking`
- **Installation** : `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking@latest`
- **Ce que ça apporte** : force un raisonnement structuré en arbre avant d'agir — décompose les problèmes complexes en étapes vérifiables, avec backtracking si une hypothèse est invalidée.
- **Cas d'usage** : ajouter `use sequential thinking` dans le prompt pour les décisions d'architecture ou les bugs difficiles à reproduire.

---

## Mémoire & Connaissance

### Knowledge Graph Memory
- **Package** : `@modelcontextprotocol/server-memory`
- **Installation** : `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory`
- **Ce que ça apporte** : graphe de connaissance persistant cross-sessions — stocke des entités (personnes, projets, décisions) et leurs relations, interrogeable par Claude à chaque session.
- **Cas d'usage** : mémoriser les préférences utilisateur, les décisions d'architecture, les contextes de projet sur le long terme.

### Basic Memory (filesystem-based)
- **Package** : `@basicmachines/basic-memory` ou implémentation custom
- **Installation** : `claude mcp add basic-memory -- npx -y @basicmachines/basic-memory@latest`
- **Ce que ça apporte** : mémoire persistante au format Markdown natif — compatible avec Obsidian, lisible sans outil. Plus simple que le knowledge graph.
- **Cas d'usage** : notes de session, décisions à retenir, contexte léger sans overhead de graphe.

> **Note** : claudekit dispose déjà d'un système de mémoire fichier dans `.claude/agent-memory/`. Le serveur `memory` (knowledge graph) est complémentaire pour les relations complexes entre entités.

---

## Product & Design

### Figma MCP (Dev Mode)
- **Package** : intégration officielle Figma (plugin Dev Mode)
- **Installation** : activer dans Figma > Preferences > Dev Mode > Enable MCP Server. Nécessite un abonnement Figma Pro avec Dev Mode activé.
- **Ce que ça apporte** : expose la hiérarchie live des layers Figma — auto-layout, variants, design tokens, composants — pour générer du code directement depuis le vrai design sans copier-coller de specs.
- **Cas d'usage** : générer des composants React/Tailwind fidèles au design, extraire les tokens de couleur et typographie.

---

## Monitoring & Erreurs

### Sentry MCP
- **Package** : `@sentry/mcp-server`
- **Installation** : `claude mcp add sentry -- npx -y @sentry/mcp-server@latest`
- **Ce que ça apporte** : accès direct aux issues Sentry avec stack traces complètes, breadcrumbs, session replay et contexte utilisateur — Claude peut analyser et corriger des bugs avec le contexte réel d'erreur.
- **Cas d'usage** : `fix the top Sentry issue in my project` — Claude lit l'issue, trace la cause, propose le fix.

---

## Finance & Payments

### Stripe MCP
- **Package** : `@stripe/mcp-server`
- **Installation** : `claude mcp add stripe -- npx -y @stripe/mcp-server@latest`
- **Ce que ça apporte** : accès en lecture aux customers, invoices, subscriptions et événements Stripe — Claude peut analyser des problèmes de facturation, générer des rapports, diagnostiquer des échecs de paiement.
- **Cas d'usage** : `why did customer X's payment fail last week ?` — Claude interroge Stripe et analyse les logs.

> **Securite** : ce serveur est read-only par défaut. Ne jamais lui donner une clé Stripe avec permissions d'écriture.

---

## Productivité & Communication

Les serveurs `slack`, `linear` et `notion` sont déjà inclus dans le template. Serveurs complémentaires :

| Nom | Package | Notes |
|-----|---------|-------|
| `jira` | `@modelcontextprotocol/server-jira` | Issues et sprints Jira |
| `confluence` | `@modelcontextprotocol/server-confluence` | Pages et espaces Confluence |
| `google-drive` | `@modelcontextprotocol/server-gdrive` | Fichiers et docs Google Drive |

---

## Claude Code comme serveur MCP

Claude Code peut s'exposer lui-même comme serveur MCP pour être appelé depuis d'autres clients.

**Ce que ça permet :**
- Cursor, Windsurf ou Claude Desktop peuvent utiliser les outils Claude Code (lecture de fichiers, exécution de commandes, édition) via le protocole MCP
- Orchestration multi-agents entre différents clients

**Activation :**
```bash
# Exposer Claude Code comme serveur MCP (écoute en stdio)
claude mcp serve

# Puis dans le client MCP cible (.mcp.json ou settings) :
# {
#   "claude-code": {
#     "command": "claude",
#     "args": ["mcp", "serve"],
#     "cwd": "/chemin/vers/projet"
#   }
# }
```

---

## Vetting avant installation

Tout serveur MCP non listé ici doit passer par le workflow `workflows/mcp-vetting.md` avant d'être ajouté à un projet.

Critères minimaux :
- Repo public avec auteur identifiable
- Dernier commit < 6 mois
- Pas de `eval()`, exfiltration de données ou permissions réseau non justifiées
- Testé en sandbox avant ajout au manifest
