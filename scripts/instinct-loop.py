#!/usr/bin/env python3
"""
instinct-loop.py — Cycle d'auto-évolution Homunculus pour claudekit

Observations légères → Instincts → Clusters thématiques → Promotion en skills/règles

Usage:
    python3 scripts/instinct-loop.py --add-observation "trigger" "action" "domain"
    python3 scripts/instinct-loop.py --cluster
    python3 scripts/instinct-loop.py --show-candidates
    python3 scripts/instinct-loop.py --generate-proposal
    python3 scripts/instinct-loop.py --report
"""

import argparse
import json
import math
import re
import string
import sys
import uuid
from datetime import date
from pathlib import Path

# ─── Chemins ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INSTINCTS_FILE = PROJECT_ROOT / ".template" / "instincts.json"
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"

# ─── Seuils ──────────────────────────────────────────────────────────────────

SIMILARITY_THRESHOLD = 0.40       # overlap de mots-clés pour fusionner deux instincts
CONFIDENCE_INCREMENT = 0.12        # gain de confiance par occurrence supplémentaire
CONFIDENCE_MAX = 0.95
CLUSTER_MATURITY_THRESHOLD = 0.60  # maturité minimale pour candidature à promotion
CLUSTER_MIN_INSTINCTS = 3          # nombre minimal d'instincts dans un cluster candidat

TODAY = date.today().isoformat()

# ─── Domaines reconnus ────────────────────────────────────────────────────────

KNOWN_DOMAINS = {
    "testing", "security", "git", "style", "architecture",
    "performance", "documentation", "workflow", "ml", "data",
    "devops", "refactor", "review", "other",
}

# ─── I/O ─────────────────────────────────────────────────────────────────────

def load_instincts() -> dict:
    """Charge .template/instincts.json. Crée la structure vide si absent."""
    if INSTINCTS_FILE.exists():
        try:
            data = json.loads(INSTINCTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "instincts" in data and "clusters" in data:
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return {"instincts": [], "clusters": [], "last_updated": None}


def save_instincts(data: dict) -> None:
    data["last_updated"] = TODAY
    INSTINCTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    INSTINCTS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ─── Heuristiques de similarité ──────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return " ".join(text.split())


def _keywords(text: str) -> set[str]:
    """Extrait les mots significatifs (longueur >= 4) d'un texte normalisé."""
    STOP = {
        "avec", "dans", "pour", "cette", "chaque", "toujours", "avant",
        "apres", "apres", "quand", "that", "this", "with", "when", "after",
        "before", "every", "always", "from", "into", "then", "should",
    }
    words = _normalize(text).split()
    return {w for w in words if len(w) >= 4 and w not in STOP}


def _similarity(a: str, b: str) -> float:
    """Jaccard sur les mots-clés des deux textes."""
    ka, kb = _keywords(a), _keywords(b)
    if not ka and not kb:
        return 1.0
    if not ka or not kb:
        return 0.0
    intersection = ka & kb
    union = ka | kb
    return len(intersection) / len(union)


# ─── Confiance ────────────────────────────────────────────────────────────────

def _confidence_for(occurrences: int) -> float:
    """Confiance croissante avec les occurrences, plafonnée à CONFIDENCE_MAX."""
    base = 0.40
    score = base + CONFIDENCE_INCREMENT * (occurrences - 1)
    return round(min(score, CONFIDENCE_MAX), 4)


# ─── add_observation ─────────────────────────────────────────────────────────

def add_observation(trigger: str, action: str, domain: str) -> dict:
    """
    Ajoute une observation. Si un instinct similaire existe → incrémente sa confiance.
    Retourne l'instinct créé ou mis à jour.
    """
    domain = domain.lower().strip()
    if domain not in KNOWN_DOMAINS:
        domain = "other"

    data = load_instincts()
    instincts = data["instincts"]

    combined_new = f"{trigger} {action}"

    # Chercher un instinct similaire dans le même domaine (ou domaines proches)
    best_match = None
    best_score = 0.0

    for inst in instincts:
        if inst.get("promoted"):
            continue
        combined_existing = f"{inst.get('trigger', '')} {inst.get('action', '')}"
        score = _similarity(combined_new, combined_existing)
        # Bonus si même domaine
        if inst.get("domain") == domain:
            score = min(score + 0.10, 1.0)
        if score > best_score:
            best_score = score
            best_match = inst

    if best_match and best_score >= SIMILARITY_THRESHOLD:
        # Incrémenter l'instinct existant
        best_match["occurrences"] = best_match.get("occurrences", 1) + 1
        best_match["confidence"] = _confidence_for(best_match["occurrences"])
        best_match["last_seen"] = TODAY
        print(
            f"[instinct-loop] Instinct existant renforcé "
            f"(similarity={best_score:.2f}, occurrences={best_match['occurrences']}, "
            f"confidence={best_match['confidence']:.2f}) : {best_match['trigger'][:60]}"
        )
        result = best_match
    else:
        # Créer un nouvel instinct
        new_inst = {
            "id": str(uuid.uuid4()),
            "trigger": trigger,
            "action": action,
            "domain": domain,
            "confidence": _confidence_for(1),
            "occurrences": 1,
            "first_seen": TODAY,
            "last_seen": TODAY,
            "promoted": False,
        }
        instincts.append(new_inst)
        print(
            f"[instinct-loop] Nouvel instinct enregistré "
            f"(domain={domain}, confidence={new_inst['confidence']:.2f}) : {trigger[:60]}"
        )
        result = new_inst

    data["instincts"] = instincts
    save_instincts(data)
    return result


# ─── cluster_instincts ────────────────────────────────────────────────────────

def cluster_instincts() -> list[dict]:
    """
    Regroupe les instincts non promus par domaine.
    Calcule la maturité : avg(confidence) * sqrt(count).
    Normalise pour garder maturité dans [0, 1].
    """
    data = load_instincts()
    instincts = data["instincts"]
    existing_clusters = {c["id"]: c for c in data.get("clusters", [])}

    # Grouper par domaine
    by_domain: dict[str, list[dict]] = {}
    for inst in instincts:
        if inst.get("promoted"):
            continue
        d = inst.get("domain", "other")
        by_domain.setdefault(d, []).append(inst)

    new_clusters: list[dict] = []

    for domain, members in by_domain.items():
        if not members:
            continue

        avg_conf = sum(m.get("confidence", 0.0) for m in members) / len(members)
        raw_maturity = avg_conf * math.sqrt(len(members))
        # Normaliser : maturité = 1.0 quand avg_conf=0.95 et count=6+
        # sqrt(6) * 0.95 ≈ 2.33  → on divise par 2.5 pour plafonner à ~0.93
        maturity = round(min(raw_maturity / 2.5, 1.0), 4)

        # Chercher un cluster existant pour ce domaine
        existing = next(
            (c for c in existing_clusters.values() if c.get("domain") == domain),
            None,
        )

        cluster_id = existing["id"] if existing else str(uuid.uuid4())
        promoted_to = existing["promoted_to"] if existing else None

        cluster = {
            "id": cluster_id,
            "domain": domain,
            "instinct_ids": [m["id"] for m in members],
            "name": f"cluster:{domain}",
            "description": _cluster_description(domain, members),
            "maturity": maturity,
            "promoted_to": promoted_to,
        }
        new_clusters.append(cluster)

    data["clusters"] = new_clusters
    save_instincts(data)

    print(f"[instinct-loop] {len(new_clusters)} cluster(s) recalculés.")
    for c in new_clusters:
        n = len(c["instinct_ids"])
        print(f"  [{c['domain']:<16}] maturité={c['maturity']:.2f}  instincts={n}")

    return new_clusters


def _cluster_description(domain: str, members: list[dict]) -> str:
    """Synthèse lisible du cluster à partir des triggers des instincts."""
    triggers = [m.get("trigger", "") for m in members[:5]]
    triggers_str = " | ".join(t[:50] for t in triggers if t)
    return f"Comportements observés dans le domaine '{domain}' : {triggers_str}"


# ─── get_promotion_candidates ─────────────────────────────────────────────────

def get_promotion_candidates() -> list[dict]:
    """Retourne les clusters avec maturité >= seuil ET count >= minimum ET non promus."""
    data = load_instincts()
    clusters = data.get("clusters", [])

    candidates = [
        c for c in clusters
        if c.get("maturity", 0.0) >= CLUSTER_MATURITY_THRESHOLD
        and len(c.get("instinct_ids", [])) >= CLUSTER_MIN_INSTINCTS
        and not c.get("promoted_to")
    ]
    return candidates


# ─── generate_claude_md_proposal ─────────────────────────────────────────────

def generate_claude_md_proposal(cluster: dict) -> str:
    """Génère un bloc markdown à insérer dans CLAUDE.md pour ce cluster."""
    domain = cluster.get("domain", "other")
    instinct_ids = set(cluster.get("instinct_ids", []))
    data = load_instincts()
    members = [i for i in data["instincts"] if i["id"] in instinct_ids]

    lines = [
        f"### Comportements automatiques — {domain}",
        "",
        f"<!-- Généré par instinct-loop — maturité={cluster['maturity']:.2f} | instincts={len(members)} -->",
        "",
    ]
    for m in members:
        trigger = m.get("trigger", "")
        action = m.get("action", "")
        if trigger and action:
            lines.append(f"- **Si** {trigger} **→** {action}")
        elif trigger:
            lines.append(f"- {trigger}")

    lines.append("")
    return "\n".join(lines)


# ─── generate_skill_proposal ──────────────────────────────────────────────────

def generate_skill_proposal(cluster: dict) -> str:
    """Génère le contenu d'un fichier .claude/skills/{domain}-instinct.md."""
    domain = cluster.get("domain", "other")
    instinct_ids = set(cluster.get("instinct_ids", []))
    data = load_instincts()
    members = [i for i in data["instincts"] if i["id"] in instinct_ids]

    avg_conf = (
        sum(m.get("confidence", 0.0) for m in members) / len(members)
        if members else 0.0
    )

    triggers_yaml = "\n".join(
        f'  - "{m.get("trigger", "")[:60]}"'
        for m in members[:4]
        if m.get("trigger")
    )

    lines = [
        "---",
        f"name: instinct-{domain}",
        f"description: Comportements auto-appris dans le domaine {domain} (Homunculus)",
        f"confidence: {avg_conf:.2f}",
        f"instinct_count: {len(members)}",
        f"maturity: {cluster['maturity']:.2f}",
        f"generated_on: {TODAY}",
        "triggers:",
        triggers_yaml,
        "---",
        "",
        f"# Instinct Skill: {domain}",
        "",
        "Patterns comportementaux observés et consolidés par le cycle Homunculus.",
        "Ces règles ont émergé de l'observation répétée du workflow.",
        "",
        "## Comportements",
        "",
    ]

    for m in members:
        trigger = m.get("trigger", "")
        action = m.get("action", "")
        conf = m.get("confidence", 0.0)
        occ = m.get("occurrences", 1)
        if trigger:
            lines.append(f"### {trigger[:70]}")
            if action:
                lines.append(f"**Action** : {action}")
            lines.append(f"**Confiance** : {conf:.2f} | **Observations** : {occ}")
            lines.append("")

    lines += [
        "## Application",
        "",
        "- Appliquer ces comportements dès que le déclencheur est reconnu",
        "- Signaler si le comportement attendu ne correspond plus au contexte du projet",
        f"- Pour ajouter une observation : `python3 scripts/instinct-loop.py --add-observation \"trigger\" \"action\" \"{domain}\"`",
        "",
    ]

    return "\n".join(lines)


# ─── show_candidates ─────────────────────────────────────────────────────────

def show_candidates() -> None:
    """Affiche les clusters candidats à promotion avec leur détail."""
    candidates = get_promotion_candidates()

    if not candidates:
        data = load_instincts()
        clusters = data.get("clusters", [])
        print("[instinct-loop] Aucun cluster candidat à promotion.")
        print(
            f"  Seuils : maturité >= {CLUSTER_MATURITY_THRESHOLD} "
            f"ET >= {CLUSTER_MIN_INSTINCTS} instincts"
        )
        if clusters:
            print("\n  Clusters actuels (non candidats) :")
            for c in clusters:
                n = len(c.get("instinct_ids", []))
                print(
                    f"    [{c['domain']:<16}] maturité={c.get('maturity', 0):.2f}  "
                    f"instincts={n}  promu={bool(c.get('promoted_to'))}"
                )
        return

    print(f"[instinct-loop] {len(candidates)} cluster(s) candidat(s) :\n")
    for i, c in enumerate(candidates, 1):
        n = len(c.get("instinct_ids", []))
        print(
            f"  {i}. [{c['domain']}] maturité={c['maturity']:.2f}  instincts={n}"
        )
        print(f"     {c.get('description', '')[:100]}")
        print()


# ─── generate_proposal ───────────────────────────────────────────────────────

def generate_proposal() -> None:
    """Génère les propositions de skill et de règle CLAUDE.md pour les clusters candidats."""
    candidates = get_promotion_candidates()

    if not candidates:
        print("[instinct-loop] Aucune proposition à générer (pas de cluster candidat).")
        return

    for cluster in candidates:
        domain = cluster.get("domain", "other")

        # Skill
        skill_content = generate_skill_proposal(cluster)
        skill_filename = f"instinct-{domain}.md"
        skill_path = SKILLS_DIR / skill_filename

        print(f"\n{'='*60}")
        print(f"PROPOSITION SKILL : .claude/skills/{skill_filename}")
        print(f"{'='*60}")
        print(skill_content)

        # Règle CLAUDE.md
        claude_md_block = generate_claude_md_proposal(cluster)
        print(f"\n{'='*60}")
        print(f"PROPOSITION CLAUDE.md (section AUTOMATISATIONS) :")
        print(f"{'='*60}")
        print(claude_md_block)

        print(
            f"\n  → Pour appliquer le skill : copie le bloc ci-dessus dans {skill_path}"
        )
        print(
            f"  → Pour appliquer la règle : insere le bloc CLAUDE.md dans la section appropriée"
        )
        print(
            f"  → Aucune modification automatique — validation utilisateur requise"
        )


# ─── report ──────────────────────────────────────────────────────────────────

def report() -> None:
    """Rapport complet : instincts, clusters, candidats."""
    data = load_instincts()
    instincts = data.get("instincts", [])
    clusters = data.get("clusters", [])
    candidates = get_promotion_candidates()

    total = len(instincts)
    promoted = sum(1 for i in instincts if i.get("promoted"))
    active = total - promoted

    print("=" * 60)
    print("  instinct-loop — Rapport Homunculus")
    print("=" * 60)
    print(f"  Instincts total    : {total}")
    print(f"  Actifs             : {active}")
    print(f"  Promus             : {promoted}")
    print(f"  Clusters           : {len(clusters)}")
    print(f"  Candidats promotion: {len(candidates)}")
    print(f"  Dernière MAJ       : {data.get('last_updated', 'jamais')}")
    print()

    if instincts:
        print("  Instincts par domaine :")
        by_domain: dict[str, int] = {}
        for inst in instincts:
            d = inst.get("domain", "other")
            by_domain[d] = by_domain.get(d, 0) + 1
        for d, count in sorted(by_domain.items(), key=lambda x: -x[1]):
            print(f"    [{d:<16}] {count}")
        print()

    if clusters:
        print("  Clusters (maturité) :")
        for c in sorted(clusters, key=lambda x: -x.get("maturity", 0)):
            n = len(c.get("instinct_ids", []))
            mark = " [CANDIDAT]" if c in candidates else ""
            print(
                f"    [{c['domain']:<16}] maturité={c.get('maturity', 0):.2f}  "
                f"n={n}{mark}"
            )
        print()

    if candidates:
        print("  Pour générer les propositions :")
        print("    python3 scripts/instinct-loop.py --generate-proposal")

    print("=" * 60)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="instinct-loop.py — Cycle d'auto-évolution Homunculus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--add-observation",
        nargs=3,
        metavar=("TRIGGER", "ACTION", "DOMAIN"),
        help="Ajouter une observation. Domain: " + "|".join(sorted(KNOWN_DOMAINS)),
    )
    parser.add_argument(
        "--cluster",
        action="store_true",
        help="Recalculer les clusters par domaine",
    )
    parser.add_argument(
        "--show-candidates",
        action="store_true",
        help="Afficher les clusters candidats à promotion",
    )
    parser.add_argument(
        "--generate-proposal",
        action="store_true",
        help="Générer les propositions de skill et règle CLAUDE.md",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Rapport complet : instincts, clusters, candidats",
    )

    args = parser.parse_args()

    if args.add_observation:
        trigger, action, domain = args.add_observation
        add_observation(trigger, action, domain)
        return

    if args.cluster:
        cluster_instincts()
        return

    if args.show_candidates:
        show_candidates()
        return

    if args.generate_proposal:
        generate_proposal()
        return

    if args.report:
        report()
        return

    parser.print_help()


if __name__ == "__main__":
    main()
