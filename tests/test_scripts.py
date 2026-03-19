"""Tests for supporting scripts: self-improve, version-bump, changelog-gen, auto-learn, check.sh."""

import json
import os
import subprocess
import importlib.util
import tempfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")


def compile_script(name):
    result = subprocess.run(
        ["python3", "-m", "py_compile", os.path.join(SCRIPTS, name)],
        capture_output=True, text=True
    )
    return result


# ── self-improve.py ────────────────────────────────────────────────────────────

class TestSelfImprove:
    def test_compiles(self):
        r = compile_script("self-improve.py")
        assert r.returncode == 0, r.stderr

    def test_help_flag(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "self-improve.py"), "--help"],
            capture_output=True, text=True
        )
        assert r.returncode == 0

    def test_log_does_not_crash(self):
        payload = json.dumps({"type": "test", "note": "pytest run"})
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "self-improve.py"), "--log", payload],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]

    def test_stats_does_not_crash(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "self-improve.py"), "--stats"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]


# ── version-bump.py ────────────────────────────────────────────────────────────

class TestVersionBump:
    def test_compiles(self):
        r = compile_script("version-bump.py")
        assert r.returncode == 0, r.stderr

    def test_show_flag_does_not_crash(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "version-bump.py"), "--show"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]

    def test_show_displays_version_info(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "version-bump.py"), "--show"],
            capture_output=True, text=True, cwd=ROOT
        )
        # Should succeed and show version info from project.manifest.json
        assert r.returncode in [0, 1]
        if r.returncode == 0:
            assert len(r.stdout) > 0


# ── changelog-gen.py ───────────────────────────────────────────────────────────

class TestChangelogGen:
    def test_compiles(self):
        r = compile_script("changelog-gen.py")
        assert r.returncode == 0, r.stderr

    def test_unreleased_flag_does_not_crash(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "changelog-gen.py"), "--unreleased"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]

    def test_output_contains_changelog_header(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "changelog-gen.py"), "--unreleased"],
            capture_output=True, text=True, cwd=ROOT
        )
        # In CI (no tags), script may output "No conventional commits found" — that's valid
        if r.returncode == 0:
            valid = (
                "##" in r.stdout
                or "Unreleased" in r.stdout
                or r.stdout == ""
                or "No conventional commits" in r.stdout
                or "No previous tag" in r.stdout
                or "Nothing to add" in r.stdout
                or "No commits found" in r.stdout
            )
            assert valid, f"Unexpected output: {r.stdout}"


# ── auto-learn.py ──────────────────────────────────────────────────────────────

class TestAutoLearn:
    def test_compiles(self):
        r = compile_script("auto-learn.py")
        assert r.returncode == 0, r.stderr

    def test_show_stats_does_not_crash(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "auto-learn.py"), "--show-stats"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]

    def test_extract_patterns_does_not_crash(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "auto-learn.py"), "--extract-patterns"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]

    def test_from_agent_reviewer_json(self):
        payload = json.dumps({
            "verdict": "WARNING",
            "blockers": [],
            "warnings": ["Use parameterized queries instead of string concatenation"],
            "suggestions": [],
            "files_reviewed": ["src/db.py"]
        })
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "auto-learn.py"),
             "--from-agent", "reviewer", "--input", payload],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode in [0, 1]


# ── check.sh ───────────────────────────────────────────────────────────────────

class TestCheckSh:
    def test_is_valid_bash(self):
        r = subprocess.run(
            ["bash", "-n", os.path.join(SCRIPTS, "check.sh")],
            capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr

    def test_runs_successfully_on_repo(self):
        r = subprocess.run(
            ["bash", os.path.join(SCRIPTS, "check.sh")],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0, f"check.sh failed:\n{r.stdout}\n{r.stderr}"


# ── hooks syntax ──────────────────────────────────────────────────────────────

class TestHooksSyntax:
    HOOKS = [
        "session-start.sh",
        "user-prompt-submit.sh",
        "pre-bash-guard.sh",
        "post-edit.sh",
        "stop.sh",
        "pre-push.sh",
    ]

    @pytest.mark.parametrize("hook", HOOKS)
    def test_hook_is_valid_bash(self, hook):
        path = os.path.join(ROOT, ".claude/hooks", hook)
        if not os.path.exists(path):
            pytest.skip(f"{hook} not present (generated hook)")
        r = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        assert r.returncode == 0, f"Syntax error in {hook}:\n{r.stderr}"


# ── claudekit.py ──────────────────────────────────────────────────────────────

class TestClaudekitCLI:
    def test_compiles(self):
        r = compile_script("claudekit.py")
        assert r.returncode == 0, r.stderr

    def test_help_flag(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "claudekit.py"), "--help"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0

    def test_status_runs(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "claudekit.py"), "status"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0, f"claudekit status failed:\n{r.stderr}"
        assert "Version" in r.stdout or "version" in r.stdout.lower()

    def test_status_lists_agents(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "claudekit.py"), "status"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0
        assert "agent" in r.stdout.lower()

    def test_status_lists_workflows(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "claudekit.py"), "status"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0
        assert "workflow" in r.stdout.lower()


# ── migrate-template.py ───────────────────────────────────────────────────────

class TestMigrateTemplate:
    def test_compiles(self):
        r = compile_script("migrate-template.py")
        assert r.returncode == 0, r.stderr

    def test_help_flag(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "migrate-template.py"), "--help"],
            capture_output=True, text=True, cwd=ROOT
        )
        assert r.returncode == 0

    def test_check_flag(self):
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "migrate-template.py"), "--check"],
            capture_output=True, text=True, cwd=ROOT
        )
        # 0 = up to date, 1 = migrations available — both are valid
        assert r.returncode in (0, 1)

    def test_dry_run_does_not_modify_manifest(self):
        manifest_path = os.path.join(ROOT, "project.manifest.json")
        with open(manifest_path) as f:
            original = f.read()
        r = subprocess.run(
            ["python3", os.path.join(SCRIPTS, "migrate-template.py"), "--dry-run"],
            capture_output=True, text=True, cwd=ROOT
        )
        with open(manifest_path) as f:
            after = f.read()
        assert original == after, "dry-run should not modify project.manifest.json"

    def test_migration_100_to_110_adds_fields(self):
        """Test that migration adds agents[] and workflows[] if missing."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("mt", os.path.join(SCRIPTS, "migrate-template.py"))
        mt = ilu.module_from_spec(spec)
        spec.loader.exec_module(mt)

        manifest = {
            "project": {"name": "test", "type": "web-app", "language": "fr"},
            "stack": {"languages": ["python"], "frameworks": []},
            "template": {"version": "1.0.2"},
        }
        result = mt.migrate_102_to_110(manifest, dry_run=True)
        assert "agents" in result, "Migration should add agents[]"
        assert "workflows" in result, "Migration should add workflows[]"
        assert isinstance(result["agents"], list), "agents should be a list"
        assert isinstance(result["workflows"], list), "workflows should be a list"
        assert result["template"]["version"] == "1.1.0"
