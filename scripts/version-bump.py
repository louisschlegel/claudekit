#!/usr/bin/env python3
"""
version-bump.py — Semantic version bumper for project and template.

Usage:
    python3 scripts/version-bump.py patch      # 1.2.3 → 1.2.4
    python3 scripts/version-bump.py minor      # 1.2.3 → 1.3.0
    python3 scripts/version-bump.py major      # 1.2.3 → 2.0.0
    python3 scripts/version-bump.py --template patch  # bump template version
    python3 scripts/version-bump.py --show     # show current version
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
MANIFEST = ROOT / "project.manifest.json"
TEMPLATE_VERSION = ROOT / ".template" / "version.json"


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse 'vX.Y.Z' or 'X.Y.Z' into (major, minor, patch)."""
    clean = version.lstrip("v")
    parts = clean.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semver: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_semver(major: int, minor: int, patch: int, prefix: str = "") -> str:
    return f"{prefix}{major}.{minor}.{patch}"


def bump_version(current: str, bump_type: str, prefix: str = "") -> str:
    major, minor, patch = parse_semver(current)
    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise ValueError(f"Unknown bump type: {bump_type}. Use: patch, minor, major")
    return format_semver(major, minor, patch, prefix)


def bump_manifest(bump_type: str) -> tuple[str, str]:
    """Bump version in project.manifest.json. Returns (old, new)."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"project.manifest.json not found at {MANIFEST}")

    data = json.loads(MANIFEST.read_text())

    if "project" not in data or "version" not in data.get("project", {}):
        raise ValueError("project.manifest.json must have 'project.version' field")

    old_version = data["project"]["version"]
    new_version = bump_version(old_version, bump_type)

    data["project"]["version"] = new_version
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n")

    return old_version, new_version


def bump_template(bump_type: str) -> tuple[str, str]:
    """Bump version in .template/version.json. Returns (old, new)."""
    TEMPLATE_VERSION.parent.mkdir(parents=True, exist_ok=True)

    if TEMPLATE_VERSION.exists():
        data = json.loads(TEMPLATE_VERSION.read_text())
    else:
        data = {
            "version": "0.1.0",
            "improvement_history": [],
        }

    old_version = data.get("version", "0.1.0")
    new_version = bump_version(old_version, bump_type)

    entry = {
        "from": old_version,
        "to": new_version,
        "date": datetime.now(timezone.utc).isoformat(),
        "type": bump_type,
    }

    data["version"] = new_version
    data.setdefault("improvement_history", []).append(entry)
    TEMPLATE_VERSION.write_text(json.dumps(data, indent=2) + "\n")

    return old_version, new_version


def bump_package_json(bump_type: str) -> tuple[str, str] | None:
    """Bump version in package.json if it exists."""
    pkg = ROOT / "package.json"
    if not pkg.exists():
        return None

    data = json.loads(pkg.read_text())
    old_version = data.get("version", "0.0.0")
    new_version = bump_version(old_version, bump_type)
    data["version"] = new_version

    pkg.write_text(json.dumps(data, indent=2) + "\n")
    return old_version, new_version


def bump_pyproject(bump_type: str) -> tuple[str, str] | None:
    """Bump version in pyproject.toml if it exists."""
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        return None

    content = pyproject.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        return None

    old_version = match.group(1)
    new_version = bump_version(old_version, bump_type)
    new_content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"', 1)
    pyproject.write_text(new_content)

    return old_version, new_version


def show_versions():
    """Show all current versions."""
    print("\n=== Current Versions ===")

    if MANIFEST.exists():
        data = json.loads(MANIFEST.read_text())
        v = data.get("project", {}).get("version", "not set")
        name = data.get("project", {}).get("name", "project")
        print(f"  {name} (manifest): {v}")

    if TEMPLATE_VERSION.exists():
        data = json.loads(TEMPLATE_VERSION.read_text())
        print(f"  template: {data.get('version', 'not set')}")

    pkg = ROOT / "package.json"
    if pkg.exists():
        data = json.loads(pkg.read_text())
        print(f"  package.json: {data.get('version', 'not set')}")

    pyproject = ROOT / "pyproject.toml"
    if pyproject.exists():
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(), re.MULTILINE)
        if match:
            print(f"  pyproject.toml: {match.group(1)}")


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    if "--show" in args:
        show_versions()
        sys.exit(0)

    is_template = "--template" in args
    args = [a for a in args if a != "--template"]

    if not args:
        print("ERROR: missing bump type (patch/minor/major)", file=sys.stderr)
        sys.exit(1)

    bump_type = args[0]
    if bump_type not in ("patch", "minor", "major"):
        print(f"ERROR: unknown bump type '{bump_type}'. Use: patch, minor, major", file=sys.stderr)
        sys.exit(1)

    if is_template:
        old, new = bump_template(bump_type)
        print(f"Template: {old} → {new}")
    else:
        bumped_any = False

        try:
            old, new = bump_manifest(bump_type)
            print(f"project.manifest.json: {old} → {new}")
            bumped_any = True
        except (FileNotFoundError, ValueError) as e:
            print(f"manifest: skipped ({e})")

        result = bump_package_json(bump_type)
        if result:
            old, new = result
            print(f"package.json: {old} → {new}")
            bumped_any = True

        result = bump_pyproject(bump_type)
        if result:
            old, new = result
            print(f"pyproject.toml: {old} → {new}")
            bumped_any = True

        if not bumped_any:
            print("No version files found to bump.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
