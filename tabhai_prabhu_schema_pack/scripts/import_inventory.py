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


def import_rows(conn: Any, rows: list[dict[str, Any]], source_id: str, commit: bool) -> None:
    try:
        with conn.cursor() as cur:
            cur.execute("select title, edition_id from scripture.sources where id = %s", (source_id,))
            source = cur.fetchone()
            if not source:
                raise ValueError(f"Source record {source_id} does not exist")
            source_title, source_edition_id = source
            for row in rows:
                if row["inventory_source"] != source_title:
                    raise ValueError("Inventory source label does not match registered source title")
            editions = {}
            works = {}
            sections = {}
            for row in rows:
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
                section_key = (work_code, row["edition_code"], section_code)
                if section_key not in sections:
                    cur.execute(
                        """
                        insert into scripture.sections
                          (work_id, edition_id, section_kind, canonical_code, canonical_title, sequence_no, edition_label)
                        values (%s, %s, 'chapter', %s, %s, %s, %s)
                        on conflict do nothing
                        returning id
                        """,
                        (works[work_code], editions[edition_key], section_code, section_title, section_seq, row["section_path"]),
                    )
                    got = cur.fetchone()
                    if not got:
                        cur.execute(
                            """select id from scripture.sections
                               where work_id = %s and edition_id = %s and canonical_code = %s""",
                            (works[work_code], editions[edition_key], section_code),
                        )
                        got = cur.fetchone()
                    if not got:
                        raise ValueError(f"Could not resolve section {section_code}")
                    sections[section_key] = got[0]
                cur.execute(
                    """
                    insert into scripture.units
                      (work_id, section_id, canonical_ref, unit_kind, sequence_no, canonical_label, inventory_state, inventory_notes)
                    values (%s, %s, %s, %s::scripture.unit_kind, %s, %s, 'expected',
                            'Inventory metadata only; source and edition must be independently verified.')
                    on conflict (canonical_ref) do nothing
                    returning id
                    """,
                    (works[work_code], sections[section_key], row["canonical_ref"], row["unit_kind"], row["sequence_no"], row.get("canonical_label") or row["canonical_ref"]),
                )
                if not cur.fetchone():
                    cur.execute("select work_id, section_id from scripture.units where canonical_ref = %s", (row["canonical_ref"],))
                    existing = cur.fetchone()
                    if not existing or existing[0] != works[work_code] or existing[1] != sections[section_key]:
                        raise ValueError(f"Existing canonical reference {row['canonical_ref']} conflicts with this inventory")
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
    parser.add_argument("--commit", action="store_true", help="Actually commit inventory metadata; default is dry-run/rollback")
    args = parser.parse_args()
    try:
        rows = read_inventory(args.csv_file)
        if not args.database_url:
            import os
            args.database_url = os.environ.get("DATABASE_URL")
        if not args.database_url:
            raise ValueError("Set DATABASE_URL to a disposable/local PostgreSQL database")
        if psycopg is None:
            raise ValueError('Install psycopg v3: python -m pip install "psycopg[binary]"')
        with psycopg.connect(args.database_url) as conn:
            import_rows(conn, rows, args.source_id, args.commit)
        print(f"{'COMMITTED' if args.commit else 'DRY RUN PASSED'}: {len(rows)} inventory rows checked.")
        if not args.commit:
            print("No database changes were retained. Re-run with --commit to insert metadata.")
        return 0
    except Exception as exc:
        print(f"IMPORT FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
