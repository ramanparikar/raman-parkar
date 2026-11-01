import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("import_inventory.py")
SPEC = importlib.util.spec_from_file_location("inventory_importer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InventoryImporterTests(unittest.TestCase):
    def read_csv(self, body):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
        try:
            handle.write(body)
            handle.close()
            return MODULE.read_inventory(Path(handle.name))
        finally:
            Path(handle.name).unlink(missing_ok=True)

    def test_accepts_named_edition_and_source(self):
        rows = self.read_csv(
            "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
            "BG,ASITAISEDITION,Chapter 2,BG.02.047,verse,47,Print edition page list\n"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sequence_no"], 47)

    def test_rejects_provisional_edition(self):
        with self.assertRaisesRegex(ValueError, "real, named edition"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,PROVISIONAL_BASELINE,Chapter 2,BG.02.047,verse,47,Unverified\n"
            )

    def test_rejects_duplicate_canonical_reference(self):
        with self.assertRaisesRegex(ValueError, "duplicate canonical reference"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,ED1,Chapter 2,BG.02.047,verse,47,Source\n"
                "BG,ED1,Chapter 2,BG.02.047,verse,48,Source\n"
            )

    def test_rejects_bad_reference_shape(self):
        with self.assertRaisesRegex(ValueError, "invalid canonical reference"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,ED1,Chapter 2,BG.2.47,verse,47,Source\n"
            )

    def test_rejects_unknown_unit_kind(self):
        with self.assertRaisesRegex(ValueError, "unsupported unit_kind"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,ED1,Chapter 2,BG.02.047,unknown,47,Source\n"
            )


if __name__ == "__main__":
    unittest.main()
