"""Independent offline fault probes for recorded-evidence publication."""
from contextlib import closing
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from check_publish import Proposal, SCHEMA, current_view, publish


class IndependentPublicationTests(unittest.TestCase):
    def setUp(self):
        temp = self.enterContext(TemporaryDirectory())
        db = Path(temp) / "closure.sqlite"
        self.actor = self.enterContext(closing(sqlite3.connect(db, timeout=1)))
        self.peer = self.enterContext(closing(sqlite3.connect(db, timeout=1)))
        self.actor.execute("PRAGMA journal_mode=WAL").fetchone()
        self.actor.executescript(SCHEMA)
        self.proposal = Proposal("finding-1", "finding-v1", "fleet", "scope-1", "joined-scan")

    def row(self):
        return self.peer.execute(
            """SELECT revision, disposition, validated_context, evidence_ref
               FROM findings WHERE id = 'finding-1'"""
        ).fetchone()

    def test_same_revision_on_disjoint_scope_cannot_supply_missing_scope(self):
        with self.peer:
            self.peer.execute("INSERT INTO context VALUES ('unrelated', 'scope-1', 'digest-b')")
            self.peer.execute("DELETE FROM context WHERE scope = 'fleet'")
        self.assertFalse(publish(self.actor, self.proposal, "finding-v2"))
        self.assertEqual(self.row(), ("finding-v1", "pending", None, None))

    def test_scope_deletion_and_recreation_with_same_digest_cannot_resurrect_proof(self):
        self.assertTrue(publish(self.actor, self.proposal, "finding-v2"))
        expected = ("finding-v2", "fixed-at-snapshot", "scope-1", "joined-scan")
        with self.peer:
            self.peer.execute("DELETE FROM context WHERE scope = 'fleet'")
        self.assertEqual(current_view(self.peer, "finding-1"), "verification-pending")
        with self.peer:
            self.peer.execute("INSERT INTO context VALUES ('fleet', 'recreated', 'digest-b')")
        self.assertEqual(current_view(self.peer, "finding-1"), "verification-pending")
        self.assertEqual(self.row(), expected)

    def test_ticket_revision_changes_even_if_disposition_unchanged(self):
        with self.peer:
            self.peer.execute("UPDATE findings SET revision = 'independent-edit'")
        self.assertFalse(publish(self.actor, self.proposal, "finding-v2"))
        self.assertEqual(self.row(), ("independent-edit", "pending", None, None))
        fresh = Proposal("finding-1", "independent-edit", "fleet", "scope-1", "fresh-review")
        self.assertTrue(publish(self.actor, fresh, "post-review"))
        self.assertEqual(self.row(), ("post-review", "fixed-at-snapshot", "scope-1", "fresh-review"))

    def test_error_after_row_write_cannot_publish_any_part_of_proof(self):
        self.actor.executescript("""
            CREATE TRIGGER reject_proof AFTER UPDATE ON findings
            BEGIN SELECT RAISE(ABORT, 'proof publication fault'); END;
        """)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "proof publication fault"):
            publish(self.actor, self.proposal, "finding-v2")
        self.assertFalse(self.actor.in_transaction)
        self.assertEqual(self.row(), ("finding-v1", "pending", None, None))
        self.assertEqual(current_view(self.peer, "finding-1"), "pending")


if __name__ == "__main__":
    unittest.main(verbosity=2)
