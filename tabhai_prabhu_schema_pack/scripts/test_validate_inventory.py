import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_inventory.py")
SPEC = importlib.util.spec_from_file_location("inventory_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InventoryValidatorTests(unittest.TestCase):
    def write_csv(self, sequence_no, canonical_ref="BG.02.047"):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False)
        handle.write(
            "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
            f"BG,EDITION_A,Chapter 2,{canonical_ref},verse,{sequence_no},Physical copy contents page\n"
        )
        handle.close()
        return Path(handle.name)

    def test_accepts_matching_canonical_sequence(self):
        path = self.write_csv(47)
        try:
            self.assertEqual(MODULE.validate(path), [])
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_mismatched_canonical_sequence(self):
        path = self.write_csv(46)
        try:
            errors = MODULE.validate(path)
            self.assertTrue(any("must match the canonical verse number 47" in error for error in errors))
        finally:
            path.unlink(missing_ok=True)

    def test_rejects_malformed_reference(self):
        path = self.write_csv(47, "BG.2.47")
        try:
            errors = MODULE.validate(path)
            self.assertTrue(any("does not match BG reference format" in error for error in errors))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
