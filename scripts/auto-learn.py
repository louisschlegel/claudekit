#!/usr/bin/env python3
"""
auto-learn.py — Extrait les apprentissages des outputs d'agents et met à jour learning.md

Usage:
    python3 scripts/auto-learn.py --from-agent reviewer --input '{"verdict":"CHANGES_REQUIRED","blockers":[...]}'
    python3 scripts/auto-learn.py --from-agent debug-detective --input '{...}'
    python3 scripts/auto-learn.py --from-agent security-auditor --input '{...}'
    python3 scripts/auto-learn.py --extract-patterns  # analyse learning.md et propose des custom_rules
    python3 scripts/auto-learn.py --show-stats        # stats sur les apprentissages accumulés
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

# ─── Chemins ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
LEARNING_MD = PROJECT_ROOT / "learning.md"
MANIFEST = PROJECT_ROOT / "project.manifest.json"

# ─── Sections de learning.md ─────────────────────────────────────────────────

SECTION_HEADERS = {
    "architecture": "## 1. Architecture & Décisions",
    "patterns": "## 2. Patterns & Conventions",
    "stack": "## 3. Stack & Config",
    "workflow": "## 4. Workflow",
    "bugs": "## 5. Bugs résolus",
    "wip": "## 6. Travail en cours",
    "auto-rules": "## 7. Règles auto-extraites",
}

TODAY = date.today().isoformat()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_learning_md() -> str:
    if not LEARNING_MD.exists():
        sys.exit(f"[auto-learn] learning.md introuvable : {LEARNING_MD}")
    return LEARNING_MD.read_text(encoding="utf-8")


def save_learning_md(content: str) -> None:
    LEARNING_MD.write_text(content, encoding="utf-8")


def insert_after_section(content: str, section_key: str, entry: str) -> str:
    """Insère `entry` juste après le header de section correspondant."""
    header = SECTION_HEADERS.get(section_key)
    if header is None:
        print(f"[auto-learn] Section inconnue : {section_key}", file=sys.stderr)
        return content

    # Chercher le header dans le contenu
    idx = content.find(header)
    if idx == -1:
        # Section absente : l'ajouter à la fin
        content = content.rstrip() + f"\n\n{header}\n\n{entry.strip()}\n"
        print(f"[auto-learn] Section '{header}' créée à la fin de learning.md")
        return content

    # Trouver la fin de la ligne du header
    end_of_header_line = content.find("\n", idx)
    if end_of_header_line == -1:
        end_of_header_line = len(content)

    # Insérer après la ligne du header (et la ligne vide suivante si présente)
    insert_pos = end_of_header_line + 1
    # Passer les lignes vides/commentaires HTML immédiats
    remaining = content[insert_pos:]
    skip = 0
    for line in remaining.splitlines(keepends=True):
        if line.strip() == "" or line.strip().startswith("<!--"):
            skip += len(line)
        else:
            break

    insert_pos += skip
    content = content[:insert_pos] + entry.strip() + "\n\n" + content[insert_pos:]
    return content


def truncate(text: str, max_len: int = 120) -> str:
    return text if len(text) <= max_len else text[:max_len - 3] + "..."


# ─── Parseurs par agent ───────────────────────────────────────────────────────

def parse_reviewer(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue (JSON structuré) :
    {
      "verdict": "APPROVED" | "CHANGES_REQUIRED",
      "blockers": [{"file": "...", "line": "...", "description": "...", "suggestion": "..."}],
      "warnings": [...],
      "suggestions": [...],
      "summary": "...",
      "auto_test_for": ["..."]   # optionnel
    }
    Aussi accepté : format texte brut du contrat de sortie.
    """
    entries = []

    verdict = data.get("verdict", "")
    summary = data.get("summary", "")
    blockers = data.get("blockers", [])
    auto_test_for = data.get("auto_test_for", [])

    if blockers:
        lines = [f"### {TODAY} — Reviewer : BLOCKERs récurrents"]
        if summary:
            lines.append(f"- **Contexte** : {truncate(summary)}")
        for b in blockers:
            loc = f"{b.get('file', '?')}:{b.get('line', '?')}"
            desc = truncate(b.get("description", ""))
            suggestion = b.get("suggestion", "")
            line = f"- **BLOCKER** `{loc}` — {desc}"
            if suggestion:
                line += f"  \n  → Fix : {truncate(suggestion)}"
            lines.append(line)
        entries.append(("patterns", "\n".join(lines)))

    if auto_test_for:
        todo_lines = [f"### {TODAY} — TODOs tests (reviewer)"]
        for item in auto_test_for:
            todo_lines.append(f"- [ ] Ajouter test : {truncate(item)}")
        entries.append(("wip", "\n".join(todo_lines)))

    return entries


def parse_debug_detective(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue :
    {
      "root_cause": "...",
      "affected_files": ["..."],
      "introduced_by": "...",
      "fix": {"file": "...", "change": "..."},
      "regression_test": "...",
      "learning_entry": "..."   # optionnel, entrée prête à coller
    }
    """
    # Si l'agent a fourni une entrée toute prête
    if data.get("learning_entry"):
        entry = f"### {TODAY} — Bug résolu\n{data['learning_entry'].strip()}"
        return [("bugs", entry)]

    root_cause = data.get("root_cause", "inconnu")
    affected = ", ".join(data.get("affected_files", []))
    introduced_by = data.get("introduced_by", "inconnu")
    fix = data.get("fix", {})
    fix_file = fix.get("file", "?")
    fix_change = fix.get("change", "?")
    regression_test = data.get("regression_test", "non spécifié")

    entry = (
        f"### {TODAY} — Bug résolu\n"
        f"- **Root cause** : {truncate(root_cause)}\n"
        f"- **Fichiers affectés** : {affected or '?'}\n"
        f"- **Introduit par** : {introduced_by}\n"
        f"- **Fix** : `{fix_file}` — {truncate(fix_change)}\n"
        f"- **Test de régression** : {truncate(regression_test)}"
    )
    return [("bugs", entry)]


def parse_security_auditor(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue :
    {
      "findings": [
        {"severity": "CRITICAL|HIGH|MEDIUM|LOW", "cwe": "CWE-xxx",
         "file": "...", "line": "...", "description": "...", "fix": "..."}
      ],
      "verdict": "CLEAR|FINDINGS_PRESENT",
      "release_gate": "PASS|BLOCK"
    }
    """
    findings = data.get("findings", [])
    high_critical = [f for f in findings if f.get("severity") in ("CRITICAL", "HIGH")]

    entries = []
    if high_critical:
        lines = [f"### {TODAY} — Audit sécurité [SÉCURITÉ]"]
        for f in high_critical:
            severity = f.get("severity", "?")
            cwe = f.get("cwe", "")
            loc = f"{f.get('file', '?')}:{f.get('line', '?')}"
            desc = truncate(f.get("description", ""))
            fix = f.get("fix", "")
            cwe_str = f" `{cwe}`" if cwe else ""
            line = f"- **{severity}**{cwe_str} `{loc}` — {desc}"
            if fix:
                line += f"  \n  → Fix appliqué : {truncate(fix)}"
            lines.append(line)
        entries.append(("bugs", "\n".join(lines)))

    return entries


def parse_architect(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue (HANDOFF JSON de l'architect) :
    {
      "recommendation": "option_N",
      "adr_title": "...",
      "decision": "...",
      "complexity": "S|M|L|XL",
      "risk": "LOW|MEDIUM|HIGH",
      "patterns_to_follow": ["..."],
      "learning_entry": "..."   # optionnel
    }
    """
    if data.get("learning_entry"):
        entry = f"### {TODAY} — ADR : {data.get('adr_title', 'sans titre')}\n{data['learning_entry'].strip()}"
        return [("architecture", entry)]

    adr_title = data.get("adr_title", "sans titre")
    decision = data.get("decision", "")
    complexity = data.get("complexity", "?")
    risk = data.get("risk", "?")
    patterns = data.get("patterns_to_follow", [])

    lines = [
        f"### {TODAY} — ADR : {adr_title}",
        f"- **Décision** : {truncate(decision)}",
        f"- **Complexité** : {complexity} | **Risque** : {risk}",
    ]
    if patterns:
        lines.append("- **Patterns à suivre** :")
        for p in patterns:
            lines.append(f"  - {truncate(p)}")

    return [("architecture", "\n".join(lines))]


def parse_ml_engineer(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue :
    {
      "problem": "...",
      "model_choice": "...",
      "rationale": "...",
      "results": {"train": "...", "val": "...", "test": "..."},
      "experiment": "..."
    }
    """
    problem = data.get("problem", "?")
    model = data.get("model_choice", "?")
    rationale = data.get("rationale", "")
    results = data.get("results", {})
    experiment = data.get("experiment", "")

    lines = [
        f"### {TODAY} — ML Experiment [ML]",
        f"- **Problème** : {truncate(problem)}",
        f"- **Modèle** : {model}",
    ]
    if rationale:
        lines.append(f"- **Rationale** : {truncate(rationale)}")
    if results:
        metrics = " | ".join(f"{k}: {v}" for k, v in results.items())
        lines.append(f"- **Résultats** : {metrics}")
    if experiment:
        lines.append(f"- **Expérience** : {experiment}")

    return [("patterns", "\n".join(lines))]


def parse_performance_analyst(data: dict) -> list[tuple[str, str]]:
    """
    Entrée attendue :
    {
      "hotspot": "fichier:ligne — description",
      "category": "N+1|algorithme|I/O|cache|mémoire",
      "current": "...",
      "expected": "...",
      "optimizations": [{"description": "...", "effort": "...", "impact": "..."}],
      "estimated_gain": "..."
    }
    """
    hotspot = data.get("hotspot", "?")
    category = data.get("category", "?")
    current = data.get("current", "")
    expected = data.get("expected", "")
    gain = data.get("estimated_gain", "")
    opts = data.get("optimizations", [])

    lines = [
        f"### {TODAY} — Performance [PERF]",
        f"- **Hotspot** : {truncate(hotspot)}",
        f"- **Catégorie** : {category}",
    ]
    if current:
        lines.append(f"- **Avant** : {truncate(current)}")
    if expected:
        lines.append(f"- **Après** : {truncate(expected)}")
    if gain:
        lines.append(f"- **Gain estimé** : {gain}")
    if opts:
        lines.append("- **Optimisations** :")
        for o in opts[:3]:  # max 3
            desc = truncate(o.get("description", ""))
            effort = o.get("effort", "?")
            impact = o.get("impact", "?")
            lines.append(f"  - {desc} (Effort: {effort}, Impact: {impact})")

    return [("patterns", "\n".join(lines))]


# ─── Dispatch ─────────────────────────────────────────────────────────────────

PARSERS = {
    "reviewer": parse_reviewer,
    "debug-detective": parse_debug_detective,
    "security-auditor": parse_security_auditor,
    "architect": parse_architect,
    "ml-engineer": parse_ml_engineer,
    "performance-analyst": parse_performance_analyst,
}


def process_agent_output(agent: str, input_json: str) -> None:
    parser = PARSERS.get(agent)
    if parser is None:
        sys.exit(f"[auto-learn] Agent inconnu : '{agent}'. Agents supportés : {list(PARSERS)}")

    try:
        data = json.loads(input_json)
    except json.JSONDecodeError as e:
        sys.exit(f"[auto-learn] JSON invalide : {e}")

    entries = parser(data)
    if not entries:
        print(f"[auto-learn] Aucune entrée à persister pour l'agent '{agent}'.")
        return

    content = load_learning_md()
    for section_key, entry_text in entries:
        content = insert_after_section(content, section_key, entry_text)
        print(f"[auto-learn] Entrée ajoutée dans la section '{SECTION_HEADERS[section_key]}'")

    save_learning_md(content)
    print(f"[auto-learn] learning.md mis à jour.")


# ─── --extract-patterns ───────────────────────────────────────────────────────

def extract_patterns() -> None:
    """
    Analyse les 20 dernières entrées de learning.md et propose des custom_rules
    candidates pour project.manifest.json. Sortie JSON.
    """
    content = load_learning_md()

    # Extraire toutes les entrées (lignes commençant par "### ")
    entry_lines = [l for l in content.splitlines() if l.startswith("### ")]
    recent = entry_lines[-20:]

    # Détecter les patterns récurrents par mots-clés
    keyword_patterns = [
        (r"N\+1", "Vérifier les N+1 queries avant tout merge ORM"),
        (r"BLOCKER.*null|null.*BLOCKER", "Valider systématiquement les valeurs nulles aux frontières"),
        (r"BLOCKER.*injection|injection.*BLOCKER", "Scanner les injections SQL/shell sur tout input utilisateur"),
        (r"\[SÉCURITÉ\].*CRITICAL", "Auditer la sécurité avant chaque release"),
        (r"\[PERF\].*cache", "Ajouter du cache Redis pour les calculs répétitifs"),
        (r"\[PERF\].*N\+1", "Utiliser l'eager loading par défaut pour les relations ORM"),
        (r"\[ML\]", "Logger toutes les expériences ML dans MLflow"),
        (r"ADR", "Documenter les décisions d'architecture dans learning.md"),
        (r"régression|regression", "Toujours ajouter un test de régression après un bugfix"),
        (r"secret|credential|token", "Scanner les secrets avant chaque commit"),
    ]

    candidates = []
    combined = "\n".join(recent)
    for pattern, rule in keyword_patterns:
        if re.search(pattern, combined, re.IGNORECASE):
            candidates.append({
                "rule": rule,
                "confidence": "HIGH" if combined.lower().count(pattern.split(r"\.")[0].lower()) >= 2 else "MEDIUM",
                "source": "auto-learn --extract-patterns",
            })

    # Lire les règles existantes pour ne pas dupliquer
    existing_rules = []
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            existing_rules = manifest.get("custom_rules", [])
        except (json.JSONDecodeError, KeyError):
            pass

    new_candidates = [c for c in candidates if c["rule"] not in existing_rules]

    output = {
        "analyzed_entries": len(recent),
        "candidates": new_candidates,
        "existing_custom_rules": existing_rules,
        "note": "Ajouter les règles HIGH-confidence dans project.manifest.json > custom_rules",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ─── --show-stats ─────────────────────────────────────────────────────────────

def show_stats() -> None:
    """Affiche des statistiques sur les apprentissages accumulés dans learning.md."""
    content = load_learning_md()
    lines = content.splitlines()

    section_counts: dict[str, int] = {}
    current_section = "preamble"
    tags = Counter()

    for line in lines:
        # Détecter une section de niveau 2
        for key, header in SECTION_HEADERS.items():
            if line.strip() == header:
                current_section = key
                break

        # Compter les entrées (sous-titres de niveau 3)
        if line.startswith("### "):
            section_counts[current_section] = section_counts.get(current_section, 0) + 1
            # Détecter les tags
            for tag in re.findall(r"\[([A-Z\ÉÈÀÙ]+)\]", line):
                tags[tag] += 1

    print("=" * 50)
    print("  learning.md — Statistiques")
    print("=" * 50)
    total = 0
    for key, header in SECTION_HEADERS.items():
        count = section_counts.get(key, 0)
        total += count
        print(f"  {header:<40} {count:>4} entrée(s)")
    print("-" * 50)
    print(f"  {'Total':<40} {total:>4} entrée(s)")

    if tags:
        print()
        print("  Tags :")
        for tag, count in tags.most_common():
            print(f"    [{tag}] × {count}")
    print("=" * 50)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="auto-learn.py — Pont entre outputs d'agents et learning.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--from-agent",
        metavar="AGENT",
        help=f"Agent source. Valeurs : {', '.join(PARSERS)}",
    )
    parser.add_argument(
        "--input",
        metavar="JSON",
        help="Output JSON de l'agent (string JSON ou '-' pour stdin)",
    )
    parser.add_argument(
        "--extract-patterns",
        action="store_true",
        help="Analyser les 20 dernières entrées et proposer des custom_rules (sortie JSON)",
    )
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Afficher les statistiques de learning.md",
    )

    args = parser.parse_args()

    if args.extract_patterns:
        extract_patterns()
        return

    if args.show_stats:
        show_stats()
        return

    if not args.from_agent:
        parser.error("--from-agent est requis (sauf avec --extract-patterns ou --show-stats)")

    if not args.input:
        parser.error("--input est requis avec --from-agent")

    input_json = sys.stdin.read() if args.input == "-" else args.input
    process_agent_output(args.from_agent, input_json)


if __name__ == "__main__":
    main()
