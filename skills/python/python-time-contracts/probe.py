"""Original isolated probes; run from this directory: python -m unittest -v probe.
No network, installation, files, clock changes or external scheduling.
"""
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo
import unittest


def candidates(wall, zone):
    if wall.tzinfo is not None:
        raise ValueError("expected naive wall time")
    instants = set()
    for fold in (0, 1):
        local = wall.replace(tzinfo=zone, fold=fold)
        utc = local.astimezone(UTC)
        back = utc.astimezone(zone).replace(tzinfo=None)
        if back == wall:
            instants.add(utc)
    return sorted(instants)


class TimeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Missing data raises, not a skipped/passing test.
        cls.ny = ZoneInfo("America/New_York")

    def test_repeated_readings_collapse_as_local_keys(self):
        a = datetime(2024, 11, 3, 1, 30, tzinfo=self.ny)
        b = a.replace(fold=1)
        self.assertEqual(a, b)
        self.assertEqual(b - a, timedelta(0))
        self.assertEqual(len({a, b}), 1)  # Faulty instant-dedup baseline.
        ua, ub = a.astimezone(UTC), b.astimezone(UTC)
        self.assertEqual(ub - ua, timedelta(hours=1))
        self.assertEqual(len({ua, ub}), 2)
        self.assertLess(ua, ub)
        self.assertNotEqual(a, ua)  # Cross-zone repeated-interval exception.

    def test_zero_addition_is_not_an_instant_copy(self):
        late = datetime(2024, 11, 3, 1, 30, tzinfo=self.ny, fold=1)
        copied = late + timedelta(0)
        self.assertEqual(copied.fold, 0)
        self.assertEqual(late.astimezone(UTC) - copied.astimezone(UTC),
                         timedelta(hours=1))
        self.assertEqual(late.replace().astimezone(UTC), late.astimezone(UTC))

    def test_wall_day_and_elapsed_day_differ(self):
        start = datetime(2024, 3, 9, 12, tzinfo=self.ny)
        wall = start + timedelta(days=1)
        elapsed = (start.astimezone(UTC) + timedelta(hours=24)).astimezone(self.ny)
        self.assertEqual(wall.hour, 12)
        self.assertEqual(elapsed.hour, 13)
        self.assertEqual(wall - start, timedelta(hours=24))
        self.assertEqual(wall.astimezone(UTC) - start.astimezone(UTC),
                         timedelta(hours=23))

    def test_gap_is_not_validated_by_attachment_or_same_zone(self):
        wall = datetime(2024, 3, 10, 2, 30)
        attached = wall.replace(tzinfo=self.ny)
        self.assertIs(attached.astimezone(self.ny), attached)
        self.assertNotEqual(attached.astimezone(UTC).astimezone(self.ny)
                            .replace(tzinfo=None), wall)
        self.assertEqual(candidates(wall, self.ny), [])

    def test_fold_candidates_have_exact_expected_instants(self):
        wall = datetime(2024, 11, 3, 1, 30)
        self.assertEqual(candidates(wall, self.ny), [
            datetime(2024, 11, 3, 5, 30, tzinfo=UTC),
            datetime(2024, 11, 3, 6, 30, tzinfo=UTC)])
        self.assertEqual(candidates(wall.replace(fold=1), self.ny),
                         candidates(wall, self.ny))

    def test_ordinary_time_deduplicates_candidate_instants(self):
        self.assertEqual(candidates(datetime(2024, 2, 1, 12), self.ny),
                         [datetime(2024, 2, 1, 17, tzinfo=UTC)])

    def test_naive_contract_rejects_aware_input(self):
        with self.assertRaisesRegex(ValueError, "naive"):
            candidates(datetime(2024, 2, 1, tzinfo=UTC), self.ny)

    def test_half_hour_fold_and_gap(self):
        zone = ZoneInfo("Australia/Lord_Howe")
        choices = candidates(datetime(2024, 4, 7, 1, 45), zone)
        self.assertEqual(choices, [datetime(2024, 4, 6, 14, 45, tzinfo=UTC),
                                  datetime(2024, 4, 6, 15, 15, tzinfo=UTC)])
        self.assertEqual(candidates(datetime(2024, 10, 6, 2, 15), zone), [])

    def test_zone_identity_changes_subtraction_not_intent(self):
        a = datetime(2024, 11, 3, 1, 30, tzinfo=self.ny)
        b = datetime(2024, 11, 3, 1, 30,
                     tzinfo=ZoneInfo.no_cache("America/New_York"), fold=1)
        self.assertEqual(b - a, timedelta(hours=1))
        self.assertEqual(b.astimezone(UTC) - a.astimezone(UTC),
                         timedelta(hours=1))

    def test_wall_keys_and_unchecked_folds_are_bad_baselines(self):
        wall = datetime(2024, 11, 3, 1, 30)
        bad = {wall.replace(tzinfo=self.ny, fold=f) for f in (0, 1)}
        self.assertEqual(len(bad), 1)
        self.assertEqual(len(candidates(wall, self.ny)), 2)
        gap = datetime(2024, 3, 10, 2, 30)
        bad_gap = {gap.replace(tzinfo=self.ny, fold=f).astimezone(UTC)
                   for f in (0, 1)}
        self.assertEqual(len(bad_gap), 2)
        self.assertEqual(candidates(gap, self.ny), [])


if __name__ == "__main__":
    unittest.main()
