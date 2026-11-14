import copy
import unittest
from backend.services.smap_series import build_series


def record(day="20250101"):
    return {"product": "SPL3SMP_E", "version": "006", "data_kind": "satellite_retrieval",
            "requested_point": {"latitude": 8.3, "longitude": 80.4}, "max_distance_km": 15,
            "file_date_label": day, "file_name": "synthetic-test", "sha256": "synthetic-test",
            "product_version_basis": "synthetic test input, not downloaded science data",
            "passes": [{"pass": "PM", "accepted": True, "soil_moisture_m3_m3": 0.25,
                        "retrieval_quality_flag": 8, "distance_km": 4}]}


class SeriesTests(unittest.TestCase):
    def test_gaps_and_missing_passes_are_explicit(self):
        inputs = [record(), record("20250103")]
        saved = copy.deepcopy(inputs)
        result = build_series(inputs, "2025-01-01", "2025-01-03")
        self.assertEqual(result["coverage"], {"expected_days": 3, "supplied_granule_days": 2, "accepted_AM": 0, "accepted_PM": 2})
        self.assertEqual(result["daily"][1]["PM"]["rejection_reason"], "granule_not_supplied")
        self.assertEqual(inputs, saved)

    def test_duplicates_mixed_versions_and_points_rejected(self):
        for change in ({}, {"version": "005"}, {"requested_point": {"latitude": 7, "longitude": 80}}):
            other = record()
            other.update(change)
            with self.assertRaises(ValueError):
                build_series([record(), other], "2025-01-01", "2025-01-03")

    def test_rejected_value_and_outside_period_fail(self):
        item = record()
        item["passes"][0]["accepted"] = False
        with self.assertRaises(ValueError):
            build_series([item], "2025-01-01", "2025-01-03")
        with self.assertRaises(ValueError):
            build_series([record("20250104")], "2025-01-01", "2025-01-03")
