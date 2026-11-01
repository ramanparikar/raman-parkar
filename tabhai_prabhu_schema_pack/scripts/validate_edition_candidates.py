#!/usr/bin/env python3
"""Validate bibliographic candidate CSVs without asserting edition correctness."""
import csv
import re
import sys
from pathlib import Path

REQUIRED = {
    "work_code", "edition_code", "title", "publisher", "publication_year",
    "edition_language", "metadata_source_url", "candidate_state", "notes",
}
VALID_WORKS = {"BG", "SB", "CC"}


def valid_isbn(value: str) -> bool:
    compact = re.sub(r"[- ]", "", value.strip()).upper()
    if re.fullmatch(r"\\d{9}[\\dX]", compact):
        digits = [10 if char == "X" else int(char) for char in compact]
        return sum((10 - index) * digit for index, digit in enumerate(digits)) % 11 == 0
    if re.fullmatch(r"\\d{13}", compact):
        digits = [int(char) for char in compact]
        checksum = sum(digit * (1 if index % 2 == 0 else 3) for index, digit in enumerate(digits[:12]))
        return (10 - checksum % 10) % 10 == digits[12]
    return False


def validate(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
        seen = set()
        count = 0
        for line, row in enumerate(reader, 2):
            code = (row.get("work_code") or "").strip()
            edition = (row.get("edition_code") or "").strip()
            key = (code, edition)
            if code not in VALID_WORKS:
                raise ValueError(f"Line {line}: invalid work_code {code!r}")
            if not edition or key in seen:
                raise ValueError(f"Line {line}: empty or duplicate edition_code {edition!r}")
            seen.add(key)
            for field in ("title", "publisher", "edition_language", "metadata_source_url", "notes"):
                if not (row.get(field) or "").strip():
                    raise ValueError(f"Line {line}: {field} is required")
            if not (row["metadata_source_url"].startswith("https://")):
                raise ValueError(f"Line {line}: metadata_source_url must use HTTPS")
            if row["candidate_state"] != "candidate_not_selected":
                raise ValueError(f"Line {line}: candidates must remain unselected until physical verification")
            try:
                year = int(row["publication_year"])
            except (ValueError, TypeError):
                raise ValueError(f"Line {line}: publication_year must be an integer")
            if not 1400 <= year <= 2200:
                raise ValueError(f"Line {line}: implausible publication_year {year}")
            isbn = (row.get("isbn") or "").strip()
            if isbn and not valid_isbn(isbn):
                raise ValueError(f"Line {line}: invalid ISBN checksum or format {isbn!r}")
            pages = (row.get("pages") or "").strip()
            if pages:
                try:
                    if int(pages) < 1:
                        raise ValueError
                except ValueError:
                    raise ValueError(f"Line {line}: pages must be a positive integer when supplied")
            count += 1
    if not count:
        raise ValueError("No edition candidates found")
    return count


if __name__ == "__main__":
    try:
        for filename in sys.argv[1:]:
            print(f"{filename}: {validate(Path(filename))} candidates validated (not selected).")
        if len(sys.argv) < 2:
            raise ValueError("Provide at least one candidate CSV")
    except Exception as error:
        print(f"EDITION CANDIDATE VALIDATION FAILED: {error}", file=sys.stderr)
        sys.exit(1)
