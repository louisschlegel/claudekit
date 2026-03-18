# Workflow: DB Migration

## DÉCLENCHEUR
Intent classifié comme `db-migration` par le hook UserPromptSubmit.
Commande directe : "migration DB", "ajoute une migration", "modifie le schéma", "alter table", "nouvelle colonne", "supprime une colonne".

## AGENTS IMPLIQUÉS
1. **Reviewer** — analyse du changement de schéma, classification du risque
2. **Tester** — tests sur snapshot de données réelles
3. **Deployer** — déploiement atomique migration + code

---

## ÉTAPE 1 — Analyser le changement de schéma

Identifier le type exact de modification :

| Type | Risque | Stratégie |
|------|--------|-----------|
| Ajout colonne nullable | Faible | Déploiement direct |
| Ajout colonne NOT NULL sans default | Élevé | Migration en 3 phases |
| Ajout colonne NOT NULL avec default | Moyen | Migration + backfill |
| Suppression colonne | Élevé | Code-first, migration ensuite |
| Rename colonne/table | Élevé | Double colonne + migration data |
| Ajout index | Moyen | `CREATE INDEX CONCURRENTLY` |
| Ajout contrainte FK | Élevé | Vérifier orphelins avant |
| Modification de type | Très élevé | Migration en 3 phases |

Poser les questions si la réponse n'est pas claire :
- La table a combien de lignes en production ?
- Y a-t-il des requêtes longues habituellement sur cette table ?
- Le déploiement peut-il avoir une fenêtre de maintenance ?

---

## ÉTAPE 2 — Créer la migration

Nommer le fichier avec un nom descriptif (PAS un nom auto-généré) :

```bash
# Python / Alembic
alembic revision --autogenerate -m "add_user_profile_picture_url"

# Django
python manage.py makemigrations --name "add_user_profile_picture_url"

# Rails
rails generate migration AddProfilePictureUrlToUsers profile_picture_url:string

# Node / Knex
knex migrate:make add_user_profile_picture_url

# Node / Prisma
# Éditer le schema.prisma puis :
npx prisma migrate dev --name add_user_profile_picture_url
```

Vérifier que le fichier généré contient bien :
- La fonction `up()` / `upgrade()`
- La fonction `down()` / `downgrade()` — **obligatoire**
- Le nom descriptif reflète le changement réel

---

## ÉTAPE 3 — Gate : Vérification de réversibilité

Invoquer `reviewer` avec :
```
Scope : fichier de migration créé
Focus : down() / downgrade() est-il correct ? La migration est-elle réversible sans perte de données ?
```

Gate :
- `down()` / `downgrade()` présent et correct → continuer
- `down()` absent ou vide → **STOP**. Implémenter le rollback avant de continuer.
- Rollback impossible (perte de données) → documenter explicitement et demander confirmation utilisateur.

---

## ÉTAPE 4 — Stratégie selon le type de migration

### Cas A — Ajout colonne nullable (safe, déploiement direct)
```sql
ALTER TABLE users ADD COLUMN profile_picture_url VARCHAR(500);
-- Pas de DEFAULT, pas de NOT NULL → pas de lock table long
```
Déploiement : migration puis code, ou simultané.

### Cas B — Ajout colonne NOT NULL (migration en 3 phases)
```sql
-- Phase 1 : ajouter nullable (déployer avec code qui n'écrit pas encore)
ALTER TABLE users ADD COLUMN status VARCHAR(20);

-- Phase 2 : backfill (hors migration, en script séparé ou job)
UPDATE users SET status = 'active' WHERE status IS NULL;

-- Phase 3 : ajouter la contrainte NOT NULL (déployer séparément)
ALTER TABLE users ALTER COLUMN status SET NOT NULL;
```
Chaque phase est un déploiement séparé. Ne jamais fusionner les 3 phases.

### Cas C — Suppression de colonne (code-first)
```
1. Déployer le code sans références à la colonne (ORM, requêtes, sérialiseurs)
2. Vérifier en production que la colonne n'est plus accédée (logs, monitoring)
3. ENSUITE seulement : déployer la migration de suppression
```
Ne jamais supprimer une colonne et le code qui la référence dans le même déploiement.

### Cas D — Rename colonne (double colonne)
```sql
-- Jamais : ALTER TABLE users RENAME COLUMN name TO full_name;

-- Phase 1 : créer la nouvelle colonne
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Phase 2 : migrer les données + synchroniser les deux colonnes via trigger ou code
UPDATE users SET full_name = name;

-- Phase 3 : déployer le code qui utilise full_name
-- Phase 4 : supprimer l'ancienne colonne (voir Cas C)
```

### Cas E — Ajout index sur grande table
```sql
-- PostgreSQL — sans lock table
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- MySQL — sans lock (MySQL 5.6+)
ALTER TABLE users ADD INDEX idx_email (email), ALGORITHM=INPLACE, LOCK=NONE;
```
Ne jamais utiliser `CREATE INDEX` sans `CONCURRENTLY` sur une table de production active.

---

## ÉTAPE 5 — Estimer le temps d'exécution et le risque de lock

```bash
# Vérifier la taille de la table avant la migration
# PostgreSQL
psql -c "SELECT pg_size_pretty(pg_total_relation_size('users')), COUNT(*) FROM users;"

# MySQL
mysql -e "SELECT table_rows, data_length FROM information_schema.tables WHERE table_name='users';"
```

Règles d'estimation :
- < 100k lignes → migration rapide, risque faible
- 100k–1M lignes → tester sur dump prod, prévoir 30s–5min
- > 1M lignes → **STOP**. Planifier une fenêtre de maintenance ou utiliser `pt-online-schema-change` / `gh-ost`.

---

## ÉTAPE 6 — Tester sur snapshot de données réelles

Invoquer `tester` avec :
```
Mode : migration
Migration : [chemin du fichier]
Dataset : snapshot de production (anonymisé) si disponible
Vérifications : up() sans erreur, down() sans erreur, données cohérentes après up()
```

```bash
# Restaurer un snapshot anonymisé
pg_restore -d db_test prod_snapshot_anonymized.dump

# Lancer la migration
alembic upgrade head  # ou équivalent

# Vérifier l'intégrité
psql db_test -c "SELECT COUNT(*) FROM users WHERE new_column IS NULL;"

# Tester le rollback
alembic downgrade -1

# Vérifier que la table est identique à l'état initial
pg_dump db_test | diff - prod_schema_before.sql
```

Gate : migration up + down sans erreur sur données réalistes → continuer.

---

## ÉTAPE 7 — Plan de rollback documenté

Avant tout déploiement, documenter :
```
ROLLBACK PLAN — Migration [nom]
- Commande de rollback : alembic downgrade -1 (ou équivalent)
- Temps estimé de rollback : [N secondes/minutes]
- Perte de données possible : oui/non — [détail]
- Code à reverter en cas de rollback : [branche/commit]
- Responsable du rollback : [nom ou "on-call engineer"]
```

---

## ÉTAPE 8 — Déploiement atomique

Invoquer `deployer` avec :
```
Type : db-migration
Migration : [nom]
Stratégie : [A/B/C/D/E selon type]
Code à déployer avec la migration : [branche]
```

Ordre strict selon la stratégie :
- **Ajout de colonne** : migration AVANT le code (le code peut utiliser la colonne dès le départ)
- **Suppression de colonne** : code AVANT la migration (le code ne doit plus référencer la colonne)
- **Migration en 3 phases** : chaque phase est un déploiement indépendant avec vérification

```bash
# Exemple déploiement atomique (Heroku / Railway / Render style)
# Le Procfile ou build command inclut la migration avant le démarrage :
# release: alembic upgrade head
# web: uvicorn app.main:app
```

---

## CONTRAT DE SORTIE

```
DB MIGRATION: [nom descriptif]
TYPE: ajout nullable / ajout NOT NULL / suppression / rename / index / contrainte
STRATEGY: A/B/C/D/E — [description en 1 phrase]

SCHEMA CHANGE:
  Table: [nom]
  Before: [état avant]
  After: [état après]

REVERSIBILITY:
  down() implemented: yes/no
  Data loss on rollback: yes/no — [détail si oui]
  Rollback command: [commande]
  Rollback time estimate: [N sec/min]

GATES:
  Reviewer: APPROVED
  Tested on: [snapshot prod / test data / local only]
  Migration up: OK
  Migration down: OK
  Table size: [N rows / N MB]
  Lock risk: low / medium / high

DEPLOYMENT ORDER: migration-first / code-first / phased
PHASES REMAINING: [si migration multi-phases : phases 2 et 3 à planifier]
```
