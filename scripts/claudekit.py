#!/usr/bin/env python3
"""
claudekit.py — CLI wrapper unifiant les opérations courantes du template

Usage:
    python3 scripts/claudekit.py validate
    python3 scripts/claudekit.py check
    python3 scripts/claudekit.py gen
    python3 scripts/claudekit.py bump patch|minor|major
    python3 scripts/claudekit.py status
    python3 scripts/claudekit.py install [path]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ─── Chemins ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent


# ─── Helpers ──────────────────────────────────────────────────────────────────

def run(cmd: list[str], cwd: Path = PROJECT_ROOT) -> int:
    """Lance une commande et retourne le code de retour."""
    result = subprocess.run(cmd, cwd=str(cwd))
    return result.returncode


def run_shell(cmd: str, cwd: Path = PROJECT_ROOT) -> int:
    """Lance une commande shell et retourne le code de retour."""
    result = subprocess.run(cmd, shell=True, cwd=str(cwd))
    return result.returncode


# ─── Commandes ────────────────────────────────────────────────────────────────

def cmd_validate() -> int:
    """Lance make validate."""
    print("[claudekit] Lancement de make validate...")
    return run(["make", "validate"])


def cmd_check() -> int:
    """Lance bash scripts/check.sh."""
    check_script = PROJECT_ROOT / "scripts" / "check.sh"
    if not check_script.exists():
        print(f"[claudekit] ERREUR : {check_script} introuvable.", file=sys.stderr)
        return 1
    print("[claudekit] Lancement de scripts/check.sh...")
    return run(["bash", str(check_script)])


def cmd_gen() -> int:
    """Lance python3 scripts/gen.py."""
    gen_script = PROJECT_ROOT / "scripts" / "gen.py"
    if not gen_script.exists():
        print(f"[claudekit] ERREUR : {gen_script} introuvable.", file=sys.stderr)
        return 1
    print("[claudekit] Lancement de scripts/gen.py...")
    return run([sys.executable, str(gen_script)])


def cmd_bump(level: str) -> int:
    """Lance python3 scripts/version-bump.py avec le niveau spécifié."""
    valid_levels = ("patch", "minor", "major")
    if level not in valid_levels:
        print(
            f"[claudekit] ERREUR : niveau invalide '{level}'. Valeurs : {', '.join(valid_levels)}",
            file=sys.stderr,
        )
        return 1
    bump_script = PROJECT_ROOT / "scripts" / "version-bump.py"
    if not bump_script.exists():
        print(f"[claudekit] ERREUR : {bump_script} introuvable.", file=sys.stderr)
        return 1
    print(f"[claudekit] Bump de version : {level}...")
    return run([sys.executable, str(bump_script), level])


def cmd_status() -> int:
    """Affiche l'état du projet : version, agents, workflows, scripts, manifest."""
    # Version depuis .template/version.json
    version_file = PROJECT_ROOT / ".template" / "version.json"
    if version_file.exists():
        try:
            version_data = json.loads(version_file.read_text(encoding="utf-8"))
            version = version_data.get("version", "inconnue")
        except (json.JSONDecodeError, KeyError):
            version = "invalide (JSON corrompu)"
    else:
        version = "inconnue (.template/version.json absent)"

    # Nombre d'agents
    agents_dir = PROJECT_ROOT / ".claude" / "agents"
    if agents_dir.exists():
        agents = sorted(agents_dir.glob("*.md"))
        agents_count = len(agents)
        agents_names = [a.stem for a in agents]
    else:
        agents_count = 0
        agents_names = []

    # Nombre de workflows
    workflows_dir = PROJECT_ROOT / "workflows"
    if workflows_dir.exists():
        workflows = sorted(workflows_dir.glob("*.md"))
        workflows_count = len(workflows)
        workflows_names = [w.stem for w in workflows]
    else:
        workflows_count = 0
        workflows_names = []

    # Scripts disponibles
    scripts_dir = PROJECT_ROOT / "scripts"
    if scripts_dir.exists():
        scripts = sorted(
            p.name
            for p in scripts_dir.iterdir()
            if p.is_file() and p.suffix in (".py", ".sh")
        )
    else:
        scripts = []

    # État du manifest
    manifest_file = PROJECT_ROOT / "project.manifest.json"
    if not manifest_file.exists():
        manifest_status = "absent"
    else:
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            if manifest_data:
                project_name = manifest_data.get("project", {}).get("name", "?")
                manifest_status = f"configuré (projet : {project_name})"
            else:
                manifest_status = "vide ({}) — setup non effectué"
        except json.JSONDecodeError:
            manifest_status = "invalide (JSON corrompu)"

    # Affichage
    sep = "=" * 56
    print(sep)
    print("  claudekit — Status")
    print(sep)
    print(f"  Version template   : {version}")
    print(f"  Manifest           : {manifest_status}")
    print(sep)
    print(f"  Agents ({agents_count})")
    for name in agents_names:
        print(f"    • {name}")
    print(sep)
    print(f"  Workflows ({workflows_count})")
    for name in workflows_names:
        print(f"    • {name}")
    print(sep)
    print(f"  Scripts ({len(scripts)})")
    for name in scripts:
        print(f"    • {name}")
    print(sep)
    return 0


def cmd_install(target_path: str | None) -> int:
    """Lance install.sh dans le répertoire cible."""
    install_script = PROJECT_ROOT / "install.sh"
    if not install_script.exists():
        print(f"[claudekit] ERREUR : {install_script} introuvable.", file=sys.stderr)
        return 1

    if target_path:
        target = Path(target_path).resolve()
        if not target.exists():
            print(f"[claudekit] ERREUR : répertoire cible '{target}' introuvable.", file=sys.stderr)
            return 1
        print(f"[claudekit] Installation dans {target}...")
        return run(["bash", str(install_script), str(target)])
    else:
        print("[claudekit] Installation dans le répertoire courant...")
        return run(["bash", str(install_script)])


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="claudekit — CLI wrapper pour les opérations du template Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMANDE")

    subparsers.add_parser("validate", help="Lance make validate (CI complète)")
    subparsers.add_parser("check", help="Lance bash scripts/check.sh (check rapide)")
    subparsers.add_parser("gen", help="Lance python3 scripts/gen.py (régénère la config)")

    bump_parser = subparsers.add_parser("bump", help="Bump de version (patch|minor|major)")
    bump_parser.add_argument(
        "level",
        choices=["patch", "minor", "major"],
        help="Niveau de bump",
    )

    subparsers.add_parser(
        "status",
        help="Affiche version, agents, workflows, scripts, état du manifest",
    )

    install_parser = subparsers.add_parser(
        "install", help="Lance install.sh dans le répertoire cible"
    )
    install_parser.add_argument(
        "path",
        nargs="?",
        default=None,
        metavar="PATH",
        help="Répertoire cible (défaut : répertoire courant)",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "validate": lambda: cmd_validate(),
        "check": lambda: cmd_check(),
        "gen": lambda: cmd_gen(),
        "bump": lambda: cmd_bump(args.level),
        "status": lambda: cmd_status(),
        "install": lambda: cmd_install(getattr(args, "path", None)),
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler())


if __name__ == "__main__":
    main()
