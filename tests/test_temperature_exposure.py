import unittest
from backend.services.temperature_exposure import temperature_exposure
from backend.services.nasa_power import normalize, request_url
from test_nasa_power import fixture


class ExposureTests(unittest.TestCase):
    def test_optional_extrema_do_not_fabricate_measurements(self):
        result = normalize(fixture(), "2024-02-28", "2024-03-01")
        self.assertEqual(result["summary"]["maximum_temperature_valid_days"], 0)
        self.assertIsNone(temperature_exposure(result)["hot_days"])

    def test_threshold_equality_missing_break_and_coverage(self):
        result = normalize(fixture(), "2024-02-28", "2024-03-01")
        for row, high, low in zip(result["daily"], [35, None, 36], [10, 9, 12]):
            row.update(temperature_max_c=high, temperature_min_c=low)
        exposure = temperature_exposure(result)
        self.assertEqual(exposure["hot_days"], 2)
        self.assertEqual(exposure["cold_nights"], 1)
        self.assertEqual(exposure["longest_observed_hot_run_days"], 1)
        self.assertTrue(exposure["hot_run_is_lower_bound"])

    def test_adapter_accepts_extrema_and_rejects_reversed_values(self):
        raw = fixture()
        raw["parameters"].update(T2M_MAX={"units": "C"}, T2M_MIN={"units": "C"})
        raw["properties"]["parameter"].update(T2M_MAX={"20240228": 5}, T2M_MIN={"20240228": -2})
        result = normalize(raw, "2024-02-28", "2024-03-01")
        self.assertEqual(result["daily"][0]["temperature_min_c"], -2)
        raw["properties"]["parameter"]["T2M_MIN"]["20240228"] = 6
        with self.assertRaises(ValueError):
            normalize(raw, "2024-02-28", "2024-03-01")
        self.assertIn("T2M_MAX", request_url(8.3, 80.4, "2025-01-01", "2025-01-02", True))
