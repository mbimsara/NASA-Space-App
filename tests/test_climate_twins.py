import unittest

from backend.services.climate_twins import rank_twins


def observation(farm, obs, rain, temp, period=None):
    return {"farm_id": farm, "observation_id": obs, "input_version": 1,
            "period": period or {"start": "2025-01-01", "end": "2025-01-31"},
            "requested_location": {"latitude": 8.3, "longitude": 80.4},
            "summary": {"rainfall_total_mm": rain, "mean_temperature_c": temp}}


class ClimateTwinTests(unittest.TestCase):
    def test_ranks_closest_complete_same_period_candidate(self):
        target = observation("a", "oa", 100, 25)
        twins, excluded = rank_twins(target, [observation("b", "ob", 105, 25.2), observation("c", "oc", 200, 29)])
        self.assertEqual([item["farm_id"] for item in twins], ["b", "c"])
        self.assertGreater(twins[0]["similarity_score"], twins[1]["similarity_score"])
        self.assertEqual(excluded, [])

    def test_excludes_missing_and_period_mismatch(self):
        target = observation("a", "oa", 100, 25)
        other_period = {"start": "2024-01-01", "end": "2024-01-31"}
        twins, excluded = rank_twins(target, [observation("b", "ob", None, 25), observation("c", "oc", 100, 25, other_period)])
        self.assertEqual(twins, [])
        self.assertEqual({item["reason"] for item in excluded}, {"incomplete_climate_summary", "period_mismatch"})


if __name__ == "__main__":
    unittest.main()
