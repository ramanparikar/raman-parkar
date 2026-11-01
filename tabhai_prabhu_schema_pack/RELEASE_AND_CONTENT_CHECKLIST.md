# Tabhai Prabhu release and content-ingestion checklist

This is an operational gate, not an authorisation to publish or deploy.

## A. Edition identity
- [ ] A physical copy or authoritative library copy has been inspected.
- [ ] Title page, copyright page, publisher, edition statement, impression, year, ISBN and volume details are recorded.
- [ ] The exact selected edition is registered in `scripture.editions`.
- [ ] Alternate editions are kept as separate edition records.
- [ ] Canonical numbering and edition-specific page/verse locators have been independently checked.
- [ ] Chapter/canto/lila coverage is reconciled; no totals are assumed from another edition.

## B. Provenance and rights
- [ ] Source record identifies the exact edition and inventory source.
- [ ] Copyright owner and licensing authority are independently verified for the exact work, edition, territory and use.
- [ ] Written permission or documented public-domain determination is retained as evidence.
- [ ] Permission grant names the exact edition and permitted languages.
- [ ] The grant separately addresses storage, public display, search indexing, embeddings, AI retrieval and redistribution.
- [ ] Start date, expiry, attribution, restrictions and withdrawal procedure are recorded.
- [ ] No protected material is imported while authority or scope is unclear.

## C. Metadata inventory
- [ ] CSV passes `validate_inventory.py`.
- [ ] Candidate edition CSV passes `validate_edition_candidates.py`.
- [ ] Each canonical reference is unique and matches its work's reference format.
- [ ] Verse-like unit sequence number matches the canonical verse number.
- [ ] Every inventory row has a named edition, section path and source provenance.
- [ ] Importer dry-run succeeds against a disposable local PostgreSQL database.
- [ ] Importer checks edition/source alignment and existing locator conflicts.
- [ ] Importer commit is reviewed and run only against a disposable/local database.
- [ ] Import batch and item audit trail is retained.

## D. Text and editorial content
- [ ] Text is obtained from an authorised source; no scraping or unapproved copying.
- [ ] Sanskrit/Bengali original, transliteration, translation, word meanings and commentaries are separate records.
- [ ] Textual transcription is independently checked against the selected edition.
- [ ] Editorial punctuation, spelling, diacritics and verse numbering are reviewed.
- [ ] Review events identify verifier, date, method and evidence source.
- [ ] Rights status and review state are recorded independently.
- [ ] Synthetic fixtures are never mistaken for real scripture content.

## E. Search and publication
- [ ] Search uses `scripture.search_published_content`, not a broad unfiltered table query.
- [ ] Search results require `verified` and `published` states.
- [ ] Licensed content passes current `search_indexing` and `public_display` grant checks for its edition and language.
- [ ] Public-domain content has a source and documented rights review.
- [ ] AI retrieval separately checks `ai_retrieval` permission; search permission does not imply AI permission.
- [ ] Embeddings separately check `embeddings` permission; search permission does not imply embeddings permission.
- [ ] Expiry/withdrawal is rechecked at request time.
- [ ] No anonymous/browser role receives direct access to the private `scripture` schema.
- [ ] Public API has authentication/rate limits, output limits and abuse controls.
- [ ] No service-role key is placed in browser code.

## F. Production deployment (separate approval required)
- [ ] Draft PR reviewed and approved.
- [ ] Backup and rollback plan documented.
- [ ] Production migration reviewed independently.
- [ ] Existing Yatra registration, payment storage and chatbot regression-tested.
- [ ] Production deployment authorised separately by the project owner.
- [ ] Post-deployment smoke test and monitoring completed.

**Current status:** database foundation and automated disposable-PostgreSQL tests exist. No scripture text is imported, no rights grant is recorded, and no production deployment is authorised.
