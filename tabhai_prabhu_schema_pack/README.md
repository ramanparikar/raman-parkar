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

## Bhagavad-gita provisional inventory integrity

`scripts/validate_bg_baseline.py` checks the internal arithmetic of the 18-chapter,
700-reference planning scaffold: chapter totals, continuous verse-number sequences,
duplicate references, section labels and provisional edition markers. It does **not**
verify any printed edition or establish a universal verse numbering. The CI workflow
runs both positive and negative tests for this validator.

The general `scripts/validate_inventory.py` also checks that a verse-like unit's
sequence number agrees with the final numeric component of its canonical reference.
This prevents an accidental mismatch such as `BG.02.047` being imported as sequence 46.

## Separate AI retrieval gate

`scripture.search_ai_retrieval_content(query, language, limit)` is a separate,
bounded-snippet retrieval contract for a future server-side AI endpoint. It does not
reuse search-indexing permission as a substitute for AI permission. Licensed content
must have an active, edition-matched grant that explicitly permits `ai_retrieval`
in the requested language. Public-domain content still requires a source record and
documented review. The SQL integration fixture proves that retrieval is denied before
AI permission is granted and allowed only after the synthetic grant explicitly adds it.

This function does not itself authorise a public endpoint or provide model safety,
attribution, citation, rate-limiting or abuse controls. Those remain requirements for
the future server-side application.

## Edition-specific printed page locators

The inventory template and metadata importer support optional `page_start` and
`page_end` values. These are stored on `unit_locators` separately for each edition,
so the same canonical verse can point to different printed pages in different
printings. Roman-numeral front matter and publisher-specific pagination may be entered
as text. A page locator is provenance metadata, not proof that the verse transcription
or numbering has been verified.

Both search contracts return the underlying `source_id` alongside the canonical
reference and edition identifier. The server-side application can use this provenance
key to resolve the bibliographic source record and construct an attributable answer.

The inventory validator and importer cross-check `section_path` against the canonical
reference for all three works: BG chapter, SB canto and chapter, and CC lila and
chapter. This guards against attaching a verse to the wrong chapter while preserving
edition-specific printed labels and page numbers in the locator record.

The migration explicitly revokes `PUBLIC` schema usage, table/sequence privileges
and function execution, and applies matching default-privilege revocations for future
objects created by the migration owner. CI checks that the private schema and its
functions are not executable/visible through default PUBLIC grants. A future backend
role must receive only the narrowly scoped privileges it actually needs.

See `SERVER_API_CONTRACT.md` for the proposed future server-side search and AI
retrieval request/response contract. It is design-only; no endpoint or production
Supabase function has been deployed.

## Rights register validation

`rights_register_template.csv` records the exact rights holder, work, edition,
content type, permitted languages and each permitted use separately. The
`scripts/validate_rights_register.py` validator fails closed: a licensed record
requires a permission reference, HTTPS evidence, reviewer, timestamp and explicit
languages; a public-domain assertion requires documented HTTPS evidence and review;
pending, unknown, restricted or uncleared records cannot enable usage flags. The
starter template is intentionally empty and fails validation until a real rights
record is documented. Passing this structural check is not legal advice or proof
that a rights holder has authority to grant the recorded permission.

## Scripture library interface preview

The isolated `tabhai-prabhu-preview.html` page is a metadata-only UI prototype.
It provides BG/SB/CC work selection, provisional chapter/unit locator construction,
canonical-reference format checks and copy-reference interaction. It deliberately
does not display verse text or claim a reference is verified. It does not connect to
Supabase, use credentials, modify the existing Shastra page, chatbot or Yatra flow,
or call an AI service. It is kept separate on the development branch until the
backend API and content-rights gates are reviewed.


## Browser reference preview

The development-only `tabhai-prabhu-preview.html` provides a metadata-only reference builder. Bhagavad-gita unit selectors are bounded by the provisional chapter-count baseline; the UI labels these counts as provisional and requires edition cross-checking. Srimad-Bhagavatam and Caitanya-caritamrita chapter/unit locators remain placeholders until a specific edition is inspected. The shared parser validates format only, not edition existence, textual accuracy or rights.
