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
- `rights_register_template.csv` — permissions and rights register.
- `scripts/` — local test and static validation helpers.

## PostgreSQL validation

The repository workflow at `.github/workflows/postgresql-validation.yml` runs a disposable PostgreSQL 17 service, applies the schema/indexes/metadata seed and executes the read-only invariant test. It does not connect to Supabase or production.

For local testing, install PostgreSQL 17 and set `DATABASE_URL` to a disposable local database, then run:

```bash
python scripts/validate_pack.py
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
