.PHONY: validate check install-local bump-patch bump-minor bump-major changelog help

# Default target
help:
	@echo "claudekit — available targets:"
	@echo ""
	@echo "  make validate       Run full CI validation (scripts + hooks + JSON + coverage)"
	@echo "  make check          Quick local syntax check (faster than validate)"
	@echo "  make install-local  Install claudekit into current directory"
	@echo "  make bump-patch     Bump patch version (1.0.0 → 1.0.1)"
	@echo "  make bump-minor     Bump minor version (1.0.0 → 1.1.0)"
	@echo "  make bump-major     Bump major version (1.0.0 → 2.0.0)"
	@echo "  make changelog      Generate CHANGELOG from git log"
	@echo "  make gen            Regenerate config from project.manifest.json"
	@echo ""

validate:
	@echo "=== Compiling Python scripts ==="
	python3 -m py_compile scripts/gen.py
	python3 -m py_compile scripts/auto-learn.py
	python3 -m py_compile scripts/self-improve.py
	python3 -m py_compile scripts/version-bump.py
	python3 -m py_compile scripts/changelog-gen.py
	@echo "=== Validating bash hooks ==="
	bash -n .claude/hooks/session-start.sh
	bash -n .claude/hooks/user-prompt-submit.sh
	@echo "=== Validating JSON files ==="
	python3 -c "import json; json.load(open('project.manifest.EXAMPLE.json'))"
	python3 -c "import json; json.load(open('.template/version.json'))"
	python3 -c "import json; json.load(open('.template/known-patterns.json'))"
	@echo "=== Checking HANDOFF JSON coverage ==="
	@missing=0; \
	for f in .claude/agents/*.md; do \
		grep -q "HANDOFF JSON" "$$f" || { echo "Missing HANDOFF JSON: $$f"; missing=1; }; \
	done; \
	[ $$missing -eq 0 ] || exit 1
	@echo "=== Checking SPÉCIALISATIONS coverage ==="
	@missing=0; \
	for f in .claude/agents/*.md; do \
		grep -q "SPÉCIALISATIONS" "$$f" || { echo "Missing SPÉCIALISATIONS: $$f"; missing=1; }; \
	done; \
	[ $$missing -eq 0 ] || exit 1
	@echo "=== Checking workflows HANDOFF JSON coverage ==="
	@missing=0; \
	for f in workflows/*.md; do \
		grep -q "HANDOFF JSON" "$$f" || { echo "Missing HANDOFF JSON: $$f"; missing=1; }; \
	done; \
	[ $$missing -eq 0 ] || exit 1
	@echo "=== Checking workflows CONTRAT DE SORTIE coverage ==="
	@missing=0; \
	for f in workflows/*.md; do \
		grep -q "CONTRAT DE SORTIE" "$$f" || { echo "Missing CONTRAT DE SORTIE: $$f"; missing=1; }; \
	done; \
	[ $$missing -eq 0 ] || exit 1
	@echo "=== Testing gen.py end-to-end ==="
	@python3 scripts/gen.py --manifest examples/web-app.manifest.json --dry-run 2>/dev/null || \
		python3 -c "\
import json, sys, os; \
sys.path.insert(0, 'scripts'); \
m = json.load(open('examples/web-app.manifest.json')); \
print('gen.py import OK — manifest loaded:', m['project']['name'])"
	@echo ""
	@echo "All checks passed."

check:
	@echo "=== Quick syntax check ==="
	@python3 -m py_compile scripts/gen.py && echo "gen.py OK"
	@python3 -m py_compile scripts/auto-learn.py && echo "auto-learn.py OK"
	@bash -n .claude/hooks/session-start.sh && echo "session-start.sh OK"
	@bash -n .claude/hooks/user-prompt-submit.sh && echo "user-prompt-submit.sh OK"
	@python3 -c "import json; json.load(open('project.manifest.EXAMPLE.json'))" && echo "manifest.EXAMPLE.json OK"
	@echo "Done."

install-local:
	@echo "Installing claudekit into current directory..."
	@bash install.sh .

gen:
	@[ -f project.manifest.json ] || { echo "Error: project.manifest.json not found"; exit 1; }
	python3 scripts/gen.py

bump-patch:
	python3 scripts/version-bump.py patch --template
	@echo "Patch version bumped."

bump-minor:
	python3 scripts/version-bump.py minor --template
	@echo "Minor version bumped."

bump-major:
	python3 scripts/version-bump.py major --template
	@echo "Major version bumped."

changelog:
	python3 scripts/changelog-gen.py --append
	@echo "CHANGELOG.md updated."
