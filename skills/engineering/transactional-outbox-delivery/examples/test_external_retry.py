"""Offline decision fixture: provider acceptance and caller recording are separate commits."""

import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory


class LostResponse(Exception):
    pass


class Provider:
    def __init__(self, path, ttl):
        self.path, self.ttl = path, ttl
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS effect(
                receipt INTEGER PRIMARY KEY, scope TEXT, token TEXT, params TEXT, accepted INTEGER)""")

    def mutate(self, scope, token, params, arrived, lose=False):
        with closing(sqlite3.connect(self.path)) as db, db:
            row = None if self.ttl is None else db.execute(
                """SELECT receipt, params FROM effect
                   WHERE scope=? AND token=? AND accepted>? ORDER BY receipt DESC LIMIT 1""",
                (scope, token, arrived - self.ttl),
            ).fetchone()
            if row is None:
                receipt = db.execute(
                    "INSERT INTO effect(scope, token, params, accepted) VALUES (?, ?, ?, ?)",
                    (scope, token, params, arrived),
                ).lastrowid
            else:
                receipt, previous = row
                if previous != params:
                    raise ValueError("changed parameters")
        if lose:
            raise LostResponse
        return receipt

    def lookup(self, scope, token):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute(
                "SELECT receipt, params FROM effect WHERE scope=? AND token=? ORDER BY receipt",
                (scope, token),
            ).fetchall()

    def count(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT count(*) FROM effect").fetchone()[0]


class Dispatcher:
    def __init__(self, path):
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS intent(
                token TEXT PRIMARY KEY, scope TEXT, params TEXT,
                deadline INTEGER, receipt INTEGER)""")

    def record(self, token, scope, params, until):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("INSERT INTO intent VALUES (?, ?, ?, ?, NULL)", (token, scope, params, until))

    def intent(self, token):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute("SELECT scope, params, deadline, receipt FROM intent WHERE token=?",
                              (token,)).fetchone()

    def complete(self, token, receipt):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE intent SET receipt=? WHERE token=?", (receipt, token))
        return "completed", receipt

    def recover(self, provider, token, scope, params, now, max_delay, *, arrived=None):
        expected_scope, expected_params, until, receipt = self.intent(token)
        if (scope, params) != (expected_scope, expected_params):
            return "intent_mismatch", None
        if receipt is not None:
            return "completed", receipt
        if (until is not None and max_delay is not None and max_delay >= 0
                and now + max_delay < until):
            arrival = now if arrived is None else arrived
            if not now <= arrival <= now + max_delay:
                raise ValueError("fixture violates stipulated arrival bound")
            return self.complete(token, provider.mutate(scope, token, params, arrival))
        matches = provider.lookup(scope, token)
        if len(matches) == 1 and matches[0][1] == params:
            return self.complete(token, matches[0][0])
        return "unresolved", None


class ExternalRetryTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.local = Path(directory.name, "local.db")
        self.remote = Path(directory.name, "remote.db")
        self.provider = Provider(self.remote, ttl=10)
        self.dispatcher = Dispatcher(self.local)
        self.dispatcher.record("op-1", "account-a:create", "blue", 10)

    def lose_receipt(self):
        with self.assertRaises(LostResponse):
            self.provider.mutate("account-a:create", "op-1", "blue", 0, lose=True)
        self.assertIsNone(self.dispatcher.intent("op-1")[-1])

    def recover(self, now, delay):
        return Dispatcher(self.local).recover(
            self.provider, "op-1", "account-a:create", "blue", now, delay)

    def test_lost_response_then_same_intent_retry(self):
        self.lose_receipt()
        self.assertEqual(self.recover(2, 1), ("completed", 1))
        self.assertEqual(self.recover(100, None), ("completed", 1))
        self.assertEqual(self.provider.count(), 1)

    def test_always_retry_baseline_duplicates_at_expiry(self):
        self.lose_receipt()
        self.assertEqual(self.provider.mutate("account-a:create", "op-1", "blue", 10), 2)
        self.assertEqual(self.provider.count(), 2)

    def test_reconcile_at_expiry_without_writing(self):
        self.lose_receipt()
        self.assertEqual(self.recover(10, 1), ("completed", 1))
        self.assertEqual(self.provider.count(), 1)

    def test_arrival_bound_not_launch_time_controls_retry(self):
        self.assertEqual(self.recover(9, 1), ("unresolved", None))
        self.assertEqual(self.provider.count(), 0)

    def test_missing_before_late_commit_does_not_send_again(self):
        self.assertEqual(self.recover(10, None), ("unresolved", None))
        self.provider.mutate("account-a:create", "op-1", "blue", 11)
        self.assertEqual(self.recover(12, None), ("completed", 1))
        self.assertEqual(self.provider.count(), 1)

    def test_request_scope_or_parameters_cannot_drift(self):
        self.lose_receipt()
        for scope, params in [("account-b:create", "blue"), ("account-a:create", "red")]:
            with self.subTest(scope=scope, params=params):
                self.assertEqual(self.dispatcher.recover(
                    self.provider, "op-1", scope, params, 2, 1), ("intent_mismatch", None))
        self.assertEqual(self.provider.count(), 1)

    def test_absent_dedup_cannot_authorize_a_retry(self):
        self.dispatcher.record("other-op", "account-a:create", "blue", None)
        provider = Provider(self.remote, ttl=None)
        self.assertEqual(self.dispatcher.recover(
            provider, "other-op", "account-a:create", "blue", 1, 0), ("unresolved", None))
        self.assertEqual(provider.count(), 0)

    def test_duplicate_provider_matches_remain_unresolved(self):
        self.lose_receipt()
        self.provider.mutate("account-a:create", "op-1", "blue", 10)
        self.assertEqual(self.recover(11, None), ("unresolved", None))
        self.assertEqual(self.provider.count(), 2)


if __name__ == "__main__":
    unittest.main()
