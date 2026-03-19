#!/usr/bin/env python3
"""
auto-learn.py — Extrait les apprentissages des outputs d'agents et met à jour learning.md

Usage:
    python3 scripts/auto-learn.py --from-agent reviewer --input '{"verdict":"CHANGES_REQUIRED","blockers":[...]}'
    python3 scripts/auto-learn.py --from-agent debug-detective --input '{...}'
    python3 scripts/auto-learn.py --from-agent security-auditor --input '{...}'
    python3 scripts/auto-learn.py --extract-patterns  # analyse learning.md et propose des custom_rules
    python3 scripts/auto-learn.py --show-stats        # stats sur les apprentissages accumulés
    python3 scripts/auto-learn.py --evolve            # liste les patterns éligibles et génère les skills
"""

import argparse
import json
import re
import sys
import uuid
from collections import Counter
from datetime import date
from pathlib import Path
import string

# ─── Chemins ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
LEARNING_MD = PROJECT_ROOT / "learning.md"
MANIFEST = PROJECT_ROOT / "project.manifest.json"
KNOWN_PATTERNS = PROJECT_ROOT / ".template" / "known-patterns.json"
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

# ─── Normalisation ───────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Normalise un texte pour la comparaison : lowercase + suppression ponctuation + strip."""
    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


# ─── Confidence scoring ──────────────────────────────────────────────────────

CONFIDENCE_BY_FREQUENCY = {1: 0.5, 2: 0.75}
CONFIDENCE_MAX = 0.95
CONFIDENCE_PROMOTION_THRESHOLD = 0.85


def _confidence_from_frequency(freq: int) -> float:
    """Calcule le score de confiance selon la fréquence d'observation."""
    if freq <= 1:
        return CONFIDENCE_BY_FREQUENCY[1]
    if freq == 2:
        return CONFIDENCE_BY_FREQUENCY[2]
    return CONFIDENCE_MAX


def load_known_patterns() -> dict:
    """Charge .template/known-patterns.json (crée la structure si absent/vide)."""
    if KNOWN_PATTERNS.exists():
        try:
            data = json.loads(KNOWN_PATTERNS.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "patterns" in data:
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return {"patterns": [], "last_updated": None}


def save_known_patterns(data: dict) -> None:
    data["last_updated"] = TODAY
    KNOWN_PATTERNS.parent.mkdir(parents=True, exist_ok=True)
    KNOWN_PATTERNS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _slugify(text: str) -> str:
    """Génère un slug valide pour nom de fichier."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text[:60] if text else "pattern"


def record_pattern(text: str) -> dict:
    """
    Enregistre ou incrémente un pattern dans known-patterns.json.
    Retourne le pattern mis à jour.
    """
    data = load_known_patterns()
    patterns = data.get("patterns", [])

    # Normalisation pour comparaison
    normalized = _normalize(text)

    # Chercher un pattern existant avec le même texte normalisé
    existing = None
    for p in patterns:
        if _normalize(p.get("text", "")) == normalized:
            existing = p
            break

    if existing:
        existing["frequency"] = existing.get("frequency", 1) + 1
        existing["confidence"] = _confidence_from_frequency(existing["frequency"])
        existing["last_seen"] = TODAY
    else:
        existing = {
            "id": str(uuid.uuid4()),
            "text": text,
            "frequency": 1,
            "confidence": _confidence_from_frequency(1),
            "first_seen": TODAY,
            "last_seen": TODAY,
            "promoted_to_skill": False,
            "skill_path": None,
        }
        patterns.append(existing)

    data["patterns"] = patterns
    save_known_patterns(data)
    return existing


def evolve_to_skill(pattern: dict) -> str:
    """
    Crée un fichier .claude/skills/{slug}.md documentant le pattern.
    Retourne le chemin du fichier créé.
    """
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    slug = _slugify(pattern.get("text", "pattern"))
    skill_path = SKILLS_DIR / f"{slug}.md"

    content = (
        f"---\n"
        f"name: {slug}\n"
        f"confidence: {pattern.get('confidence', 0.0)}\n"
        f"frequency: {pattern.get('frequency', 1)}\n"
        f"first_seen: {pattern.get('first_seen', TODAY)}\n"
        f"promoted_on: {TODAY}\n"
        f"---\n\n"
        f"# Skill: {pattern.get('text', '')}\n\n"
        f"## Description\n\n"
        f"{pattern.get('text', '')}\n\n"
        f"## Contexte\n\n"
        f"Pattern observé {pattern.get('frequency', 1)} fois depuis le {pattern.get('first_seen', TODAY)}. "
        f"Score de confiance : {pattern.get('confidence', 0.0):.2f}.\n\n"
        f"## Application\n\n"
        f"- Appliquer ce pattern systématiquement dans le contexte détecté\n"
        f"- Vérifier la cohérence avec les conventions existantes du projet\n"
    )

    skill_path.write_text(content, encoding="utf-8")
    return str(skill_path)


def evolve_patterns() -> None:
    """
    Liste les patterns éligibles (confidence >= 0.85) et génère les skills
    pour ceux qui ne sont pas encore promus.
    """
    data = load_known_patterns()
    patterns = data.get("patterns", [])

    eligible = [
        p for p in patterns
        if p.get("confidence", 0.0) >= CONFIDENCE_PROMOTION_THRESHOLD
        and not p.get("promoted_to_skill", False)
    ]

    if not eligible:
        print(f"[auto-learn] Aucun pattern éligible à la promotion (seuil: {CONFIDENCE_PROMOTION_THRESHOLD}).")
        already = [p for p in patterns if p.get("promoted_to_skill", False)]
        if already:
            print(f"[auto-learn] {len(already)} skill(s) déjà promus :")
            for p in already:
                print(f"  - {p.get('text', '?')} → {p.get('skill_path', '?')}")
        return

    print(f"[auto-learn] {len(eligible)} pattern(s) éligible(s) à la promotion en skill :\n")
    for i, p in enumerate(eligible, 1):
        print(f"  {i}. [{p.get('confidence', 0):.2f}] (×{p.get('frequency', 1)}) {p.get('text', '?')}")

    print()
    for p in eligible:
        skill_path = evolve_to_skill(p)
        p["promoted_to_skill"] = True
        p["skill_path"] = skill_path
        print(f"[auto-learn] Skill créé : {skill_path}")

    save_known_patterns(data)
    print(f"\n[auto-learn] {len(eligible)} skill(s) générés dans {SKILLS_DIR}")


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


# ─── --deduplicate ────────────────────────────────────────────────────────────

def deduplicate_entries(learning_file: Path | None = None) -> int:
    """
    Lit learning.md, détecte les entrées en double dans chaque section (même texte normalisé),
    garde la plus récente de chaque doublon, réécrit le fichier et retourne le nombre de
    suppressions.

    Une « entrée » est un bloc commençant par une ligne ### et se terminant avant la prochaine
    ligne ### ou avant un header de section (##).
    """
    target = learning_file or LEARNING_MD

    if not target.exists():
        sys.exit(f"[auto-learn] learning.md introuvable : {target}")

    content = target.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # ── Découper le contenu en blocs ──────────────────────────────────────────
    # Chaque bloc est soit un "header" (## ou titre de niveau 1), soit une "entry" (### …),
    # soit du contenu "flottant" (lignes hors entrée).

    class Block:
        __slots__ = ("kind", "section", "lines", "key")

        def __init__(self, kind: str, section: str, raw_lines: list[str]):
            self.kind = kind          # "header" | "entry" | "float"
            self.section = section    # clé de section courante
            self.lines = raw_lines    # lignes brutes
            self.key = _normalize("".join(raw_lines))  # clé de dédup

    blocks: list[Block] = []
    current_section = "__preamble__"
    current_kind: str | None = None
    current_lines: list[str] = []

    def flush(kind: str) -> None:
        if current_lines:
            blocks.append(Block(kind, current_section, list(current_lines)))
        current_lines.clear()

    for line in lines:
        stripped = line.strip()

        # Détection d'un header de section (## …)
        is_section_header = stripped.startswith("## ") or stripped == "##"
        # Détection d'une entrée (### …)
        is_entry_header = stripped.startswith("### ") or stripped == "###"

        if is_section_header:
            # Flush du bloc précédent
            if current_kind and current_lines:
                flush(current_kind)
            current_kind = "header"
            current_lines.clear()
            current_lines.append(line)
            # Mettre à jour la section courante
            for key, header in SECTION_HEADERS.items():
                if stripped == header:
                    current_section = key
                    break
            flush("header")
            current_kind = None

        elif is_entry_header:
            if current_kind and current_lines:
                flush(current_kind)
            current_kind = "entry"
            current_lines.clear()
            current_lines.append(line)

        else:
            if current_kind == "entry":
                # Les lignes non-header appartiennent à l'entrée en cours
                current_lines.append(line)
            else:
                # Contenu flottant (lignes vides, commentaires, etc. hors entrée)
                if current_kind == "float":
                    current_lines.append(line)
                else:
                    if current_kind and current_lines:
                        flush(current_kind)
                    current_kind = "float"
                    current_lines.clear()
                    current_lines.append(line)

    # Flush final
    if current_kind and current_lines:
        flush(current_kind)

    # ── Déduplication par section ─────────────────────────────────────────────
    # Parcours en ordre inverse pour garder la plus récente (dernière occurrence).
    seen: dict[str, set[str]] = {}  # section → ensemble de clés normalisées vues
    removed = 0
    kept_flags: list[bool] = []

    for block in reversed(blocks):
        if block.kind != "entry":
            kept_flags.append(True)
            continue

        section_seen = seen.setdefault(block.section, set())
        if block.key in section_seen:
            kept_flags.append(False)
            removed += 1
        else:
            section_seen.add(block.key)
            kept_flags.append(True)

    # Remettre dans l'ordre original
    kept_flags.reverse()

    # ── Reconstruction du fichier ─────────────────────────────────────────────
    new_lines: list[str] = []
    for block, keep in zip(blocks, kept_flags):
        if keep:
            new_lines.extend(block.lines)

    target.write_text("".join(new_lines), encoding="utf-8")

    if removed > 0:
        print(f"[auto-learn] {removed} entrée(s) dupliquée(s) supprimée(s) de learning.md")
    else:
        print("[auto-learn] Aucun doublon détecté dans learning.md")

    return removed


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
    parser.add_argument(
        "--deduplicate",
        action="store_true",
        help="Supprimer les entrées en double dans learning.md (garde la plus récente)",
    )
    parser.add_argument(
        "--record-pattern",
        metavar="TEXT",
        help="Enregistre ou incrémente un pattern dans .template/known-patterns.json",
    )
    parser.add_argument(
        "--evolve",
        action="store_true",
        help=f"Liste les patterns avec confidence >= {CONFIDENCE_PROMOTION_THRESHOLD} et génère les skills .claude/skills/",
    )

    args = parser.parse_args()

    if args.extract_patterns:
        extract_patterns()
        return

    if args.show_stats:
        show_stats()
        return

    if args.deduplicate:
        deduplicate_entries()
        return

    if args.record_pattern:
        p = record_pattern(args.record_pattern)
        print(f"[auto-learn] Pattern enregistré : confidence={p['confidence']:.2f} frequency={p['frequency']} — {p['text'][:80]}")
        return

    if args.evolve:
        evolve_patterns()
        return

    if not args.from_agent:
        parser.error("--from-agent est requis (sauf avec --extract-patterns, --show-stats, --evolve)")

    if not args.input:
        parser.error("--input est requis avec --from-agent")

    input_json = sys.stdin.read() if args.input == "-" else args.input
    process_agent_output(args.from_agent, input_json)


if __name__ == "__main__":
    main()
