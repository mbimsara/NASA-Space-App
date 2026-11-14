import unittest
from datetime import date, timedelta
from backend.services.climate_twins import rank_twins


def history(point, offset=0):
    day, rows = date(2022, 1, 1), []
    while day <= date(2023, 12, 31):
        rows.append({"date": day.isoformat(), "temperature_c": 25 + offset,
                     "precipitation_mm_per_day": 2})
        day += timedelta(days=1)
    return {"provider": "NASA POWER", "sources": ["synthetic-test"], "data_kind": "synthetic",
            "time_standard": "UTC", "coordinates": point, "daily": rows}


class TwinTests(unittest.TestCase):
    def test_distance_order_and_inputs_not_mutated(self):
        target = history([80.4, 8.3])
        result = rank_twins(target, [
            {"name": "Farther", "observations": history([81.12, 6.12], 2)},
            {"name": "Same profile", "observations": history([80.03, 9.66])}], 2022, 2023)
        self.assertEqual(result["ranked_candidates"][0]["distance"], 0)
        self.assertEqual(result["ranked_candidates"][1]["distance"], 2)
        self.assertEqual(target["daily"][0]["temperature_c"], 25)

    def test_missing_candidate_rejected_not_silently_ranked(self):
        candidate = history([81.12, 6.12])
        candidate["daily"][0]["temperature_c"] = None
        result = rank_twins(history([80.4, 8.3]), [{"name": "Incomplete", "observations": candidate}], 2022, 2023)
        self.assertEqual(result["ranked_candidates"], [])
        self.assertEqual(len(result["rejected_candidates"]), 1)

    def test_invalid_scales_and_duplicate_target(self):
        target = history([80.4, 8.3])
        with self.assertRaises(ValueError):
            rank_twins(target, [], 2022, 2023, rain_scale_mm=0)
        result = rank_twins(target, [{"name": "Self", "observations": target}], 2022, 2023)
        self.assertEqual(len(result["rejected_candidates"]), 1)
