# Tabhai Prabhu — Scripture Knowledge Base

A free-first PostgreSQL 17 schema draft for a searchable Gaudiya Vaishnava scripture catalogue.

## Safety boundary

- This is development work only. It must not be applied to the production Supabase project.
- No changes are made to the existing Yatra registration tables, payment storage, or chatbot.
- No paid Supabase plan, managed branch, paid API, or paid service is required for local testing.
- No scripture text, translations, word meanings, purports, scans, or artwork are included.
- Do not import or publish protected BBT editorial content without written permission covering the intended uses.

## Contents

- `001_scripture_schema_draft.sql` — 17-table schema in a private `scripture` schema.
- `002_search_indexes_draft.sql` — PostgreSQL full-text indexes.
- `003_schema_invariants_test.sql` — read-only structural checks.
- `004_seed_work_catalog_draft.sql` — metadata-only catalogue records for BG, SB, CC.
- `inventory_template.csv` — expected textual unit inventory.
- `bg_chapter_inventory_baseline.csv` and `bg_expected_unit_inventory_provisional.csv` — a 700-reference metadata scaffold for the commonly used Bhagavad-gita numbering; every row remains provisional until checked against the selected edition.
- `rights_register_template.csv` — permissions and rights register.
- `scripts/` — local test and static validation helpers.

## PostgreSQL validation

The repository workflow at `.github/workflows/postgresql-validation.yml` runs a disposable PostgreSQL 17 service, applies the schema/indexes/metadata seed and executes the read-only invariant test. It does not connect to Supabase or production.

For local testing, install PostgreSQL 17 and set `DATABASE_URL` to a disposable local database, then run:

```bash
python scripts/validate_pack.py
python scripts/validate_inventory.py bg_expected_unit_inventory_provisional.csv
bash scripts/run-postgres-tests.sh
```

Alternatively use the Supabase CLI + Docker local workflow in `scripts/bootstrap-local.sh`. Do not point any test runner at production.

## Content and rights safeguards

- Inventory rows must be derived from a named edition's legally usable table of contents and verified numbering.
- Do not assume modern translations, word meanings, purports, editorial matter, scans, or artwork are public domain merely because the underlying scripture is ancient.
- Record provenance and rights separately from textual verification.
- Publication requires verified content and a documented public-domain or licensed status.
- Permission to display does not automatically permit search indexing, embeddings, AI retrieval, or redistribution. Track each permission independently.

## Design

- Canonical references are stable across editions; edition-specific page/verse locators are stored separately.
- Units support verse, Sanskrit verse, Bengali payar, prose, invocation, song, prayer and other forms.
- Original text and transliteration are separate from translations, word meanings and commentaries.
- The schema is private by default. No browser-role grants or public policies are created.
- Any future public search endpoint must retrieve exact verified source passages and enforce the relevant rights permissions before returning content.

## Production

Production deployment requires a separate review and explicit approval of the exact migration, backup/restore verification, RLS review, security/performance checks, and rollback plan.

## Bhagavad-gita inventory note

The provisional inventory contains 700 reference slots across 18 chapters. This is a planning scaffold, not a verified edition transcription. Chapter 13 numbering and other recension/edition differences must be checked against the actual chosen edition. No Sanskrit text, translation, word meanings, or purports are included. The GitHub Actions workflow checks the row count and reference format only; it cannot certify textual accuracy.

## Inventory import pipeline

The metadata importer is `scripts/import_inventory.py`. It accepts a CSV matching
`inventory_template.csv`, validates canonical reference formats and duplicates, and
requires an already-registered work, named edition, and source record. It creates
canonical chapter sections and units, attaches edition-specific locators, and records an
import batch plus item-level audit entries. Dry-run rolls all of these changes back.

Install its optional database driver with `python -m pip install "psycopg[binary]"`.
Set `DATABASE_URL` to a disposable/local PostgreSQL database. First run without
`--commit` (dry-run; transaction is rolled back). Only after confirming the target
database, edition metadata, source provenance, and inventory CSV should an operator
add `--commit`. The provisional BG scaffold is intentionally rejected by the importer
because it does not name a real edition. No verse text or translations are imported.

Example (dry-run):
```bash
python scripts/import_inventory.py your_verified_inventory.csv --source-id YOUR_SOURCE_UUID
```

## Bhagavad-gita edition selection and rights

`bg_edition_candidates.csv` records bibliographic candidates from the official BBT catalog.
They are deliberately marked `candidate_not_selected`: select and verify the exact printing
against the physical/reference copy before registering an edition as the primary reference.
Do not treat the 700 provisional slots as a verified edition inventory.

See `BBT_RIGHTS_CLEARANCE_CHECKLIST.md` for the written-permission scope required before
copying, indexing, publicly displaying, or using BBT editorial material in AI retrieval.

**Additional rights-chain caution:** the separate site `officialbbt.org` currently publishes
a notice about the 1972 Trust's copyright ownership and ongoing trusteeship/licensing
regularisation. The notice says its trusteeship is still being confirmed. Do not assume
that BBTI's permissions page or the separate Trust notice alone resolves licensing
authority. Obtain legal advice and verify the chain of authority before any BBT editorial
content is imported. See `BBT_RIGHTS_CLEARANCE_CHECKLIST.md`.

## BG / SB / CC edition candidates

`work_edition_candidates.csv` records BBT catalogue candidates for all three works.
These are discovery metadata only and are all marked `candidate_not_selected`. The
Srimad-Bhagavatam 12-volume Cantos 1-10 and 18-volume Cantos 1-12 catalogued sets are
different scopes; Sri Caitanya-caritamrita 9-volume and one-volume formats are also
different edition structures. Do not merge their locators or assume their page maps
are interchangeable.

Use `EDITION_VERIFICATION_WORKSHEET.md` for every physical edition before registering
it as the reference edition or importing its inventory. The separate 1972 Trust notice
and BBTI permissions information are both recorded in the rights checklist; legal
authority for licensing remains an open verification item.

## Database integrity and rights enforcement

- Canonical unit sequence numbers are unique within a canonical section.
- A permission grant is tied to one exact edition; content from another edition cannot reference it.
- `scripture.permission_grant_allows(grant_id, edition_id, action, language)` checks grant status, dates, permitted action, language and the corresponding action flag at request time.
- The helper supports `public_display`, `search_indexing`, `embeddings`, `ai_retrieval` and `redistribution`. Unknown actions fail closed.
- Public-domain determinations still require a source record and documented human/legal review. The helper does not make public-domain determinations.
- A published flag is not a substitute for request-time permission checks: grants can expire or be amended. The application must call the helper before each protected use.

The CI workflow runs `005_rights_integrity_test.sql` against disposable PostgreSQL. Its fixtures are synthetic and rolled back; they test edition-mismatch rejection, expired-grant rejection, denied AI retrieval, language scoping, and duplicate canonical sequence rejection.

`BBT_RIGHTS_REQUEST_TEMPLATE.md` is a draft letter for seeking written permissions and verifying the licensor's authority. It is not sent automatically and is not legal advice.

## Rights-filtered scripture search

`scripture.search_published_content(query, language, limit)` is the database search
contract for the future server-side API. It searches original text, translations, word
meanings and commentaries, but returns only rows that are both verified and published.
For licensed material it checks the exact edition's current grant for both
`search_indexing` and `public_display`, including expiry and permitted language.
Public-domain rows still require a source record and a confirmed rights state.

The function is an invoker function in the private schema. It does not grant browser or
anonymous access and must not be exposed directly. A reviewed server-side endpoint must
apply rate limits, authentication/abuse controls and the required output policy. The
database search function returns snippets (up to 500 characters), not full documents.

**Database target guard:** the importer refuses all Supabase database and pooler
hostnames, even if remote-target opt-in is supplied. Other remote PostgreSQL targets
are blocked by default and require `--allow-remote-database`. Use a disposable local
PostgreSQL database for normal development. This is an additional safeguard against
accidental production access.

See `RELEASE_AND_CONTENT_CHECKLIST.md` for the end-to-end edition, rights, inventory,
text review, search and production-release gates. Production deployment requires
separate project-owner approval and is not part of this development PR.
