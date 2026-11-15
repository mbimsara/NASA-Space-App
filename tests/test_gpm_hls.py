import unittest
from backend.services.gpm_imerg import normalize_daily
from backend.services.hls_vegetation import normalize_observations

class SatelliteContextTests(unittest.TestCase):
    def test_gpm_preserves_gap(self):
        result = normalize_daily([{"date":"2025-01-01","precipitation_mm":2.5}], latitude=8.3, longitude=80.4,
                                 start="2025-01-01", end="2025-01-02", source_refs=["NASA GPM"])
        self.assertEqual([2.5, None], [row["precipitation_mm"] for row in result["daily"]])
        self.assertEqual(1, result["coverage"]["valid_days"])
    def test_hls_rejected_value_must_be_null(self):
        with self.assertRaises(ValueError):
            normalize_observations([{"date":"2025-01-01","product":"HLSL30","ndvi":.4,"cloud_percent":90,"quality_accepted":False}], latitude=8.3, longitude=80.4, source_refs=["NASA HLS"])
    def test_hls_keeps_products(self):
        result = normalize_observations([{"date":"2025-01-01","product":"HLSS30","ndvi":.4,"cloud_percent":5,"quality_accepted":True}], latitude=8.3, longitude=80.4, source_refs=["NASA HLS"])
        self.assertEqual("HLSS30", result["observations"][0]["product"])
if __name__ == "__main__": unittest.main()
