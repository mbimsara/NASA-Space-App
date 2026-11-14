"""Synthetic provider-shaped inputs; no network required."""
import unittest
from backend.services.nasa_power import normalize, request_url


def fixture():
    return {
        "header": {"start": "20240228", "end": "20240301", "time_standard": "UTC",
                   "fill_value": -999, "sources": ["synthetic-test"], "api": {"version": "test"}},
        "parameters": {"T2M": {"units": "C"}, "PRECTOTCORR": {"units": "mm/day"}},
        "geometry": {"coordinates": [80.4, 8.3]},
        "properties": {"parameter": {
            "T2M": {"20240228": 0, "20240229": -999, "20240301": 30},
            "PRECTOTCORR": {"20240228": 0, "20240229": 2, "20240301": 4}}},
    }


class PowerTests(unittest.TestCase):
    def test_leap_day_and_zero_are_preserved(self):
        result = normalize(fixture(), "2024-02-28", "2024-03-01")
        self.assertEqual(result["summary"]["expected_days"], 3)
        self.assertEqual(result["summary"]["mean_temperature_c"], 15)
        self.assertEqual(result["summary"]["rainfall_total_mm"], 6)
        self.assertEqual(len(result["monthly"]), 2)
        self.assertIsNone(result["daily"][1]["temperature_c"])

    def test_absent_day_does_not_understate_total(self):
        raw = fixture()
        del raw["properties"]["parameter"]["PRECTOTCORR"]["20240229"]
        result = normalize(raw, "2024-02-28", "2024-03-01")
        self.assertIsNone(result["summary"]["rainfall_total_mm"])
        self.assertEqual(result["summary"]["rainfall_available_days_mm"], 4)

    def test_units_and_period_mismatch_fail(self):
        raw = fixture()
        raw["parameters"]["T2M"]["units"] = "K"
        with self.assertRaises(ValueError):
            normalize(raw, "2024-02-28", "2024-03-01")
        with self.assertRaises(ValueError):
            normalize(fixture(), "2024-02-27", "2024-03-01")

    def test_invalid_coordinates_and_dates(self):
        for lat, lon, start, end in [(91, 80, "2025-01-01", "2025-01-02"),
                                      (float("nan"), 80, "2025-01-01", "2025-01-02"),
                                      (8, 80, "2025-02-01", "2025-01-01")]:
            with self.assertRaises(ValueError):
                request_url(lat, lon, start, end)


if __name__ == "__main__":
    unittest.main()
