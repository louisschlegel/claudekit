# Workflow: Publish Package

## DÉCLENCHEUR
Intent classifié comme `publish` par le hook UserPromptSubmit.
Commande directe : "publie le package", "publish to PyPI", "npm publish", "release library", "publie sur npm/PyPI/crates.io".

**Note :** Ce workflow publie une LIBRAIRIE sur un registry public. Pour déployer une application, voir `workflows/release.md`.

## AGENTS IMPLIQUÉS
1. **Security Auditor** — vérification des secrets et dépendances avant publication
2. **Reviewer** — validation du contenu du package et de l'API publique
3. **Release Manager** — bump de version, changelog, tag git

---

## ÉTAPE 1 — Vérifications pré-publication

### 1.1 — Vérifier les dépendances

```bash
# Python — vérifier que les dev deps ne sont pas dans install_requires
python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
deps = data.get('project', {}).get('dependencies', [])
dev_deps = data.get('project', {}).get('optional-dependencies', {}).get('dev', [])
print('Production deps:', deps)
print('Dev deps:', dev_deps)
"

# Node — vérifier que les dev deps ne sont pas dans dependencies
node -e "
const pkg = require('./package.json');
const deps = Object.keys(pkg.dependencies || {});
const devDeps = Object.keys(pkg.devDependencies || {});
const overlap = deps.filter(d => devDeps.includes(d));
if (overlap.length) console.error('PROBLÈME: deps en double:', overlap);
else console.log('OK: pas de chevauchement deps/devDeps');
"
```

### 1.2 — Vérifier qu'aucun fichier sensible ne sera publié

```bash
# Python — vérifier ce qui sera inclus dans le package
python -m build --sdist
tar -tzf dist/*.tar.gz | grep -E "\.(env|key|pem|secret|token|credential)" && echo "DANGER: fichiers sensibles détectés !" || echo "OK: pas de fichiers sensibles"

# Node — vérifier le contenu du package
npm pack --dry-run 2>&1 | grep -v "^npm notice"

# Rust
cargo package --list | grep -E "\.(env|key|pem|secret|token|credential)" && echo "DANGER !" || echo "OK"

# Ruby
gem build *.gemspec && gem contents *.gem | grep -E "\.(env|key|pem|secret|token|credential)" && echo "DANGER !" || echo "OK"
```

Vérifier aussi la présence d'un `.npmignore` / `MANIFEST.in` / `.cargo/package.include` correctement configuré.

### 1.3 — Gate : Security Audit

Invoquer `security-auditor` avec :
```
Scope : package complet
Focus : secrets hardcodés, dépendances avec CVE connues, fichiers sensibles dans le bundle
```

Gate : `RELEASE_GATE: PASS` requis pour continuer.

### 1.4 — Vérifier le README et le changelog

Checklist :
- [ ] README.md reflète la version actuelle (API, exemples, installation)
- [ ] CHANGELOG.md contient l'entrée pour la version à publier
- [ ] La version dans le fichier de config correspond à celle attendue
- [ ] Les breaking changes sont clairement documentés (si applicable)
- [ ] La version minimum de Python/Node/Rust/Ruby supportée est à jour

### 1.5 — Vérifier les tests sur la version minimum supportée

```bash
# Python — tester sur la version minimum supportée
# (utiliser tox ou GitHub Actions matrix)
tox -e py39  # si Python 3.9 est le minimum

# Node — tester sur Node minimum supporté
nvm use 18  # si Node 18 est le minimum
npm test

# Rust — tester sur la MSRV (Minimum Supported Rust Version)
rustup override set 1.70.0  # si 1.70 est la MSRV
cargo test
rustup override unset
```

---

## ÉTAPE 2 — Préparer la release

Invoquer `release-manager` avec :
```
Type : patch/minor/major
Commits : [git log depuis dernier tag]
Ecosystem : python/node/rust/ruby
```

Le release-manager :
- Bumpe la version dans le fichier approprié
- Génère l'entrée CHANGELOG.md
- Crée le commit de release
- Crée le tag git signé

```bash
# Python — bumper la version dans pyproject.toml / setup.cfg
# Node — bumper dans package.json
npm version patch  # ou minor / major

# Rust — bumper dans Cargo.toml
cargo set-version 1.2.3  # cargo-edit requis

# Ruby — bumper dans lib/[gem]/version.rb
sed -i 's/VERSION = ".*"/VERSION = "1.2.3"/' lib/[gem]/version.rb
```

---

## ÉTAPE 3 — Build et inspection du package

### Python

```bash
# Installer les outils de build
pip install build twine

# Builder le package (sdist + wheel)
python -m build

# Vérifier la structure et les métadonnées
twine check dist/*

# Inspecter le contenu
tar -tzf dist/*.tar.gz
unzip -l dist/*.whl
```

### Node / npm

```bash
# Vérifier le contenu avant publication
npm pack
tar -tzf $(ls *.tgz | head -1)

# Vérifier les métadonnées
node -e "
const pkg = require('./package.json');
['name','version','description','main','license','repository'].forEach(k => {
  console.log(k+':', pkg[k] || 'MANQUANT');
});
"

# Nettoyer
rm *.tgz
```

### Rust

```bash
# Vérifier le package
cargo package --list

# Vérifier que le package compile depuis le registry (simulé)
cargo package
cargo build --manifest-path target/package/[nom]-[version]/Cargo.toml
```

### Ruby

```bash
# Builder le gem
gem build [nom].gemspec

# Inspecter le contenu
gem contents [nom]-[version].gem

# Vérifier les métadonnées
gem specification [nom]-[version].gem
```

---

## ÉTAPE 4 — Publication sur le registry de test

**Toujours tester sur le registry de staging avant la production.**

### Python → TestPyPI

```bash
# Uploader sur TestPyPI
twine upload --repository testpypi dist/*

# URL de la publication test
echo "Vérifier : https://test.pypi.org/project/[nom]/"
```

### Node → npm (dry-run)

```bash
# Dry-run : simule la publication sans uploader
npm publish --dry-run

# Optionnel : publier sur un registry privé de test
npm publish --registry http://localhost:4873  # Verdaccio local
```

### Rust → crates.io (dry-run)

```bash
cargo publish --dry-run
```

### Ruby → gem (staging)

```bash
# Tester l'installation depuis le fichier local
gem install [nom]-[version].gem
ruby -e "require '[nom]'; puts [Module]::VERSION"
gem uninstall [nom]
```

---

## ÉTAPE 5 — Vérification d'installation depuis le registry de test

```bash
# Python — vérifier l'installation depuis TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  [nom]==[version]
python -c "import [nom]; print([nom].__version__)"

# Node — vérifier l'installation depuis le tarball
npm install ./[nom]-[version].tgz
node -e "const pkg = require('[nom]'); console.log('OK:', pkg.version || 'importé');"

# Rust — vérifier le build depuis le dry-run package
# (déjà testé en étape 3)
```

Gate :
- Installation sans erreur → continuer
- Erreur d'installation → **STOP**. Corriger le package avant de continuer.

---

## ÉTAPE 6 — Publication en production

**Requiert une confirmation explicite de l'utilisateur.**

```
Prêt à publier [nom] v[version] sur [PyPI/npm/crates.io/RubyGems].
Cette action est IRRÉVERSIBLE (la version publiée ne peut pas être supprimée, seulement dépréciée).
Confirmer ? [oui/non]
```

### Python → PyPI

```bash
twine upload dist/*
# ou avec 2FA via token
twine upload --username __token__ --password pypi-[TOKEN] dist/*
```

### Node → npm

```bash
# S'assurer d'être connecté
npm whoami

# Publier (public par défaut pour les scoped packages)
npm publish
# ou pour un package scoped privé devenu public :
npm publish --access public
```

### Rust → crates.io

```bash
cargo publish
```

### Ruby → RubyGems

```bash
gem push [nom]-[version].gem
```

---

## ÉTAPE 7 — Vérification post-publication

```bash
# Python
pip index versions [nom]  # ou vérifier PyPI
pip install [nom]==[version]
python -c "import [nom]; print([nom].__version__)"

# Node
npm view [nom]@[version]
npm install [nom]@[version]

# Rust
cargo search [nom]
# (peut prendre quelques minutes pour apparaître)

# Ruby
gem list --remote [nom]
gem install [nom] -v [version]
```

Vérifier aussi :
- [ ] La documentation générée est à jour (Read the Docs, docs.rs, etc.)
- [ ] Le badge de version sur le README est correct (si applicable)

---

## ÉTAPE 8 — Annonces et post-publication

```bash
# Créer la GitHub Release
gh release create v[version] \
  --title "[nom] v[version]" \
  --notes-file CHANGELOG_ENTRY.md \
  dist/*  # attacher les artifacts si pertinent

# Push le tag
git push origin v[version]
git push origin main
```

Si la librairie a une communauté active :
- Poster dans le Discord/Slack du projet
- Tweeter / post Mastodon (si applicable)
- Mettre à jour les templates d'exemple dans la documentation

---

## CONTRAT DE SORTIE

```
PACKAGE: [nom]
VERSION: [version]
ECOSYSTEM: python/node/rust/ruby
REGISTRY: PyPI / npm / crates.io / RubyGems

GATES:
  Security audit: PASS
  Dev deps in prod deps: none
  Sensitive files in bundle: none
  README current: yes
  Changelog complete: yes
  Tests on min supported version: PASS
  Dry-run / test registry: OK
  Install from test registry: OK

BUILD:
  Artifacts: [liste des fichiers dist/]
  Size: [N KB]

PUBLICATION:
  Registry URL: [lien vers la page du package]
  Install command: pip install [nom]==[version] / npm install [nom]@[version] / etc.

POST-PUBLICATION:
  GitHub Release: [url]
  Documentation: updated / not applicable
  Announcement: sent / not applicable

TAG: v[version] created and pushed
```
