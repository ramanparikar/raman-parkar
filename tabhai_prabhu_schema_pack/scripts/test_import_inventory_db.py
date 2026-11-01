import os
import unittest
from pathlib import Path

import psycopg

from import_inventory import import_rows


class InventoryDatabaseIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg.connect(os.environ["DATABASE_URL"])
        with cls.conn.cursor() as cur:
            cur.execute("select id from scripture.works where code = 'BG'")
            cls.work_id = cur.fetchone()[0]
            cur.execute(
                """insert into scripture.editions (work_id, edition_code, title, edition_language)
                   values (%s, 'CI_TEST_EDITION', 'CI test edition', 'en') returning id""",
                (cls.work_id,),
            )
            cls.edition_id = cur.fetchone()[0]
            cur.execute(
                """insert into scripture.sources (edition_id, source_type, title)
                   values (%s, 'other', 'CI test inventory source') returning id""",
                (cls.edition_id,),
            )
            cls.source_id = cur.fetchone()[0]
        cls.conn.commit()

    @classmethod
    def tearDownClass(cls):
        with cls.conn.cursor() as cur:
            cur.execute("delete from scripture.units where canonical_ref = 'BG.18.999'")
            cur.execute("delete from scripture.sections where canonical_code = 'BG.18' and work_id = %s", (cls.work_id,))
            cur.execute("delete from scripture.sources where id = %s", (cls.source_id,))
            cur.execute("delete from scripture.editions where id = %s", (cls.edition_id,))
        cls.conn.commit()
        cls.conn.close()

    def test_dry_run_then_commit_adds_canonical_unit_and_edition_locator(self):
        row = {
            "work_code": "BG",
            "edition_code": "CI_TEST_EDITION",
            "section_path": "Chapter 18",
            "canonical_ref": "BG.18.999",
            "unit_kind": "verse",
            "sequence_no": 999,
            "canonical_label": "Test reference",
            "edition_section_label": "Chapter 18",
            "edition_verse_label": "999",
            "inventory_source": "CI test inventory source",
        }
        import_rows(self.conn, [row], str(self.source_id), commit=False, batch_name="CI dry-run batch")
        with self.conn.cursor() as cur:
            cur.execute("select count(*) from scripture.units where canonical_ref = 'BG.18.999'")
            self.assertEqual(cur.fetchone()[0], 0)

        import_rows(self.conn, [row], str(self.source_id), commit=True, batch_name="CI committed batch")
        with self.conn.cursor() as cur:
            cur.execute(
                """select u.canonical_ref, l.section_label, l.verse_label
                   from scripture.units u
                   join scripture.unit_locators l on l.unit_id = u.id
                   where u.canonical_ref = 'BG.18.999' and l.edition_id = %s""",
                (self.edition_id,),
            )
            self.assertEqual(cur.fetchone(), ("BG.18.999", "Chapter 18", "999"))
            cur.execute("select id from scripture.import_batches where batch_name = %s", ("CI committed batch",))
            batch = cur.fetchone()
            self.assertIsNotNone(batch)
            cur.execute("select count(*) from scripture.import_batch_items where batch_id = %s", (batch[0],))
            self.assertEqual(cur.fetchone()[0], 2)
            cur.execute("select count(*) from scripture.import_batches where batch_name = %s", ("CI dry-run batch",))
            self.assertEqual(cur.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
