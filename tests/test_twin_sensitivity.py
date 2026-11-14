import unittest
from backend.services.twin_sensitivity import sensitivity


class SensitivityTests(unittest.TestCase):
    def test_rank_reversal_and_tie_are_visible(self):
        ranking = {"reference_years": [2015, 2024], "ranked_candidates": [
            {"name": "A", "monthly_rainfall_rms_difference_mm": 100, "monthly_temperature_rms_difference_c": 0},
            {"name": "B", "monthly_rainfall_rms_difference_mm": 0, "monthly_temperature_rms_difference_c": 1}]}
        result = sensitivity(ranking, [{"rainfall_mm": r, "temperature_c": 1} for r in (50, 100, 200)])
        self.assertFalse(result["best_set_unchanged_in_tested_settings"])
        self.assertEqual(result["trials"][1]["tied_best_candidates"], ["A", "B"])
        self.assertEqual(result["trials"][0]["tied_best_candidates"], ["B"])

    def test_empty_and_invalid_settings(self):
        ranking = {"reference_years": [2015, 2024], "ranked_candidates": []}
        result = sensitivity(ranking, [{"rainfall_mm": 100, "temperature_c": 1}])
        self.assertIsNone(result["best_set_unchanged_in_tested_settings"])
        with self.assertRaises(ValueError):
            sensitivity(ranking, [{"rainfall_mm": 0, "temperature_c": 1}])
