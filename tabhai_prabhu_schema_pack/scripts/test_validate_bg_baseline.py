import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).with_name("validate_bg_baseline.py")
SPEC = importlib.util.spec_from_file_location("bg_baseline_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BhagavadGitaBaselineTests(unittest.TestCase):
    def test_repository_baseline_is_internally_consistent(self):
        errors = MODULE.validate(
            ROOT / "bg_chapter_inventory_baseline.csv",
            ROOT / "bg_expected_unit_inventory_provisional.csv",
        )
        self.assertEqual(errors, [])

    def test_detects_missing_reference(self):
        baseline = (ROOT / "bg_chapter_inventory_baseline.csv").read_text(encoding="utf-8")
        inventory = (ROOT / "bg_expected_unit_inventory_provisional.csv").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            base_path = Path(tmp) / "baseline.csv"
            inventory_path = Path(tmp) / "inventory.csv"
            base_path.write_text(baseline, encoding="utf-8")
            inventory_path.write_text("\n".join(inventory.splitlines()[:-1]) + "\n", encoding="utf-8")
            errors = MODULE.validate(base_path, inventory_path)
        self.assertTrue(any("not 700" in error for error in errors))

    def test_detects_wrong_verse_sequence(self):
        baseline = (ROOT / "bg_chapter_inventory_baseline.csv").read_text(encoding="utf-8")
        lines = (ROOT / "bg_expected_unit_inventory_provisional.csv").read_text(encoding="utf-8").splitlines()
        fields = lines[1].split(",")
        fields[5] = "9"
        lines[1] = ",".join(fields)
        with tempfile.TemporaryDirectory() as tmp:
            base_path = Path(tmp) / "baseline.csv"
            inventory_path = Path(tmp) / "inventory.csv"
            base_path.write_text(baseline, encoding="utf-8")
            inventory_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            errors = MODULE.validate(base_path, inventory_path)
        self.assertTrue(any("does not match reference verse" in error for error in errors))

    def test_detects_baseline_count_drift(self):
        baseline = (ROOT / "bg_chapter_inventory_baseline.csv").read_text(encoding="utf-8").replace("BG,13,BG.13,34,", "BG,13,BG.13,35,")
        inventory = (ROOT / "bg_expected_unit_inventory_provisional.csv").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            base_path = Path(tmp) / "baseline.csv"
            inventory_path = Path(tmp) / "inventory.csv"
            base_path.write_text(baseline, encoding="utf-8")
            inventory_path.write_text(inventory, encoding="utf-8")
            errors = MODULE.validate(base_path, inventory_path)
        self.assertTrue(any("not 700" in error for error in errors))
        self.assertTrue(any("Chapter 13" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
