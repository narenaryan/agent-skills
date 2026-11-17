"""Independent edge probes. From this directory: python -m unittest -v independent_probe."""
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import ast
import unittest

from probe import candidates


class IndependentEdges(unittest.TestCase):
    def test_deleted_day_and_adjacent_valid_days(self):
        zone = ZoneInfo("Pacific/Apia")
        for hour in (0, 6, 12, 18, 23):
            self.assertEqual(candidates(datetime(2011, 12, 30, hour), zone), [])
        self.assertEqual(candidates(datetime(2011, 12, 29, 12), zone),
                         [datetime(2011, 12, 29, 22, tzinfo=UTC)])
        self.assertEqual(candidates(datetime(2011, 12, 31, 12), zone),
                         [datetime(2011, 12, 30, 22, tzinfo=UTC)])

    def test_gap_and_fold_microsecond_boundaries(self):
        zone = ZoneInfo("America/New_York")
        for wall, count in [
            (datetime(2024, 3, 10, 1, 59, 59, 999999), 1),
            (datetime(2024, 3, 10, 2), 0),
            (datetime(2024, 3, 10, 2, 59, 59, 999999), 0),
            (datetime(2024, 3, 10, 3), 1),
            (datetime(2024, 11, 3, 0, 59, 59, 999999), 1),
            (datetime(2024, 11, 3, 1), 2),
            (datetime(2024, 11, 3, 1, 59, 59, 999999), 2),
            (datetime(2024, 11, 3, 2), 1),
        ]:
            with self.subTest(wall=wall):
                self.assertEqual(len(candidates(wall, zone)), count)

    def test_bounded_forward_oracle(self):
        # Independent direction: enumerate actual UTC instants, then index wall labels.
        # Two 72-hour minute-grid windows, not an all-zones/history proof.
        zone = ZoneInfo("America/New_York")
        for center in (datetime(2024, 3, 10), datetime(2024, 11, 3)):
            oracle = {}
            start = (center - timedelta(days=1)).replace(tzinfo=UTC)
            for minute in range(72 * 60):
                utc = start + timedelta(minutes=minute)
                wall = utc.astimezone(zone).replace(tzinfo=None)
                oracle.setdefault(wall, []).append(utc)
            for minute in range(24 * 60):
                wall = center + timedelta(minutes=minute)
                with self.subTest(wall=wall):
                    self.assertEqual(candidates(wall, zone), oracle.get(wall, []))

    def test_literal_skill_function_matches_fixture(self):
        text = Path(__file__).with_name("SKILL.md").read_text()
        snippet = text.split("```python\n", 1)[1].split("```", 1)[0]
        snippet_ast = ast.parse(snippet)
        fixture_ast = ast.parse(Path(__file__).with_name("probe.py").read_text())
        function = lambda tree: next(n for n in tree.body
                                    if isinstance(n, ast.FunctionDef) and n.name == "candidates")
        self.assertEqual(ast.dump(function(snippet_ast)), ast.dump(function(fixture_ast)))
        namespace = {}
        exec(compile(snippet_ast, "SKILL.md recipe", "exec"), namespace)
        self.assertEqual(namespace["choices"], [datetime(2024, 11, 3, 5, 30, tzinfo=UTC),
                                                datetime(2024, 11, 3, 6, 30, tzinfo=UTC)])


if __name__ == "__main__":
    unittest.main()
