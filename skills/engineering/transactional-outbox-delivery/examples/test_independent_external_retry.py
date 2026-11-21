"""Independent probes for the offline external-effect fixture."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from test_external_retry import Dispatcher, LostResponse, Provider


class ObservedProvider(Provider):
    def __init__(self, path, ttl):
        super().__init__(path, ttl)
        self.lookups = []
        self.writes = []
        self.hide_committed_rows = False

    def mutate(self, scope, token, params, arrived, lose=False):
        self.writes.append((scope, token, params, arrived))
        return super().mutate(scope, token, params, arrived, lose)

    def lookup(self, scope, token):
        self.lookups.append((scope, token))
        return [] if self.hide_committed_rows else super().lookup(scope, token)


class IndependentRetryTests(unittest.TestCase):
    operation = ("order-19", "east:dispatch", '{"variant":"blue"}')

    def make_stores(self, path, deadline=15):
        token, scope, params = self.operation
        caller = Dispatcher(path / "local.db")
        provider = ObservedProvider(path / "remote.db", ttl=10)
        caller.record(token, scope, params, deadline)
        with self.assertRaises(LostResponse):
            provider.mutate(scope, token, params, 5, lose=True)
        return path / "local.db", provider

    def test_worst_case_arrival_grid_uses_entire_bounded_interval(self):
        protected_ticks = set(range(5, 15))
        cases = 0
        for now in range(10, 17):
            for delay in (0, 1, 2, 3, None):
                actual_arrivals = range(now, now + (delay or 0) + 1)
                permits_write = delay is not None and set(actual_arrivals) <= protected_ticks
                for arrived in actual_arrivals:
                    with self.subTest(now=now, delay=delay, arrived=arrived):
                        with TemporaryDirectory() as folder:
                            path, provider = self.make_stores(Path(folder))
                            outcome = Dispatcher(path).recover(
                                provider, *self.operation, now, delay, arrived=arrived)
                            self.assertEqual(outcome, ("completed", 1))
                            self.assertEqual(len(provider.writes), 2 if permits_write else 1)
                            self.assertEqual(len(provider.lookups), 0 if permits_write else 1)
                            self.assertEqual(provider.count(), 1)
                            cases += 1
        self.assertEqual(cases, 77)

    def test_committed_but_temporarily_hidden_is_not_terminal_negative(self):
        with TemporaryDirectory() as folder:
            path, provider = self.make_stores(Path(folder))
            provider.hide_committed_rows = True
            # The old effect already committed, so a proof it cannot newly
            # commit would still not be proof that it never committed.
            self.assertEqual(provider.count(), 1)
            self.assertEqual(Dispatcher(path).recover(
                provider, *self.operation, 15, None), ("unresolved", None))
            self.assertEqual(len(provider.writes), 1)
            self.assertIsNone(Dispatcher(path).intent(self.operation[0])[-1])

            provider.hide_committed_rows = False
            self.assertEqual(Dispatcher(path).recover(
                provider, *self.operation, 17, None), ("completed", 1))
            self.assertEqual(len(provider.writes), 1)
            self.assertEqual(provider.count(), 1)

    def test_early_local_cutoff_can_reconcile_without_extending_provider_window(self):
        with TemporaryDirectory() as folder:
            path, provider = self.make_stores(Path(folder), deadline=13)
            self.assertEqual(Dispatcher(path).recover(
                provider, *self.operation, 12, 1, arrived=12), ("completed", 1))
            self.assertEqual(len(provider.writes), 1)
            self.assertEqual(len(provider.lookups), 1)
            self.assertEqual(provider.count(), 1)


if __name__ == "__main__":
    unittest.main()
