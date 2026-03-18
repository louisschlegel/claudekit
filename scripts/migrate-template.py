#!/usr/bin/env python3
"""
migrate-template.py — Migration automatique d'une version du template à une autre

Usage:
    python3 scripts/migrate-template.py                  # Détecte et applique les migrations
    python3 scripts/migrate-template.py --check          # Vérifie si des migrations sont disponibles
    python3 scripts/migrate-template.py --dry-run        # Simule sans écrire
    python3 scripts/migrate-template.py --from 1.0.0     # Force la version de départ
    python3 scripts/migrate-template.py --to 1.1.0       # Force la version cible

Migrations disponibles :
    1.0.0 → 1.0.1 : patch (aucune migration manuelle requise)
    1.0.x → 1.1.0 : nouveau champ agents[], workflows[] dans le manifest
    1.1.0 → 1.2.0 : (futur)
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
VERSION_FILE = ROOT / ".template" / "version.json"
MANIFEST_FILE = ROOT / "project.manifest.json"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)

def write_json(path: Path, data: dict, dry_run: bool = False) -> None:
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry_run:
        print(f"  [dry-run] Would write: {path.relative_to(ROOT)}")
        print(f"  {content[:200]}...")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"  ✅ Written: {path.relative_to(ROOT)}")

def backup_file(path: Path) -> Path:
    """Crée une sauvegarde avant modification."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(f".{ts}.bak")
    shutil.copy2(path, backup)
    print(f"  📦 Backup: {backup.relative_to(ROOT)}")
    return backup

def parse_version(v: str) -> tuple[int, int, int]:
    parts = v.lstrip("v").split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))

def version_gte(v1: str, v2: str) -> bool:
    return parse_version(v1) >= parse_version(v2)

def version_lt(v1: str, v2: str) -> bool:
    return parse_version(v1) < parse_version(v2)


# ─── Migrations ──────────────────────────────────────────────────────────────

MIGRATIONS: list[dict] = []

def migration(from_version: str, to_version: str, description: str):
    """Décorateur pour enregistrer une migration."""
    def decorator(fn):
        MIGRATIONS.append({
            "from": from_version,
            "to": to_version,
            "description": description,
            "fn": fn,
        })
        return fn
    return decorator


@migration("1.0.0", "1.0.1", "No manifest changes required")
def migrate_100_to_101(manifest: dict, dry_run: bool) -> dict:
    """1.0.0 → 1.0.1 : patch, aucune modification du manifest."""
    print("  ℹ️  Patch release — no manifest changes needed.")
    return manifest


@migration("1.0.1", "1.0.2", "No manifest changes required")
def migrate_101_to_102(manifest: dict, dry_run: bool) -> dict:
    """1.0.1 → 1.0.2 : patch."""
    print("  ℹ️  Patch release — no manifest changes needed.")
    return manifest


@migration("1.0.2", "1.1.0", "Add agents[], workflows[], spec-to-project, cost-analyst fields")
def migrate_102_to_110(manifest: dict, dry_run: bool) -> dict:
    """
    1.0.x → 1.1.0 : Ajout des champs agents[] et workflows[] dans le manifest.
    Si absents, on les génère depuis le type de projet.
    """
    project_type = manifest.get("project", {}).get("type", "web-app")

    # Agents par défaut selon le type
    DEFAULT_AGENTS_BY_TYPE = {
        "web-app": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                    "deployer", "explorer", "doc-writer", "performance-analyst", "release-manager",
                    "devops-engineer", "cost-analyst", "template-improver"],
        "api": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                "deployer", "explorer", "doc-writer", "performance-analyst", "release-manager",
                "devops-engineer", "cost-analyst", "template-improver"],
        "mobile": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                   "explorer", "doc-writer", "release-manager", "template-improver"],
        "library": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                    "explorer", "doc-writer", "release-manager", "template-improver"],
        "data-pipeline": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                          "explorer", "doc-writer", "data-engineer", "devops-engineer",
                          "cost-analyst", "template-improver"],
        "ml": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
               "explorer", "doc-writer", "data-engineer", "ml-engineer", "devops-engineer",
               "cost-analyst", "template-improver"],
        "iac": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                "explorer", "doc-writer", "devops-engineer", "cost-analyst", "release-manager",
                "template-improver"],
        "cli": ["architect", "reviewer", "tester", "security-auditor", "debug-detective",
                "explorer", "doc-writer", "release-manager", "template-improver"],
    }

    DEFAULT_WORKFLOWS = [
        "feature", "bugfix", "hotfix", "release", "security-audit",
        "dependency-update", "dependency-audit", "refactor", "onboard", "self-improve"
    ]

    EXTRA_WORKFLOWS_BY_TYPE = {
        "web-app": ["db-migration", "incident-response", "api-design", "monitoring-setup", "cost-optimization"],
        "api": ["db-migration", "incident-response", "api-design", "performance-baseline", "monitoring-setup"],
        "data-pipeline": ["db-migration", "data-quality", "incident-response", "monitoring-setup", "cost-optimization"],
        "ml": ["llm-eval", "data-quality", "performance-baseline", "monitoring-setup", "cost-optimization"],
        "iac": ["incident-response", "monitoring-setup", "cost-optimization"],
        "library": ["publish-package"],
        "cli": ["publish-package"],
    }

    changed = False

    # Ajouter agents[] si absent
    if "agents" not in manifest:
        manifest["agents"] = DEFAULT_AGENTS_BY_TYPE.get(
            project_type,
            DEFAULT_AGENTS_BY_TYPE["web-app"]
        )
        # Ajouter spec-reader si pas déjà présent
        if "spec-reader" not in manifest["agents"]:
            manifest["agents"].append("spec-reader")
        print(f"  ✅ Added 'agents' field ({len(manifest['agents'])} agents)")
        changed = True
    else:
        # Ajouter les nouveaux agents de v1.1.0 s'ils manquent
        new_agents_v110 = ["cost-analyst", "spec-reader"]
        for agent in new_agents_v110:
            if agent not in manifest["agents"]:
                manifest["agents"].append(agent)
                print(f"  ✅ Added new agent: {agent}")
                changed = True

    # Ajouter workflows[] si absent
    if "workflows" not in manifest:
        workflows = DEFAULT_WORKFLOWS + EXTRA_WORKFLOWS_BY_TYPE.get(project_type, [])
        manifest["workflows"] = list(dict.fromkeys(workflows))  # dedup
        print(f"  ✅ Added 'workflows' field ({len(manifest['workflows'])} workflows)")
        changed = True
    else:
        # Ajouter les nouveaux workflows de v1.1.0 s'ils manquent
        new_workflows_v110 = ["a-b-test", "data-quality", "llm-eval", "spec-to-project",
                               "dependency-audit", "monitoring-setup", "cost-optimization",
                               "code-review"]
        type_relevant = {
            "a-b-test": ["web-app", "api", "ml"],
            "data-quality": ["data-pipeline", "ml"],
            "llm-eval": ["ml", "api"],
            "monitoring-setup": ["web-app", "api", "data-pipeline", "ml", "iac"],
            "cost-optimization": ["web-app", "api", "iac", "data-pipeline", "ml"],
            "code-review": None,  # tous les types
            "dependency-audit": None,
            "spec-to-project": None,
        }
        for wf in new_workflows_v110:
            relevant_types = type_relevant.get(wf)
            if wf not in manifest["workflows"]:
                if relevant_types is None or project_type in relevant_types:
                    manifest["workflows"].append(wf)
                    print(f"  ✅ Added new workflow: {wf}")
                    changed = True

    # Mettre à jour template.version
    if "template" not in manifest:
        manifest["template"] = {}
    if manifest["template"].get("version") != "1.1.0":
        manifest["template"]["version"] = "1.1.0"
        manifest["template"]["source"] = "https://github.com/louisschlegel/claudekit"
        print(f"  ✅ Updated template.version to 1.1.0")
        changed = True

    # Ajouter security.owasp_check si absent
    if "security" in manifest and "owasp_check" not in manifest["security"]:
        manifest["security"]["owasp_check"] = False
        changed = True

    if not changed:
        print("  ℹ️  Manifest already up to date for 1.1.0")

    return manifest


# ─── Orchestrateur ───────────────────────────────────────────────────────────

def get_current_version() -> str:
    version_data = load_json(VERSION_FILE)
    return version_data.get("version", "1.0.0")

def get_applicable_migrations(from_v: str, to_v: str) -> list[dict]:
    """Retourne les migrations à appliquer dans l'ordre."""
    applicable = []
    current = from_v
    for m in sorted(MIGRATIONS, key=lambda x: parse_version(x["from"])):
        if version_gte(current, m["from"]) and version_lt(current, m["to"]) and version_lt(current, to_v):
            applicable.append(m)
            current = m["to"]
    return applicable

def run_migrations(from_v: str, to_v: str, dry_run: bool = False) -> bool:
    """Applique toutes les migrations nécessaires."""
    migrations = get_applicable_migrations(from_v, to_v)

    if not migrations:
        print(f"✅ Manifest already up to date ({from_v} → {to_v})")
        return True

    print(f"\n🔄 Applying {len(migrations)} migration(s): {from_v} → {to_v}\n")

    manifest = load_json(MANIFEST_FILE)
    if not manifest:
        print("❌ project.manifest.json not found or empty. Run setup first.")
        return False

    for m in migrations:
        print(f"📦 Migration {m['from']} → {m['to']}: {m['description']}")
        if not dry_run:
            backup_file(MANIFEST_FILE)
        manifest = m["fn"](manifest, dry_run)
        print()

    write_json(MANIFEST_FILE, manifest, dry_run)

    if not dry_run:
        # Mettre à jour version.json
        version_data = load_json(VERSION_FILE)
        version_data["version"] = to_v
        if "improvement_history" not in version_data:
            version_data["improvement_history"] = []
        version_data["improvement_history"].append({
            "from": from_v,
            "to": to_v,
            "date": datetime.utcnow().isoformat() + "Z",
            "type": "migration",
            "summary": f"Auto-migrated by migrate-template.py"
        })
        write_json(VERSION_FILE, version_data)

    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Migrate claudekit template to a newer version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--check", action="store_true",
                        help="Check if migrations are available without applying")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate migrations without writing files")
    parser.add_argument("--from", dest="from_version", default=None,
                        help="Override current version (default: read from version.json)")
    parser.add_argument("--to", dest="to_version", default=None,
                        help="Override target version (default: latest available)")
    args = parser.parse_args()

    # Déterminer les versions
    current_v = args.from_version or get_current_version()
    latest_v = sorted(
        [m["to"] for m in MIGRATIONS],
        key=parse_version
    )[-1] if MIGRATIONS else current_v
    target_v = args.to_version or latest_v

    print(f"claudekit migrate-template")
    print(f"  Current version : {current_v}")
    print(f"  Target version  : {target_v}")

    if args.check:
        migrations = get_applicable_migrations(current_v, target_v)
        if not migrations:
            print(f"\n✅ Already up to date ({current_v})")
            sys.exit(0)
        else:
            print(f"\n⬆️  {len(migrations)} migration(s) available:")
            for m in migrations:
                print(f"   {m['from']} → {m['to']}: {m['description']}")
            sys.exit(1)  # exit 1 = migrations available (utile pour CI)

    if args.dry_run:
        print("  Mode: DRY-RUN (no files written)\n")

    success = run_migrations(current_v, target_v, dry_run=args.dry_run)

    if success and not args.dry_run:
        print(f"\n✅ Migration complete. Now at {target_v}.")
        print("   Run `python3 scripts/gen.py` to regenerate hooks and settings.")
    elif success and args.dry_run:
        print(f"\n✅ Dry-run complete. No files written.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
