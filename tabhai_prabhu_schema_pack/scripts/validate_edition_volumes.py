#!/usr/bin/env python3
"""Validate completed physical-volume verification records; never selects an edition."""
import csv
import datetime as dt
import re
import sys
from pathlib import Path

REQUIRED = {
    "work_code", "edition_code", "volume_number", "volume_title", "publisher",
    "edition_statement", "publication_year", "total_pages", "first_section",
    "last_section", "first_printed_page", "last_printed_page",
    "title_page_checked", "copyright_page_checked", "table_of_contents_checked",
    "numbering_checked", "independent_checker", "checked_on",
    "physical_copy_reference", "evidence_notes",
}
CHECK_FIELDS = (
    "title_page_checked", "copyright_page_checked",
    "table_of_contents_checked", "numbering_checked",
)
VALID_WORKS = {"BG", "SB", "CC"}


def validate(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        seen = set()
        count = 0
        for line, row in enumerate(reader, 2):
            work = (row.get("work_code") or "").strip()
            edition = (row.get("edition_code") or "").strip()
            if work not in VALID_WORKS or not edition:
                raise ValueError(f"Line {line}: valid work_code and edition_code are required")
            try:
                volume = int(row["volume_number"])
                year = int(row["publication_year"])
                pages = int(row["total_pages"])
            except (ValueError, TypeError):
                raise ValueError(f"Line {line}: volume_number, publication_year and total_pages must be integers")
            if volume < 1 or pages < 1 or not 1400 <= year <= 2200:
                raise ValueError(f"Line {line}: invalid volume number, page count or publication year")
            key = (work, edition, volume)
            if key in seen:
                raise ValueError(f"Line {line}: duplicate work/edition/volume record")
            seen.add(key)
            for field in (
                "volume_title", "publisher", "edition_statement", "first_section",
                "last_section", "first_printed_page", "last_printed_page",
                "independent_checker", "physical_copy_reference", "evidence_notes",
            ):
                if not (row.get(field) or "").strip():
                    raise ValueError(f"Line {line}: {field} is required")
            for field in CHECK_FIELDS:
                if (row.get(field) or "").strip().lower() != "yes":
                    raise ValueError(f"Line {line}: {field} must be yes before a volume is verified")
            try:
                checked = dt.date.fromisoformat(row["checked_on"].strip())
            except (ValueError, TypeError):
                raise ValueError(f"Line {line}: checked_on must be YYYY-MM-DD")
            if checked > dt.date.today():
                raise ValueError(f"Line {line}: checked_on cannot be in the future")
            # Page labels intentionally remain strings: roman numerals and supplements are valid.
            count += 1
    if not count:
        raise ValueError("No completed physical-volume verification records found")
    return count


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise ValueError("Provide at least one completed volume-verification CSV")
        for filename in sys.argv[1:]:
            print(f"{filename}: {validate(Path(filename))} physical-volume records validated.")
    except Exception as error:
        print(f"VOLUME VERIFICATION FAILED: {error}", file=sys.stderr)
        sys.exit(1)
