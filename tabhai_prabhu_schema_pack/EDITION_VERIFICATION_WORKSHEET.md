# Edition verification worksheet

Use one completed worksheet per physical edition. A web catalogue entry is a discovery aid, not a substitute for inspecting the actual copy.

## Bibliographic identity
- Work code (BG / SB / CC):
- Exact title as printed:
- Author / translator / commentator:
- Publisher / imprint:
- Place of publication:
- Copyright year(s):
- Edition statement:
- Printing / impression number and year:
- ISBN / catalogue number:
- Language(s):
- Script(s):
- Total pages:
- Volume number and total set size:
- Physical copy owner / library / accession reference:
- Photographs or scan of title page and copyright page (private evidence only; do not upload copyrighted scans to public repo):

## Multi-volume edition register

For multi-volume works, create one row per physical volume in `edition_volume_verification_template.csv`. Do not treat a set-level catalogue page as proof of each volume's title, printing, pagination, or canto/līlā coverage. Record volume boundaries from the actual table of contents and printed pages. Keep photographs/scans of copyright pages private unless permission expressly allows sharing.

Run completed volume records through `scripts/validate_edition_volumes.py` before treating them as inspected metadata. The validator requires all four checks (title page, copyright page, table of contents and numbering), a physical-copy reference, independent checker and date. It does not decide whether the edition is legally usable or whether all text is correct.

## Textual structure and numbering
- Does this copy preserve the original verse numbering?
- Does it use alternate numbering, omissions, insertions, or editorial renumbering?
- For BG: confirm chapter-wise verse count against this exact copy; explicitly resolve Chapter 13 and all variant numbering.
- For SB: record canto, chapter, verse numbering and volume/part boundaries; do not infer a universal total from another edition.
- For CC: record Adi/Madhya/Antya lila, chapter, verse and non-verse units; record volume mapping and any edition-specific verse numbering.
- Record front matter, prayers, songs, appendices, indexes and other non-verse units separately where in scope.

## Verification evidence
- Inventory source title and source UUID:
- Exact page or scan locator for each section:
- Independent checker:
- Date checked:
- Discrepancies and resolution:
- Inventory CSV SHA-256:
- Status: candidate / transcribed / independently checked / approved for metadata import.

## Rights and publication gate
- Rights holder / licensor verified by:
- Written authority evidence reference:
- Rights scope includes digital storage:
- Rights scope includes public display:
- Rights scope includes full-text indexing:
- Rights scope includes embeddings / semantic search:
- Rights scope includes AI retrieval:
- Rights scope includes language / territory / domain:
- Permission expiry / review date:
- Status: unknown / pending / confirmed for specified uses.

Never set a text row to public or eligible for publication until both textual verification and the applicable rights checks have been completed. A candidate edition record does not itself grant rights.
