#!/usr/bin/env python3
"""Static checks for the Tabhai Prabhu SQL pack (does not execute SQL)."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
core = (ROOT / "001_scripture_schema_draft.sql").read_text(encoding="utf-8")
indexes = (ROOT / "002_search_indexes_draft.sql").read_text(encoding="utf-8")
test = (ROOT / "003_schema_invariants_test.sql").read_text(encoding="utf-8")
seed = (ROOT / "004_seed_work_catalog_draft.sql").read_text(encoding="utf-8")

expected = {
    "works", "editions", "sections", "units", "unit_locators", "sources",
    "rights_holders", "permission_grants", "import_batches", "unit_texts",
    "translations", "word_meanings", "commentaries", "topics", "unit_topics",
    "verification_events", "import_batch_items",
}
created = set(re.findall(r"create\s+table\s+scripture\.([a-z_]+)", core, re.I))
errors = []
if created != expected:
    errors.append(f"Table inventory mismatch. Missing={sorted(expected-created)} extra={sorted(created-expected)}")
if "expected_tables constant integer := 17" not in test:
    errors.append("Smoke test expected table count is not 17")
if not re.search(r"create\s+schema\s+if\s+not\s+exists\s+scripture", core, re.I):
    errors.append("Private scripture schema creation missing")
if not re.search(r"alter\s+table\s+scripture\.%I\s+enable\s+row\s+level\s+security", core, re.I):
    errors.append("RLS enablement loop missing")
if not re.search(r"foreign\s+key\s*\(unit_id,\s*work_id\).*scripture\.units\(id,\s*work_id\)", core, re.I | re.S):
    errors.append("Composite unit/work integrity FK missing")
if not re.search(r"foreign\s+key\s*\(edition_id,\s*work_id\).*scripture\.editions\(id,\s*work_id\)", core, re.I | re.S):
    errors.append("Composite edition/work integrity FK missing")
for code in ("BG", "SB", "CC"):
    if not re.search(r"\('" + code + r"'", seed):
        errors.append(f"Metadata-only seed missing {code}")
if sum(core.count(f"constraint {name}_publication_gate") for name in ("unit_text", "translation", "word_meaning", "commentary")) != 4:
    errors.append("One or more publication safety gates are missing")
if "to_tsvector" not in indexes:
    errors.append("Full-text search indexes missing")
for function_name in (
    "permission_grant_allows",
    "search_published_content",
    "search_ai_retrieval_content",
):
    if not re.search(r"create\\s+or\\s+replace\\s+function\\s+scripture\\." + function_name, core, re.I):
        errors.append(f"Required rights/search function missing: {function_name}")
if "source_id uuid" not in core[core.find("create or replace function scripture.search_published_content"):]:
    errors.append("Search results do not expose source provenance")

if re.search(r"insert\s+into\s+scripture\.(unit_texts|translations|word_meanings|commentaries)", seed, re.I):
    errors.append("Seed unexpectedly includes scripture content")
if errors:
    print("STATIC VALIDATION FAILED")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print("STATIC VALIDATION PASSED")
print(f"- {len(created)} expected tables present")
print("- Composite work/edition integrity checks present")
print("- RLS enablement present")
print("- Search indexes present")
print("- Metadata-only seed for BG, SB, CC")
print("NOTE: This is not a PostgreSQL execution test; run the local Docker workflow for that.")
