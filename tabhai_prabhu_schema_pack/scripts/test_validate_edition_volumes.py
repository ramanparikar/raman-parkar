#!/usr/bin/env python3
"""Tests for completed physical-volume verification records."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_edition_volumes import validate  # noqa: E402

FIELDS = [
    "work_code", "edition_code", "volume_number", "volume_title", "publisher",
    "place_of_publication", "edition_statement", "impression_number",
    "publication_year", "copyright_year", "isbn_or_catalogue_number",
    "total_pages", "first_section", "last_section", "first_printed_page",
    "last_printed_page", "title_page_checked", "copyright_page_checked",
    "table_of_contents_checked", "numbering_checked", "independent_checker",
    "checked_on", "physical_copy_reference", "evidence_notes",
]


def record(**changes):
    value = {
        "work_code": "SB", "edition_code": "SB_PHYSICAL_01", "volume_number": "1",
        "volume_title": "Srimad-Bhagavatam First Canto", "publisher": "Publisher",
        "place_of_publication": "Mumbai", "edition_statement": "First edition",
        "impression_number": "First impression", "publication_year": "1972",
        "copyright_year": "1972", "isbn_or_catalogue_number": "",
        "total_pages": "400", "first_section": "Canto 1 Chapter 1",
        "last_section": "Canto 1 Chapter 19", "first_printed_page": "i",
        "last_printed_page": "388", "title_page_checked": "yes",
        "copyright_page_checked": "yes", "table_of_contents_checked": "yes",
        "numbering_checked": "yes", "independent_checker": "Reviewer",
        "checked_on": "2026-11-01", "physical_copy_reference": "Library shelf ref A1",
        "evidence_notes": "Inspected physical copy; discrepancies recorded separately",
    }
    value.update(changes)
    return value


class EditionVolumeValidationTests(unittest.TestCase):
    def write(self, rows):
        f = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        self.addCleanup(Path(f.name).unlink, missing_ok=True)
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        f.close()
        return Path(f.name)

    def test_accepts_complete_physical_volume_record(self):
        self.assertEqual(validate(self.write([record()])), 1)

    def test_accepts_roman_numeral_page_labels(self):
        self.assertEqual(validate(self.write([record(first_printed_page="xii")])), 1)

    def test_rejects_missing_physical_copy_reference(self):
        with self.assertRaisesRegex(ValueError, "physical_copy_reference is required"):
            validate(self.write([record(physical_copy_reference="")]))

    def test_rejects_unchecked_copyright_page(self):
        with self.assertRaisesRegex(ValueError, "copyright_page_checked must be yes"):
            validate(self.write([record(copyright_page_checked="no")]))

    def test_rejects_unchecked_numbering(self):
        with self.assertRaisesRegex(ValueError, "numbering_checked must be yes"):
            validate(self.write([record(numbering_checked="pending")]))

    def test_rejects_duplicate_volume(self):
        with self.assertRaisesRegex(ValueError, "duplicate work/edition/volume"):
            validate(self.write([record(), record()]))

    def test_rejects_invalid_volume_page_count(self):
        with self.assertRaisesRegex(ValueError, "invalid volume number"):
            validate(self.write([record(total_pages="0")]))

    def test_rejects_future_or_malformed_check_date(self):
        for date in ("2026-13-01", "2099-01-01"):
            with self.subTest(date=date), self.assertRaisesRegex(ValueError, "checked_on"):
                validate(self.write([record(checked_on=date)]))

    def test_empty_template_is_not_a_verified_inventory(self):
        with self.assertRaisesRegex(ValueError, "No completed physical-volume"):
            validate(self.write([]))


if __name__ == "__main__":
    unittest.main()
