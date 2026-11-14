import unittest
from datetime import date, timedelta
from backend.services.climate_baseline import compare_monthly


def series():
    day = date(2022, 1, 1)
    rows = []
    while day <= date(2024, 12, 31):
        rows.append({"date": day.isoformat(), "temperature_c": day.year - 2000,
                     "precipitation_mm_per_day": 2 if day.year == 2024 else 1})
        day += timedelta(days=1)
    return {"provider": "NASA POWER", "daily": rows}


class BaselineTests(unittest.TestCase):
    def test_reference_excludes_target_and_handles_leap_month(self):
        result = compare_monthly(series(), 2022, 2023, 2024)
        jan, feb = result["monthly"][:2]
        self.assertEqual(jan["rainfall_difference_pct"], 100)
        self.assertEqual(jan["temperature_difference_c"], 1.5)
        self.assertEqual(feb["target_rainfall_mm"], 58)
        self.assertEqual(feb["reference_rainfall_mm"], 28)

    def test_partial_and_missing_months_are_not_averaged(self):
        data = series()
        data["daily"] = data["daily"][1:]
        result = compare_monthly(data, 2022, 2023, 2024)["monthly"][0]
        self.assertIsNone(result["reference_rainfall_mm"])
        self.assertEqual(result["rain_reference_years"], [2023])
        data = series()
        data["daily"][0]["precipitation_mm_per_day"] = None
        result = compare_monthly(data, 2022, 2023, 2024)["monthly"][0]
        self.assertIsNone(result["rainfall_difference_pct"])
        self.assertIsNotNone(result["reference_mean_temperature_c"])

    def test_zero_reference_has_no_percentage(self):
        data = series()
        for row in data["daily"]:
            row["precipitation_mm_per_day"] = 0
        self.assertIsNone(compare_monthly(data, 2022, 2023, 2024)["monthly"][0]["rainfall_difference_pct"])

    def test_invalid_reference_rejected(self):
        for start, end, target in [(2022, 2023, 2023), (2023, 2022, 2024), (2022, 2022, 2024)]:
            with self.assertRaises(ValueError):
                compare_monthly(series(), start, end, target)
