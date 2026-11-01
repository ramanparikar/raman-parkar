#!/usr/bin/env python3
"""Validate a scripture inventory CSV before any database import.

This checks catalogue metadata only. It does not fetch or reproduce scripture text.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REQUIRED = {
    "work_code", "edition_code", "section_path", "canonical_ref", "unit_kind",
    "sequence_no", "inventory_source",
}
REF_PATTERNS = {
    "BG": re.compile(r"^BG\.\d{2}\.\d{3}$"),
    "SB": re.compile(r"^SB\.\d{2}\.\d{2}\.\d{3}$"),
    "CC": re.compile(r"^CC\.(?:ADI|MADHYA|ANTYA)\.\d{2,3}\.\d{3}$"),
}
UNIT_KINDS = {
    "verse", "sanskrit_verse", "bengali_payar", "prose", "invocation",
    "song", "prayer", "caption", "other",
}


def section_path_matches(work: str, match: re.Match[str], section_path: str) -> bool:
    path = section_path.lower().replace("_", "-")
    if work == "BG":
        return bool(re.search(r"chapter[-\\s]*0*" + str(int(match.group(1))) + r"(?:\\D|$)", path))
    if work == "SB":
        canto, chapter = int(match.group(1)), int(match.group(2))
        return bool(
            re.search(r"canto[-\\s]*0*" + str(canto) + r"(?:\\D|$)", path)
            and re.search(r"chapter[-\\s]*0*" + str(chapter) + r"(?:\\D|$)", path)
        )
    lila, chapter = match.group(1).lower(), int(match.group(2))
    return bool(lila in path and re.search(r"chapter[-\\s]*0*" + str(chapter) + r"(?:\\D|$)", path))


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED - headers
        if missing:
            return [f"Missing required columns: {', '.join(sorted(missing))}"]

        seen: set[str] = set()
        row_count = 0
        for line, row in enumerate(reader, start=2):
            row_count += 1
            get = lambda key: (row.get(key) or "").strip()
            work = get("work_code").upper()
            ref = get("canonical_ref")
            match = None
            if work not in REF_PATTERNS:
                errors.append(f"Line {line}: unsupported work_code {work!r}")
            else:
                match = REF_PATTERNS[work].fullmatch(ref)
                if not match:
                    errors.append(f"Line {line}: canonical_ref {ref!r} does not match {work} reference format")
            if ref in seen:
                errors.append(f"Line {line}: duplicate canonical_ref {ref!r}")
            seen.add(ref)
            if not get("edition_code"):
                errors.append(f"Line {line}: edition_code is required")
            if not get("section_path"):
                errors.append(f"Line {line}: section_path is required")
            elif match and not section_path_matches(work, match, get("section_path")):
                errors.append(f"Line {line}: section_path does not agree with canonical reference {ref!r}")
            if not get("inventory_source"):
                errors.append(f"Line {line}: inventory_source is required for provenance")
            kind = get("unit_kind")
            if kind not in UNIT_KINDS:
                errors.append(f"Line {line}: invalid unit_kind {kind!r}")
            try:
                sequence = int(get("sequence_no"))
                if sequence < 0:
                    raise ValueError
                if match and kind in {"verse", "sanskrit_verse", "bengali_payar"}:
                    reference_sequence = int(ref.split(".")[-1])
                    if sequence != reference_sequence:
                        errors.append(f"Line {line}: sequence_no must match the canonical verse number {reference_sequence}")
            except ValueError:
                errors.append(f"Line {line}: sequence_no must be a non-negative integer")
        if row_count == 0:
            errors.append("Inventory file has a header but no data rows")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    errors = validate(args.csv_file)
    if errors:
        print("INVENTORY VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("INVENTORY VALIDATION PASSED")
    print("Metadata is structurally valid; edition accuracy and rights still require human verification.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
