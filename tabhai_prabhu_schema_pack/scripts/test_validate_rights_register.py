import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_rights_register.py")
SPEC = importlib.util.spec_from_file_location("rights_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

FIELDS = [
    "rights_holder","work_code","edition_code","content_type","rights_state",
    "public_display_allowed","search_indexing_allowed","embeddings_allowed",
    "ai_retrieval_allowed","redistribution_allowed","permission_reference",
    "evidence_source_title","evidence_source_url","permitted_languages",
    "starts_on","expires_on","territory","restrictions","reviewed_by","reviewed_at"
]

def row(**changes):
    value = {field: "" for field in FIELDS}
    value.update({
        "rights_holder":"Test holder","work_code":"BG","edition_code":"ED1",
        "content_type":"translation","rights_state":"permission_pending",
        "public_display_allowed":"false","search_indexing_allowed":"false",
        "embeddings_allowed":"false","ai_retrieval_allowed":"false",
        "redistribution_allowed":"false"
    })
    value.update(changes)
    return value

class RightsRegisterTests(unittest.TestCase):
    def validate_rows(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rights.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            return MODULE.validate(path)

    def test_empty_template_is_not_a_valid_register(self):
        self.assertTrue(any("no records" in e for e in MODULE.validate(Path(__file__).parents[1] / "rights_register_template.csv")))

    def test_pending_permission_cannot_enable_any_use(self):
        errors = self.validate_rows([row(public_display_allowed="true")])
        self.assertTrue(any("usage flags must remain false" in e for e in errors))

    def test_licensed_record_requires_evidence_and_review(self):
        licensed = row(
            rights_state="licensed_for_use", public_display_allowed="true",
            permission_reference="LIC-123", permitted_languages="en;sa"
        )
        errors = self.validate_rows([licensed])
        self.assertTrue(any("evidence source" in e for e in errors))
        self.assertTrue(any("reviewed_by" in e for e in errors))

    def test_complete_licensed_record_passes(self):
        licensed = row(
            rights_state="licensed_for_use", public_display_allowed="true",
            search_indexing_allowed="true", permission_reference="LIC-123",
            evidence_source_title="Signed permission letter",
            evidence_source_url="https://example.org/permission.pdf",
            permitted_languages="en;sa", reviewed_by="Rights reviewer",
            reviewed_at="2026-11-01T10:00:00Z", starts_on="2026-01-01",
            expires_on="2027-01-01"
        )
        self.assertEqual(self.validate_rows([licensed]), [])

    def test_public_domain_requires_evidence_and_review(self):
        errors = self.validate_rows([row(rights_state="public_domain_confirmed")])
        self.assertTrue(any("documented HTTPS evidence" in e for e in errors))
        self.assertTrue(any("reviewer and timestamp" in e for e in errors))

    def test_expiry_before_start_is_rejected(self):
        errors = self.validate_rows([row(starts_on="2027-01-01", expires_on="2026-01-01")])
        self.assertTrue(any("expires_on precedes" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
