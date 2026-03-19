#!/bin/bash
# Hook: UserPromptSubmit — Intent classification + prompt injection detection
# Bootstrap version (avant gen.py) — même logique que la version générée
# Auto-portable via BASH_SOURCE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('prompt',''))" 2>/dev/null || echo "")

python3 - "$PROMPT" <<'PYEOF'
import sys, json, re

prompt = sys.argv[1].lower() if len(sys.argv) > 1 else ""

# ── Injection detection ──────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions",
    r"disregard (previous|all|your) (instructions|rules)",
    r"you are now (a |an )?(?!claude)",
    r"new (system |)prompt",
    r"forget (everything|all) (you|your)",
    r"override (your |)instructions",
    r"jailbreak",
    r"<\|im_start\|>|<\|endoftext\|>|\[INST\]|\[\/INST\]",
]

for pattern in INJECTION_PATTERNS:
    if re.search(pattern, prompt, re.IGNORECASE):
        print(json.dumps({
            "decision": "block",
            "reason": f"Possible prompt injection detected (pattern: '{pattern}'). If this is a legitimate request, rephrase it."
        }))
        sys.exit(0)

# ── Intent classification ────────────────────────────────────────────────────
INTENT_RULES = [
    ("hotfix",            ["hotfix", "urgence prod", "correctif immédiat", "ça crashe en prod", "emergency", "production down", "service down"]),
    ("incident",          ["incident prod", "incident en prod", "alerte critique", "service dégradé", "sla breach", "p1 incident", "p2 incident", "production incident", "service down", "service unavailable", "outage"]),
    ("db-migration",      ["migration db", "migration base", "ajoute une migration", "modifie le schéma", "alter table", "nouvelle colonne", "supprime une colonne", "rename colonne", "add column", "drop column", "migrate schema", "schema migration"]),
    ("perf-test",         ["test de charge", "load test", "benchmark", "tient la charge", "mesure les performances", "profile l'appli", "locust", "k6", "performance test", "stress test", "perf baseline"]),
    ("publish",           ["publie le package", "publie sur pypi", "publie sur npm", "npm publish", "publish to pypi", "release library", "publie la librairie", "crates.io", "rubygems", "publish package"]),
    ("api-design",        ["design l'api", "design api", "nouvel endpoint", "api first", "contrat api", "définis le schéma", "ajoute un endpoint", "openapi", "graphql schema", "grpc proto", "api contract"]),
    ("ab-test",           ["a/b test", "feature flag", "split test", "rollout progressif", "expérimentation", "statistical significance"]),
    ("data-quality",      ["qualité des données", "data quality", "great expectations", "données corrompues", "anomalie de données"]),
    ("llm-eval",          ["évalue le rag", "llm eval", "ragas", "qualité des réponses", "hallucination", "benchmark llm", "rag evaluation"]),
    ("spec-to-project",   ["cahier des charges", "cahier de charges", "analyse cette spec", "voici les specs", "voici mon brief", "prd", "product requirement", "génère le projet depuis", "setup depuis spec", "j'ai un document de spec", "analyse ce document"]),
    ("code-review",       ["review cette pr", "relis ce code", "code review", "analyse ces changements", "review le diff", "donne moi un review", "relecture", "pr review"]),
    ("monitoring-setup",  ["setup monitoring", "configure observabilité", "ajoute prometheus", "grafana", "datadog", "configure les alertes", "métriques", "logs centralisés", "tracing", "observabilité"]),
    ("cost-optimization", ["optimise les coûts", "réduis les coûts cloud", "trop cher aws", "facture cloud", "optimise les tokens", "rightsizing", "coûts llm", "burn rate trop élevé", "coût infrastructure"]),
    ("dependency-audit",  ["audit les dépendances", "vérifie les cve", "scan les vulnérabilités", "dépendances vulnérables", "npm audit", "pip-audit", "security scan deps", "snyk", "licence check"]),
    ("multi-agent",       ["multi-agent", "parallel agents", "worktrees parallèles", "agents en parallèle", "parallélise"]),
    ("context-handoff",   ["handoff", "passe le contexte", "reprends la session", "continue de là"]),
    ("notebook",          ["notebook", "jupyter", "ipynb", "cellules"]),
    ("cost-dashboard",    ["coûts session", "dashboard coûts", "usage tokens", "combien ça coûte"]),
    ("release",           ["release", "prépare une version", "prépare la version", "tag v", "déploie une release"]),
    ("bugfix",            ["bug", "crash", "erreur", "error", "fixe", "corrige", "ça marche pas", "broken", "regression", "régression"]),
    ("security-audit",    ["audit", "sécurité", "security", "vulnérabilité", "scan", "cve", "faille"]),
    ("update-deps",       ["mets à jour les dépendances", "update deps", "update dependencies", "upgrade packages", "outdated packages"]),
    ("refactor",          ["refactor", "nettoie", "restructure", "améliore la structure", "clean up", "dette technique"]),
    ("improve-template",  ["améliore le template", "self-improve", "mets-toi à jour", "update template", "template improve"]),
    ("onboard",           ["setup", "initialise", "configure le projet", "onboard", "nouveau projet", "legacy"]),
    ("feature",           ["implémente", "ajoute", "crée une feature", "nouvelle feature", "add feature", "implement"]),
    ("question",          ["comment", "comment fonctionne", "explique", "qu'est-ce que", "pourquoi", "what is", "how does", "explain"]),
]

intent = "other"
for intent_name, keywords in INTENT_RULES:
    if any(kw in prompt for kw in keywords):
        intent = intent_name
        break

# Inject intent as context (not blocking)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"[INTENT:{intent}] — Voir CLAUDE.md routing table pour le workflow correspondant."
    }
}))
PYEOF

exit 0
