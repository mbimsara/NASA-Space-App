import copy
import unittest
from backend.services.climate import historical_indicators, rainfall_scenario


def example(rains=(0, 0.5, None, 0, 20)):
    return {"provider": "NASA POWER", "daily": [
        {"date": f"2025-01-{i:02}", "precipitation_mm_per_day": rain, "temperature_c": 30}
        for i, rain in enumerate(rains, 1)]}


class ClimateTests(unittest.TestCase):
    def test_unknown_breaks_run_and_thresholds_are_explicit(self):
        result = historical_indicators(example())
        self.assertEqual(result["dry_days"], 3)
        self.assertEqual(result["longest_observed_dry_run_days"], 2)
        self.assertTrue(result["dry_run_is_lower_bound"])
        self.assertEqual(result["high_rain_days"], 1)
        self.assertEqual(result["warm_daily_mean_days"], 5)

    def test_scenario_preserves_baseline_and_unknowns(self):
        baseline = example()
        saved = copy.deepcopy(baseline)
        result = rainfall_scenario(baseline, -30)
        self.assertEqual(baseline, saved)
        self.assertIsNone(result["summary"]["scenario_rainfall_mm"])
        self.assertIsNone(result["daily"][2]["scenario_mm_per_day"])
        self.assertEqual(result["daily"][4]["scenario_mm_per_day"], 14)

    def test_complete_total_and_extreme_scenarios(self):
        baseline = example((0, 10, 20))
        self.assertEqual(rainfall_scenario(baseline, -30)["summary"]["difference_mm"], -9)
        self.assertEqual(rainfall_scenario(baseline, -100)["summary"]["scenario_rainfall_mm"], 0)
        self.assertEqual(rainfall_scenario(baseline, 0)["summary"]["scenario_rainfall_mm"], 30)

    def test_all_missing_is_unknown_not_zero(self):
        result = historical_indicators(example((None, None)))
        self.assertIsNone(result["dry_days"])
        self.assertIsNone(result["longest_observed_dry_run_days"])

    def test_invalid_inputs_fail(self):
        for change in (-101, float("nan"), True):
            with self.assertRaises(ValueError):
                rainfall_scenario(example(), change)
        data = example()
        data["daily"][1]["date"] = "2025-01-03"
        with self.assertRaises(ValueError):
            historical_indicators(data)
        with self.assertRaises(ValueError):
            historical_indicators(example(), dry_below_mm=20, rain_at_or_above_mm=10)


if __name__ == "__main__":
    unittest.main()
