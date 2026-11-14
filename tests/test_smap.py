import unittest
from unittest.mock import patch, MagicMock
from backend.services.smap import search_url, quality_filter, discover


class SmapTests(unittest.TestCase):
    def test_documented_flags_and_missing_values(self):
        for flag in (0, 8):
            self.assertTrue(quality_filter(0.25, flag)["accepted"])
        for flag in (1, 2, 4, 9, 65534, None, True):
            self.assertIsNone(quality_filter(0.25, flag)["soil_moisture_m3_m3"])
        for value in (-9999, None, float("nan"), 1.1, 0):
            self.assertFalse(quality_filter(value, 0)["accepted"])

    def test_query_validation(self):
        url = search_url(8.3, 80.4, "2025-01-01", "2025-01-03")
        self.assertIn("SPL3SMP_E", url)
        self.assertIn("version=006", url)
        for args in [(91, 80, "2025-01-01", "2025-01-03"),
                     (8, 80, "2014-01-01", "2014-01-03")]:
            with self.assertRaises(ValueError):
                search_url(*args)

    def test_discovery_is_metadata_only_and_filters_boundary(self):
        entries = [{"id": "sample", "time_start": "2025-01-01T00:00:00Z", "links": [
            {"rel": "http://esipfed.org/ns/fedsearch/1.1/data#", "href": "https://example.test/data.h5"}]},
            {"id": "boundary", "time_start": "2025-01-04T00:00:00Z"}]
        response = MagicMock()
        response.headers = {"CMR-Hits": "2"}
        with patch("backend.services.smap.urlopen") as request, patch("backend.services.smap.json.load", return_value={"feed": {"entry": entries}}):
            request.return_value.__enter__.return_value = response
            result = discover(8.3, 80.4, "2025-01-01", "2025-01-03")
        self.assertEqual(len(result["granules"]), 1)
        self.assertEqual(result["kind"], "granule_metadata_only")
