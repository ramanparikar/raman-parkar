#!/usr/bin/env python3
"""Safely import verified *inventory metadata only* into a disposable/local DB.

No verse text, translations, word meanings, purports, scans, or artwork are imported.
Default mode is dry-run. Use --commit only after validating the CSV and DB target.
Requires psycopg (v3): python -m pip install "psycopg[binary]".
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

try:
    import psycopg
except ImportError:
    psycopg = None

REFS = {
    "BG": re.compile(r"^BG\.(\d{2})\.(\d{3})$"),
    "SB": re.compile(r"^SB\.(\d{2})\.(\d{2})\.(\d{3})$"),
    "CC": re.compile(r"^CC\.(ADI|MADHYA|ANTYA)\.(\d{2,3})\.(\d{3})$"),
}
KINDS = {"verse", "sanskrit_verse", "bengali_payar", "prose", "invocation", "song", "prayer", "caption", "other"}
REQUIRED = {"work_code", "edition_code", "section_path", "canonical_ref", "unit_kind", "sequence_no", "inventory_source"}


def validate_database_target(database_url: str, allow_remote: bool = False) -> None:
    """Block accidental production Supabase connections and remote targets by default."""
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
        raise ValueError("DATABASE_URL must be a PostgreSQL URL with an explicit host")
    host = parsed.hostname.lower()
    if host.endswith(".supabase.co"):
        raise ValueError("Supabase projects are blocked by this importer; do not connect it to production or staging Supabase")
    if host not in {"localhost", "127.0.0.1", "::1"} and not allow_remote:
        raise ValueError("Remote database target blocked; use a disposable local PostgreSQL database or explicitly pass --allow-remote-database for a separately approved non-Supabase target")


def read_inventory(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        rows = []
        seen = set()
        for line, raw in enumerate(reader, start=2):
            row = {k: (v or "").strip() for k, v in raw.items()}
            work = row["work_code"].upper()
            match = REFS.get(work).fullmatch(row["canonical_ref"]) if work in REFS else None
            if not match:
                raise ValueError(f"Line {line}: invalid canonical reference for {work}: {row['canonical_ref']!r}")
            if row["canonical_ref"] in seen:
                raise ValueError(f"Line {line}: duplicate canonical reference {row['canonical_ref']}")
            seen.add(row["canonical_ref"])
            if not row["edition_code"] or row["edition_code"] == "PROVISIONAL_BASELINE":
                raise ValueError(f"Line {line}: choose a real, named edition; provisional scaffold cannot be imported")
            if not row["section_path"] or not row["inventory_source"]:
                raise ValueError(f"Line {line}: section_path and inventory_source are required")
            if row["unit_kind"] not in KINDS:
                raise ValueError(f"Line {line}: unsupported unit_kind {row['unit_kind']!r}")
            try:
                seq = int(row["sequence_no"])
                if seq < 1:
                    raise ValueError
            except ValueError:
                raise ValueError(f"Line {line}: sequence_no must be a positive integer")
            row["work_code"] = work
            row["sequence_no"] = seq
            if row["unit_kind"] in {"verse", "sanskrit_verse", "bengali_payar"} and seq != int(row["canonical_ref"].split(".")[-1]):
                raise ValueError(f"Line {line}: sequence_no must match the canonical verse number for verse-like units")
            if not re.fullmatch(r"[A-Z0-9][A-Z0-9_.-]*", row["edition_code"]):
                raise ValueError(f"Line {line}: edition_code must use uppercase letters, digits, dot, underscore or hyphen")
            rows.append(row)
    if not rows:
        raise ValueError("Inventory contains no rows")
    return rows


def section_details(row: dict[str, Any]) -> tuple[str, str, int]:
    work = row["work_code"]
    ref = row["canonical_ref"]
    if work == "BG":
        chapter = int(ref.split(".")[1])
        return f"BG.{chapter:02d}", f"Chapter {chapter}", chapter
    if work == "SB":
        _, canto, chapter, _ = ref.split(".")
        return f"SB.{canto}.{chapter}", f"Canto {int(canto)}, Chapter {int(chapter)}", int(chapter)
    _, lila, chapter, _ = ref.split(".")
    return f"CC.{lila}.{chapter}", f"{lila.title()}-lila, Chapter {int(chapter)}", int(chapter)


def import_rows(conn: Any, rows: list[dict[str, Any]], source_id: str, commit: bool, batch_name: str = "inventory metadata import") -> None:
    """Insert canonical units, edition locators, and audit records atomically."""
    try:
        with conn.cursor() as cur:
            cur.execute("select title, edition_id from scripture.sources where id = %s", (source_id,))
            source = cur.fetchone()
            if not source:
                raise ValueError(f"Source record {source_id} does not exist")
            source_title, source_edition_id = source
            cur.execute(
                """insert into scripture.import_batches
                   (batch_name, source_id, edition_id, imported_by, import_method, batch_notes)
                   values (%s, %s, %s, %s, %s, %s) returning id""",
                (batch_name, source_id, source_edition_id, "inventory_importer",
                 "csv_inventory_metadata",
                 "Metadata-only inventory import; no scripture text or translations imported."),
            )
            batch_id = cur.fetchone()[0]
            editions: dict[tuple[str, str], Any] = {}
            works: dict[str, Any] = {}
            sections: dict[tuple[str, str], Any] = {}
            for row in rows:
                if row["inventory_source"] != source_title:
                    raise ValueError("Inventory source label does not match registered source title")
                work_code = row["work_code"]
                if work_code not in works:
                    cur.execute("select id from scripture.works where code = %s", (work_code,))
                    got = cur.fetchone()
                    if not got:
                        raise ValueError(f"Work {work_code} is not seeded in scripture.works")
                    works[work_code] = got[0]
                edition_key = (work_code, row["edition_code"])
                if edition_key not in editions:
                    cur.execute(
                        "select id from scripture.editions where work_id = %s and edition_code = %s",
                        (works[work_code], row["edition_code"]),
                    )
                    got = cur.fetchone()
                    if not got:
                        raise ValueError(f"Edition {row['edition_code']} for {work_code} is not registered")
                    editions[edition_key] = got[0]
                if source_edition_id is not None and source_edition_id != editions[edition_key]:
                    raise ValueError("Source record is registered to a different edition")
                section_code, section_title, section_seq = section_details(row)
                section_key = (work_code, section_code)
                if section_key not in sections:
                    cur.execute(
                        """
                        insert into scripture.sections
                          (work_id, edition_id, section_kind, canonical_code, canonical_title, sequence_no, edition_label)
                        values (%s, null, 'chapter', %s, %s, %s, null)
                        on conflict do nothing returning id
                        """,
                        (works[work_code], section_code, section_title, section_seq),
                    )
                    got = cur.fetchone()
                    if not got:
                        cur.execute(
                            "select id from scripture.sections where work_id = %s and canonical_code = %s",
                            (works[work_code], section_code),
                        )
                        got = cur.fetchone()
                    if not got:
                        raise ValueError(f"Could not resolve canonical section {section_code}")
                    sections[section_key] = got[0]
                cur.execute(
                    """
                    insert into scripture.units
                      (work_id, section_id, canonical_ref, unit_kind, sequence_no, canonical_label, inventory_state, inventory_notes)
                    values (%s, %s, %s, %s::scripture.unit_kind, %s, %s, 'expected',
                            'Inventory metadata only; source and edition must be independently verified.')
                    on conflict (canonical_ref) do nothing returning id
                    """,
                    (works[work_code], sections[section_key], row["canonical_ref"], row["unit_kind"],
                     row["sequence_no"], row.get("canonical_label") or row["canonical_ref"]),
                )
                unit = cur.fetchone()
                if not unit:
                    cur.execute(
                        "select id, work_id, section_id from scripture.units where canonical_ref = %s",
                        (row["canonical_ref"],),
                    )
                    existing = cur.fetchone()
                    if not existing or existing[1] != works[work_code] or existing[2] != sections[section_key]:
                        raise ValueError(f"Existing canonical reference {row['canonical_ref']} conflicts with this work/section")
                    unit_id = existing[0]
                else:
                    unit_id = unit[0]
                cur.execute(
                    """insert into scripture.import_batch_items
                       (batch_id, entity_type, entity_id, item_state, message)
                       values (%s, 'unit', %s, 'imported', 'Canonical inventory metadata')""",
                    (batch_id, unit_id),
                )
                cur.execute(
                    """
                    insert into scripture.unit_locators
                      (work_id, unit_id, edition_id, section_label, verse_label, source_id, locator_note)
                    values (%s, %s, %s, %s, %s, %s, 'Edition-specific locator imported from inventory metadata')
                    on conflict (unit_id, edition_id) do nothing
                    returning id
                    """,
                    (works[work_code], unit_id, editions[edition_key],
                     row.get("edition_section_label") or row["section_path"],
                     row.get("edition_verse_label") or row["canonical_ref"].split(".")[-1],
                     source_id),
                )
                locator = cur.fetchone()
                if locator:
                    locator_id = locator[0]
                else:
                    cur.execute(
                        "select id, section_label, verse_label, source_id from scripture.unit_locators where unit_id = %s and edition_id = %s",
                        (unit_id, editions[edition_key]),
                    )
                    existing_locator = cur.fetchone()
                    if not existing_locator:
                        raise ValueError(f"Could not resolve locator for {row['canonical_ref']}")
                    locator_id, section_label, verse_label, locator_source_id = existing_locator
                    expected_locator = (
                        row.get("edition_section_label") or row["section_path"],
                        row.get("edition_verse_label") or row["canonical_ref"].split(".")[-1],
                        source_id,
                    )
                    if (section_label, verse_label, locator_source_id) != expected_locator:
                        raise ValueError(f"Existing edition locator conflicts for {row['canonical_ref']}")
                cur.execute(
                    """insert into scripture.import_batch_items
                       (batch_id, entity_type, entity_id, item_state, message)
                       values (%s, 'locator', %s, 'imported', 'Edition-specific locator metadata')""",
                    (batch_id, locator_id),
                )
            cur.execute("update scripture.import_batches set completed_at = now() where id = %s", (batch_id,))
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--database-url", default=None, help="Disposable/local PostgreSQL connection URL; or set DATABASE_URL")
    parser.add_argument("--source-id", required=True, help="Existing scripture.sources UUID documenting this inventory")
    parser.add_argument("--batch-name", default=None, help="Audit label for this import batch (defaults to CSV filename)")
    parser.add_argument("--commit", action="store_true", help="Actually commit inventory metadata; default is dry-run/rollback")
    parser.add_argument("--allow-remote-database", action="store_true", help="Allow a remote non-Supabase PostgreSQL target; remote targets are blocked by default")
    args = parser.parse_args()
    try:
        rows = read_inventory(args.csv_file)
        if not args.database_url:
            import os
            args.database_url = os.environ.get("DATABASE_URL")
        if not args.database_url:
            raise ValueError("Set DATABASE_URL to a disposable/local PostgreSQL database")
        validate_database_target(args.database_url, args.allow_remote_database)
        if psycopg is None:
            raise ValueError('Install psycopg v3: python -m pip install "psycopg[binary]"')
        with psycopg.connect(args.database_url) as conn:
            import_rows(conn, rows, args.source_id, args.commit, args.batch_name or args.csv_file.stem)
        print(f"{'COMMITTED' if args.commit else 'DRY RUN PASSED'}: {len(rows)} inventory rows checked.")
        if not args.commit:
            print("No database changes were retained. Re-run with --commit to insert metadata.")
        return 0
    except Exception as exc:
        print(f"IMPORT FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
