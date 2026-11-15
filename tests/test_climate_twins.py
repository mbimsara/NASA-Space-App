import unittest
from datetime import date, timedelta

from backend.services.climate_twins import rank_snapshot_twins, rank_twins


def observation(farm, obs, rain, temp, period=None):
    return {"farm_id": farm, "observation_id": obs, "input_version": 1,
            "period": period or {"start": "2025-01-01", "end": "2025-01-31"},
            "requested_location": {"latitude": 8.3, "longitude": 80.4},
            "summary": {"rainfall_total_mm": rain, "mean_temperature_c": temp}}


class ClimateTwinTests(unittest.TestCase):
    def test_ranks_closest_complete_same_period_candidate(self):
        target = observation("a", "oa", 100, 25)
        twins, excluded = rank_snapshot_twins(target, [observation("b", "ob", 105, 25.2), observation("c", "oc", 200, 29)])
        self.assertEqual([item["farm_id"] for item in twins], ["b", "c"])
        self.assertGreater(twins[0]["similarity_score"], twins[1]["similarity_score"])
        self.assertEqual(excluded, [])

    def test_excludes_missing_and_period_mismatch(self):
        target = observation("a", "oa", 100, 25)
        other_period = {"start": "2024-01-01", "end": "2024-01-31"}
        twins, excluded = rank_snapshot_twins(target, [observation("b", "ob", None, 25), observation("c", "oc", 100, 25, other_period)])
        self.assertEqual(twins, [])
        self.assertEqual({item["reason"] for item in excluded}, {"incomplete_climate_summary", "period_mismatch"})

    def test_existing_multiyear_metric_remains_available(self):
        def history(point, offset=0):
            day, rows = date(2022, 1, 1), []
            while day <= date(2023, 12, 31):
                rows.append({"date": day.isoformat(), "temperature_c": 25 + offset, "precipitation_mm_per_day": 2})
                day += timedelta(days=1)
            return {"provider": "NASA POWER", "sources": ["synthetic-test"], "data_kind": "synthetic",
                    "time_standard": "UTC", "coordinates": point, "daily": rows}
        target = history([80.4, 8.3])
        result = rank_twins(target, [{"name": "Farther", "observations": history([81.12, 6.12], 2)},
                                     {"name": "Same profile", "observations": history([80.03, 9.66])}], 2022, 2023)
        self.assertEqual([item["distance"] for item in result["ranked_candidates"]], [0, 2])


if __name__ == "__main__":
    unittest.main()
