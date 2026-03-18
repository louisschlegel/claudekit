"""Tests for scripts/gen.py — the core manifest-to-config generator."""

import json
import os
import subprocess
import importlib.util
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_gen():
    spec = importlib.util.spec_from_file_location("gen", os.path.join(ROOT, "scripts/gen.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def gen():
    return load_gen()


@pytest.fixture
def web_manifest():
    return json.load(open(os.path.join(ROOT, "examples/web-app.manifest.json")))


@pytest.fixture
def api_manifest():
    return json.load(open(os.path.join(ROOT, "examples/api.manifest.json")))


@pytest.fixture
def ml_manifest():
    return json.load(open(os.path.join(ROOT, "examples/ml.manifest.json")))


@pytest.fixture
def mobile_manifest():
    return json.load(open(os.path.join(ROOT, "examples/mobile.manifest.json")))


@pytest.fixture
def minimal_manifest():
    return {
        "project": {"name": "test", "description": "test", "type": "api", "language": "en"},
        "stack": {
            "languages": ["python"], "frameworks": [], "databases": [],
            "runtime": "python", "testing": ["pytest"], "linting": ["ruff"],
            "package_managers": ["pip"], "monorepo_tools": [], "data_tools": [],
            "serverless": [], "desktop_frameworks": []
        },
        "mcp_servers": [],
        "guards": {"lint": True, "type_check": False, "test_on_edit": False,
                   "migration_check": False, "i18n_check": False, "secret_scan": True}
    }


# ── build_permissions ──────────────────────────────────────────────────────────

class TestBuildPermissions:
    def test_not_empty(self, gen, web_manifest):
        assert len(gen.build_permissions(web_manifest)) > 0

    def test_returns_list_of_strings(self, gen, web_manifest):
        perms = gen.build_permissions(web_manifest)
        assert isinstance(perms, list)
        assert all(isinstance(p, str) for p in perms)

    def test_no_duplicates(self, gen, web_manifest):
        perms = gen.build_permissions(web_manifest)
        assert len(perms) == len(set(perms))

    def test_python_project_has_python_perms(self, gen, api_manifest):
        perms = " ".join(gen.build_permissions(api_manifest))
        assert "python3" in perms

    def test_typescript_project_has_node_perms(self, gen, web_manifest):
        perms = " ".join(gen.build_permissions(web_manifest))
        assert any(t in perms for t in ["npm", "node", "pnpm", "bun"])

    def test_ml_manifest_has_ml_tools(self, gen, ml_manifest):
        perms = " ".join(gen.build_permissions(ml_manifest))
        assert any(t in perms for t in ["mlflow", "dvc", "python3"])

    def test_always_includes_git(self, gen, minimal_manifest):
        perms = " ".join(gen.build_permissions(minimal_manifest))
        assert "git" in perms

    def test_always_includes_bash(self, gen, minimal_manifest):
        perms = gen.build_permissions(minimal_manifest)
        assert any("bash" in p.lower() or "Bash" in p for p in perms)


# ── build_hooks ────────────────────────────────────────────────────────────────
# build_hooks returns a dict: {event_name: [hook_config, ...], ...}

class TestBuildHooks:
    def test_returns_dict(self, gen, web_manifest):
        assert isinstance(gen.build_hooks(web_manifest), dict)

    def test_contains_user_prompt_submit(self, gen, web_manifest):
        assert "UserPromptSubmit" in gen.build_hooks(web_manifest)

    def test_contains_session_start(self, gen, web_manifest):
        assert "SessionStart" in gen.build_hooks(web_manifest)

    def test_hooks_have_command_field(self, gen, web_manifest):
        for event, configs in gen.build_hooks(web_manifest).items():
            for cfg in configs:
                assert "command" in cfg or "hooks" in cfg, f"No command in {event} hook"

    def test_hook_count_reasonable(self, gen, web_manifest):
        # Should have at least 2 events (SessionStart + UserPromptSubmit)
        assert len(gen.build_hooks(web_manifest)) >= 2


# ── make_session_start ─────────────────────────────────────────────────────────

class TestMakeSessionStart:
    def test_contains_project_name(self, gen, web_manifest):
        assert web_manifest["project"]["name"] in gen.make_session_start(web_manifest)

    def test_not_empty(self, gen, api_manifest):
        assert len(gen.make_session_start(api_manifest)) > 200

    def test_is_valid_bash(self, gen, web_manifest, tmp_path):
        content = gen.make_session_start(web_manifest)
        f = tmp_path / "hook.sh"
        f.write_text(content)
        result = subprocess.run(["bash", "-n", str(f)], capture_output=True)
        assert result.returncode == 0, f"Bash syntax error:\n{result.stderr.decode()}"

    def test_no_hardcoded_secrets(self, gen, web_manifest):
        content = gen.make_session_start(web_manifest).lower()
        forbidden = ["password =", "api_key =", "private_key =", "secret ="]
        for pat in forbidden:
            assert pat not in content, f"Potential secret pattern found: {pat}"

    def test_contains_shebang(self, gen, web_manifest):
        content = gen.make_session_start(web_manifest)
        assert content.startswith("#!/")


# ── make_user_prompt_submit ────────────────────────────────────────────────────

class TestMakeUserPromptSubmit:
    REQUIRED_INTENTS = [
        "feature", "bugfix", "hotfix", "release", "security-audit",
        "db-migration", "incident", "perf-test", "publish", "api-design",
        "refactor", "onboard",
    ]

    def test_contains_all_required_intents(self, gen, web_manifest):
        content = gen.make_user_prompt_submit(web_manifest)
        for intent in self.REQUIRED_INTENTS:
            assert intent in content, f"Intent '{intent}' missing"

    def test_contains_injection_detection(self, gen, web_manifest):
        content = gen.make_user_prompt_submit(web_manifest)
        assert "jailbreak" in content or "injection" in content.lower()

    def test_is_valid_bash(self, gen, web_manifest, tmp_path):
        content = gen.make_user_prompt_submit(web_manifest)
        f = tmp_path / "hook.sh"
        f.write_text(content)
        result = subprocess.run(["bash", "-n", str(f)], capture_output=True)
        assert result.returncode == 0, f"Bash syntax error:\n{result.stderr.decode()}"

    def test_contains_shebang(self, gen, web_manifest):
        content = gen.make_user_prompt_submit(web_manifest)
        assert content.startswith("#!/")


# ── build_mcp_servers ──────────────────────────────────────────────────────────
# build_mcp_servers returns a flat dict: {"github": {...}, "postgres": {...}, ...}

class TestBuildMcpServers:
    def test_returns_dict(self, gen, web_manifest):
        assert isinstance(gen.build_mcp_servers(web_manifest), dict)

    def test_github_server_present(self, gen, web_manifest):
        # web-app manifest has "github" in mcp_servers
        mcp = gen.build_mcp_servers(web_manifest)
        assert "github" in mcp

    def test_no_comment_fields_in_output(self, gen, web_manifest):
        mcp = gen.build_mcp_servers(web_manifest)
        for key in mcp:
            assert not key.startswith("_"), f"Comment key leaked: {key}"
        for server, cfg in mcp.items():
            if isinstance(cfg, dict):
                for k in cfg:
                    assert not k.startswith("_"), f"Comment key in {server}: {k}"

    def test_empty_mcp_list_returns_empty(self, gen):
        mcp = gen.build_mcp_servers({"mcp_servers": []})
        assert mcp == {}

    def test_unknown_server_is_skipped(self, gen):
        mcp = gen.build_mcp_servers({"mcp_servers": ["nonexistent-server-xyz"]})
        assert "nonexistent-server-xyz" not in mcp


# ── examples validation ────────────────────────────────────────────────────────

class TestExamples:
    EXAMPLES_DIR = os.path.join(ROOT, "examples")
    REQUIRED_SECTIONS = ["project", "stack", "workflow", "mcp_servers", "guards", "agents"]

    @pytest.mark.parametrize("filename", [
        "web-app.manifest.json",
        "api.manifest.json",
        "ml.manifest.json",
        "mobile.manifest.json",
    ])
    def test_example_is_valid_json(self, filename):
        path = os.path.join(self.EXAMPLES_DIR, filename)
        data = json.load(open(path))
        assert isinstance(data, dict)

    @pytest.mark.parametrize("filename", [
        "web-app.manifest.json",
        "api.manifest.json",
        "ml.manifest.json",
        "mobile.manifest.json",
    ])
    def test_example_has_required_sections(self, filename):
        path = os.path.join(self.EXAMPLES_DIR, filename)
        data = json.load(open(path))
        for section in self.REQUIRED_SECTIONS:
            assert section in data, f"{filename} missing section: {section}"

    @pytest.mark.parametrize("filename", [
        "web-app.manifest.json",
        "api.manifest.json",
        "ml.manifest.json",
        "mobile.manifest.json",
    ])
    def test_example_can_generate_permissions(self, gen, filename):
        path = os.path.join(self.EXAMPLES_DIR, filename)
        manifest = json.load(open(path))
        perms = gen.build_permissions(manifest)
        assert len(perms) > 0

    @pytest.mark.parametrize("filename", [
        "web-app.manifest.json",
        "api.manifest.json",
        "ml.manifest.json",
        "mobile.manifest.json",
    ])
    def test_example_generates_valid_bash_hooks(self, gen, filename, tmp_path):
        path = os.path.join(self.EXAMPLES_DIR, filename)
        manifest = json.load(open(path))

        session = gen.make_session_start(manifest)
        f = tmp_path / "session.sh"
        f.write_text(session)
        result = subprocess.run(["bash", "-n", str(f)], capture_output=True)
        assert result.returncode == 0, f"Invalid bash in session-start for {filename}"

        ups = gen.make_user_prompt_submit(manifest)
        f2 = tmp_path / "ups.sh"
        f2.write_text(ups)
        result2 = subprocess.run(["bash", "-n", str(f2)], capture_output=True)
        assert result2.returncode == 0, f"Invalid bash in user-prompt-submit for {filename}"
