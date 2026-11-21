"""Offline fixture: atomic closure publication against recorded evidence, not live assets."""
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest


SCHEMA = """
CREATE TABLE context (
  scope TEXT PRIMARY KEY, revision TEXT NOT NULL, observed_digest TEXT NOT NULL
);
CREATE TABLE findings (
  id TEXT PRIMARY KEY, scope TEXT NOT NULL, revision TEXT NOT NULL,
  disposition TEXT NOT NULL, validated_context TEXT, evidence_ref TEXT
);
INSERT INTO context VALUES ('fleet', 'scope-1', 'digest-b');
INSERT INTO findings VALUES ('finding-1', 'fleet', 'finding-v1', 'pending', NULL, NULL);
"""


@dataclass(frozen=True)
class Proposal:
    finding: str
    finding_revision: str
    scope: str
    context_revision: str
    evidence_ref: str


def publish(conn, proposal, new_finding_revision):
    """Caller supplies a validated proposal and a nonreused new finding token."""
    if conn.in_transaction:
        raise ValueError("use a fresh connection transaction for publication")
    if not new_finding_revision or new_finding_revision == proposal.finding_revision:
        raise ValueError("a new finding revision is required")
    if not all((proposal.finding, proposal.finding_revision, proposal.scope,
                proposal.context_revision, proposal.evidence_ref)):
        raise ValueError("a complete proof reference is required")
    # One atomic SQLite statement; callers must not treat a transaction that rolls
    # back, a busy error, or a zero-row update as a published proof.
    with conn:
        changed = conn.execute(
            """UPDATE findings
               SET disposition = 'fixed-at-snapshot', revision = ?,
                   validated_context = ?, evidence_ref = ?
               WHERE id = ? AND revision = ? AND scope = ?
                 AND disposition = 'pending'
                 AND EXISTS (SELECT 1 FROM context WHERE scope = ? AND revision = ?)""",
            (new_finding_revision, proposal.context_revision, proposal.evidence_ref,
             proposal.finding, proposal.finding_revision, proposal.scope,
             proposal.scope, proposal.context_revision),
        ).rowcount
    return changed == 1


def current_view(conn, finding):
    """Derive current reporting from both the immutable proof reference and current context."""
    row = conn.execute(
        """SELECT CASE
               WHEN f.disposition = 'fixed-at-snapshot'
                    AND (NULLIF(f.evidence_ref, '') IS NULL
                         OR NULLIF(f.validated_context, '') IS NULL
                         OR c.revision IS NOT f.validated_context) THEN 'verification-pending'
               ELSE f.disposition END
           FROM findings AS f LEFT JOIN context AS c ON c.scope = f.scope
           WHERE f.id = ?""",
        (finding,),
    ).fetchone()
    return None if row is None else row[0]


class PublicationTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        db = Path(tmp.name) / "fixture.sqlite"
        self.verifier = self.enterContext(closing(sqlite3.connect(db, timeout=1)))
        self.observer = self.enterContext(closing(sqlite3.connect(db, timeout=1)))
        self.verifier.executescript(SCHEMA)
        # Represents a successful earlier evidence join, not permission to change assets.
        self.proposal = Proposal("finding-1", "finding-v1", "fleet", "scope-1", "joined-scan")

    def change_observed(self, revision, digest):
        with self.observer:
            self.observer.execute("UPDATE context SET revision = ?, observed_digest = ?",
                                  (revision, digest))

    def test_commit_valid_review(self):
        self.assertTrue(publish(self.verifier, self.proposal, "finding-v2"))
        self.assertEqual(current_view(self.observer, "finding-1"), "fixed-at-snapshot")
        self.assertEqual(self.observer.execute(
            "SELECT validated_context, evidence_ref FROM findings").fetchone(),
            ("scope-1", "joined-scan"))

    def test_unconditional_baseline_stores_stale_proof(self):
        self.change_observed("scope-2", "digest-a")
        with self.verifier:
            self.verifier.execute(
                """UPDATE findings SET disposition = 'fixed-at-snapshot',
                       validated_context = ?, evidence_ref = ?""",
                (self.proposal.context_revision, self.proposal.evidence_ref))
        self.assertEqual(self.observer.execute(
            "SELECT disposition FROM findings").fetchone()[0], "fixed-at-snapshot")
        self.assertEqual(current_view(self.observer, "finding-1"), "verification-pending")

    def test_rollback_between_review_and_publish(self):
        self.change_observed("scope-2", "digest-a")
        self.assertFalse(publish(self.verifier, self.proposal, "finding-v2"))
        self.assertEqual(current_view(self.observer, "finding-1"), "pending")

    def test_same_digest_after_rollback_does_not_reuse_proof(self):
        self.change_observed("scope-2", "digest-a")
        self.change_observed("scope-3", "digest-b")
        self.assertFalse(publish(self.verifier, self.proposal, "finding-v2"))

    def test_disappeared_context_is_not_retirement(self):
        with self.observer:
            self.observer.execute("DELETE FROM context WHERE scope = 'fleet'")
        self.assertFalse(publish(self.verifier, self.proposal, "finding-v2"))

    def test_new_finding_disposition_is_not_overwritten(self):
        with self.observer:
            self.observer.execute("UPDATE findings SET disposition = 'accepted-risk', revision = 'risk-v2'")
        self.assertFalse(publish(self.verifier, self.proposal, "finding-v3"))
        self.assertEqual(current_view(self.observer, "finding-1"), "accepted-risk")

    def test_change_after_commit_preserves_history_without_claiming_current(self):
        self.assertTrue(publish(self.verifier, self.proposal, "finding-v2"))
        self.change_observed("scope-2", "digest-a")
        self.assertEqual(current_view(self.observer, "finding-1"), "verification-pending")
        self.assertEqual(self.observer.execute(
            "SELECT validated_context, evidence_ref FROM findings").fetchone(),
            ("scope-1", "joined-scan"))

    def test_duplicate_proposal_does_not_overwrite_history(self):
        self.assertTrue(publish(self.verifier, self.proposal, "finding-v2"))
        self.assertFalse(publish(self.verifier, self.proposal, "finding-v3"))
        self.assertEqual(self.observer.execute("SELECT revision FROM findings").fetchone()[0],
                         "finding-v2")

    def test_missing_or_malformed_fixed_marker_is_not_verification(self):
        self.assertIsNone(current_view(self.verifier, "missing-finding"))
        with self.observer:
            self.observer.execute("UPDATE findings SET disposition = 'fixed-at-snapshot'")
            self.observer.execute("DELETE FROM context")
        self.assertEqual(current_view(self.verifier, "finding-1"), "verification-pending")


if __name__ == "__main__":
    unittest.main(verbosity=2)
