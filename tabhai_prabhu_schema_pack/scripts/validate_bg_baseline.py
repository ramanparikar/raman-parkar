#!/usr/bin/env python3
"""Validate the provisional Bhagavad-gita 700-reference scaffold.

This validates only the internal arithmetic and reference sequence of the scaffold.
It does not certify any edition's actual numbering or textual completeness.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

BASELINE_FIELDS = {"work_code", "chapter_number", "chapter_ref", "expected_verse_count", "inventory_state"}
INVENTORY_FIELDS = {"work_code", "canonical_ref", "unit_kind", "sequence_no", "section_path", "edition_code"}


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def validate(baseline_path: Path, inventory_path: Path) -> list[str]:
    errors: list[str] = []
    baseline, bh = read_csv(baseline_path)
    inventory, ih = read_csv(inventory_path)
    if missing := BASELINE_FIELDS - bh:
        return [f"Baseline missing columns: {', '.join(sorted(missing))}"]
    if missing := INVENTORY_FIELDS - ih:
        return [f"Inventory missing columns: {', '.join(sorted(missing))}"]
    chapters: dict[int, int] = {}
    for line, row in enumerate(baseline, 2):
        try:
            number = int(row["chapter_number"])
            count = int(row["expected_verse_count"])
        except (ValueError, TypeError):
            errors.append(f"Baseline line {line}: chapter and expected count must be integers")
            continue
        if row["work_code"] != "BG" or row["chapter_ref"] != f"BG.{number:02d}":
            errors.append(f"Baseline line {line}: inconsistent Bhagavad-gita chapter reference")
        if number in chapters:
            errors.append(f"Baseline line {line}: duplicate chapter {number}")
        if count < 1:
            errors.append(f"Baseline line {line}: expected count must be positive")
        if row["inventory_state"] != "expected":
            errors.append(f"Baseline line {line}: provisional chapter state must remain 'expected'")
        chapters[number] = count
    if set(chapters) != set(range(1, 19)):
        errors.append("Baseline must contain exactly chapters 1 through 18")
    if sum(chapters.values()) != 700:
        errors.append(f"Baseline counts sum to {sum(chapters.values())}, not 700")

    observed: dict[int, list[int]] = {}
    seen: set[str] = set()
    for line, row in enumerate(inventory, 2):
        ref = row["canonical_ref"].strip()
        match = re.fullmatch(r"BG\.(\d{2})\.(\d{3})", ref)
        if row["work_code"].strip() != "BG" or not match:
            errors.append(f"Inventory line {line}: invalid BG canonical reference {ref!r}")
            continue
        chapter, verse = int(match.group(1)), int(match.group(2))
        if ref in seen:
            errors.append(f"Inventory line {line}: duplicate reference {ref}")
        seen.add(ref)
        if chapter not in chapters:
            errors.append(f"Inventory line {line}: chapter {chapter} is absent from baseline")
            continue
        if row["unit_kind"].strip() != "verse":
            errors.append(f"Inventory line {line}: expected verse unit kind")
        try:
            sequence = int(row["sequence_no"])
        except (ValueError, TypeError):
            errors.append(f"Inventory line {line}: sequence_no must be an integer")
            continue
        if sequence != verse:
            errors.append(f"Inventory line {line}: sequence_no {sequence} does not match reference verse {verse}")
        if row["section_path"].strip() != f"chapter-{chapter:02d}":
            errors.append(f"Inventory line {line}: section_path does not match chapter {chapter}")
        if row["edition_code"].strip() != "PROVISIONAL_BASELINE":
            errors.append(f"Inventory line {line}: baseline edition_code must remain provisional")
        observed.setdefault(chapter, []).append(verse)

    if len(inventory) != 700:
        errors.append(f"Inventory contains {len(inventory)} rows, not 700")
    for chapter, expected in sorted(chapters.items()):
        numbers = sorted(observed.get(chapter, []))
        if len(numbers) != expected:
            errors.append(f"Chapter {chapter}: found {len(numbers)} references, expected provisional count {expected}")
        if numbers != list(range(1, expected + 1)):
            errors.append(f"Chapter {chapter}: references are not a continuous 1..{expected} sequence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    errors = validate(args.baseline, args.inventory)
    if errors:
        print("BHAGAVAD-GITA BASELINE VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("BHAGAVAD-GITA BASELINE VALIDATION PASSED")
    print("700 provisional references; 18 chapters; numbering arithmetic is internally consistent.")
    print("WARNING: this does not verify a physical edition, recension, or textual numbering.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
