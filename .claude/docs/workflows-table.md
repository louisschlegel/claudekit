## Routing des workflows

Le hook `user-prompt-submit.sh` classifie l'intention et l'injecte en contexte.
**Lis la classification et route immédiatement.**

| Intention détectée | Action |
|-------------------|--------|
| `hotfix` | → `workflows/hotfix.md` |
| `incident` | → `workflows/incident-response.md` |
| `db-migration` | → `workflows/db-migration.md` |
| `perf-test` | → `workflows/performance-baseline.md` |
| `publish` | → `workflows/publish-package.md` |
| `api-design` | → `workflows/api-design.md` |
| `feature` | → `workflows/feature.md` |
| `bugfix` | → `workflows/bugfix.md` |
| `release` | → `workflows/release.md` |
| `security-audit` | → `workflows/security-audit.md` |
| `update-deps` | → `workflows/dependency-update.md` |
| `refactor` | → `workflows/refactor.md` |
| `onboard` | → `workflows/onboarding.md` |
| `improve-template` | → `workflows/self-improve.md` |
| `ab-test` | → `workflows/a-b-test.md` |
| `data-quality` | → `workflows/data-quality.md` |
| `llm-eval` | → `workflows/llm-eval.md` |
| `spec-to-project` | → `workflows/spec-to-project.md` |
| `code-review` | → `workflows/code-review.md` |
| `monitoring-setup` | → `workflows/monitoring-setup.md` |
| `cost-optimization` | → `workflows/cost-optimization.md` |
| `dependency-audit` | → `workflows/dependency-audit.md` |
| `multi-agent` | → `workflows/multi-agent-worktrees.md` |
| `context-handoff` | → `workflows/context-handoff.md` |
| `notebook` | → `workflows/notebook-review.md` |
| `cost-dashboard` | → `workflows/cost-dashboard.md` |
| `riper` | → `workflows/riper.md` |
| `mcp-vetting` | → `workflows/mcp-vetting.md` |
| `agent-teams` | → `workflows/agent-teams.md` |
| `cost-audit` | → `workflows/cost-audit.md` |
| `skill-lifecycle` | → `workflows/skill-lifecycle.md` |
| `remote-dev` | → `workflows/remote-dev.md` |
| `monitoring-setup` | → `workflows/monitoring.md` |
| `question` | → réponse directe, pas de workflow |
| `other` | → demande de clarification, puis route |

**Pour invoquer un agent :** lis son fichier dans `.claude/agents/[nom].md`, puis utilise le tool `Agent` avec son contenu comme instructions. Passe toujours le contexte du manifest et le résultat du handoff précédent.

**Pour exécuter un workflow :** lis `workflows/[nom].md` et suis les étapes dans l'ordre. Respecte les gates — si une gate échoue, boucle ou escalade.
