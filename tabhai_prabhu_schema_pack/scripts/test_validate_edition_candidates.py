#!/usr/bin/env python3
"""Unit tests for metadata-only edition candidate validation."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from validate_edition_candidates import validate, valid_isbn  # noqa: E402


FIELDS = [
    "work_code", "edition_code", "title", "publisher", "publication_year",
    "edition_language", "isbn", "pages", "metadata_source_url",
    "candidate_state", "notes",
]


def row(**overrides):
    values = {
        "work_code": "BG", "edition_code": "BG_TEST", "title": "Test edition",
        "publisher": "Test publisher", "publication_year": "2000",
        "edition_language": "English", "isbn": "089213285X", "pages": "100",
        "metadata_source_url": "https://example.org/catalog",
        "candidate_state": "candidate_not_selected", "notes": "Metadata test only",
    }
    values.update(overrides)
    return values


class EditionCandidateValidationTests(unittest.TestCase):
    def write_csv(self, rows):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", suffix=".csv", delete=False)
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
        handle.close()
        return Path(handle.name)

    def test_known_catalogue_isbns_have_valid_checksums(self):
        for isbn in ("089213285X", "0892131233", "0892132752", "0912776277", "0947259066", "0957834535"):
            with self.subTest(isbn=isbn):
                self.assertTrue(valid_isbn(isbn))

    def test_accepts_valid_candidate_without_selecting_it(self):
        self.assertEqual(validate(self.write_csv([row()])), 1)

    def test_rejects_invalid_isbn_checksum(self):
        with self.assertRaisesRegex(ValueError, "invalid ISBN"):
            validate(self.write_csv([row(isbn="0892132851")]))

    def test_allows_isbn_to_be_blank_when_catalogue_does_not_supply_one(self):
        self.assertEqual(validate(self.write_csv([row(isbn="")])), 1)

    def test_rejects_nonpositive_or_noninteger_page_count(self):
        for pages in ("0", "-4", "many"):
            with self.subTest(pages=pages), self.assertRaisesRegex(ValueError, "pages must be a positive integer"):
                validate(self.write_csv([row(pages=pages)]))

    def test_rejects_selected_candidate_state(self):
        with self.assertRaisesRegex(ValueError, "must remain unselected"):
            validate(self.write_csv([row(candidate_state="selected")]))

    def test_rejects_duplicate_work_edition_pair(self):
        with self.assertRaisesRegex(ValueError, "duplicate edition_code"):
            validate(self.write_csv([row(), row()]))

    def test_rejects_non_https_catalogue_evidence(self):
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            validate(self.write_csv([row(metadata_source_url="http://example.org")]))

if __name__ == "__main__":
    unittest.main()
