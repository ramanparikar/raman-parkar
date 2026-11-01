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


    def test_rejects_section_path_mismatch(self):
        with self.assertRaisesRegex(ValueError, "section_path does not agree"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,ED1,Chapter 3,BG.02.047,verse,47,Source\n"
            )

    def test_accepts_srimat_bhagavatam_section_path(self):
        rows = self.read_csv(
            "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
            "SB,ED1,Canto 1 Chapter 2,SB.01.02.006,verse,6,Source\n"
        )
        self.assertEqual(rows[0]["canonical_ref"], "SB.01.02.006")

    def test_accepts_caitanya_caritamrita_section_path(self):
        rows = self.read_csv(
            "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
            "CC,ED1,Adi-lila Chapter 2,CC.ADI.02.006,verse,6,Source\n"
        )
        self.assertEqual(rows[0]["canonical_ref"], "CC.ADI.02.006")

    def test_rejects_sequence_number_mismatch(self):
        with self.assertRaisesRegex(ValueError, "must match the canonical verse number"):
            self.read_csv(
                "work_code,edition_code,section_path,canonical_ref,unit_kind,sequence_no,inventory_source\n"
                "BG,ED1,Chapter 2,BG.02.047,verse,46,Source\n"
            )

    def test_local_database_target_allowed(self):
        MODULE.validate_database_target("postgresql://postgres:postgres@localhost:5432/scripture_test")

    def test_remote_database_blocked_by_default(self):
        with self.assertRaisesRegex(ValueError, "Remote database target blocked"):
            MODULE.validate_database_target("postgresql://user:pass@db.example.net:5432/scripture")

    def test_remote_non_supabase_target_requires_opt_in(self):
        MODULE.validate_database_target("postgresql://user:pass@db.example.net:5432/scripture", allow_remote=True)

    def test_supabase_target_always_blocked(self):
        with self.assertRaisesRegex(ValueError, "Supabase projects are blocked"):
            MODULE.validate_database_target("postgresql://postgres:pass@project.supabase.co:5432/postgres", allow_remote=True)
        with self.assertRaisesRegex(ValueError, "Supabase projects are blocked"):
            MODULE.validate_database_target("postgresql://postgres:pass@aws-0.pooler.supabase.com:6543/postgres", allow_remote=True)


if __name__ == "__main__":
    unittest.main()
