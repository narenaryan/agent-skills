"""Offline local-policy examples, not scanner or asset-discovery validation."""
from datetime import datetime, timedelta, timezone
import unittest


def state(observed_at, ingested_at, now, complete, budget, skew):
    """Ingestion is audit metadata; never use it to refresh collection age."""
    if budget < timedelta(0) or skew < timedelta(0):
        raise ValueError("Negative policy duration")
    for value in (observed_at, ingested_at, now):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Timezone-aware timestamps required")
    if observed_at is None:
        return "unknown"
    age = now - observed_at
    if age < -skew:
        return "invalid-time"
    if not complete:
        return "partial"
    return "fresh" if age <= budget else "stale"


class FreshnessContract(unittest.TestCase):
    def test_scenarios(self):
        now = datetime(2026, 10, 10, tzinfo=timezone.utc)
        day, skew = timedelta(days=1), timedelta(minutes=5)
        cases = [
            (now-day, True, "fresh"),
            (now-day-timedelta(seconds=1), True, "stale"),
            (now-timedelta(days=3), True, "stale"),
            (now+timedelta(hours=1), True, "invalid-time"),
            (now, False, "partial"),
            (None, True, "unknown"),
        ]
        for observed, complete, expected in cases:
            with self.subTest(expected=expected, observed=observed):
                self.assertEqual(state(observed, now, now, complete, day, skew), expected)
        with self.assertRaises(ValueError):
            state(now.replace(tzinfo=None), now, now, True, day, skew)


if __name__ == "__main__":
    unittest.main()
