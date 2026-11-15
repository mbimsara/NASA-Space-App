import unittest

from scripts.download_earthdata_context import PRODUCTS, search_arguments


class EarthdataDownloadTests(unittest.TestCase):
    def test_uses_exact_reviewed_products(self):
        self.assertEqual(PRODUCTS["gpm"], (("GPM_3IMERGDF", "07"),))
        self.assertEqual({name for name, _ in PRODUCTS["hls"]}, {"HLSL30", "HLSS30"})

    def test_point_query_is_bounded_and_rejects_unbounded_counts(self):
        query = search_arguments("HLSL30", "2.0", 8.3, 80.4, "2025-01-01", "2025-01-31", 20)
        self.assertEqual(query["bounding_box"], (80.399, 8.299000000000001, 80.40100000000001, 8.301))
        with self.assertRaises(ValueError):
            search_arguments("HLSL30", "2.0", 8.3, 80.4, "2025-01-01", "2025-01-31", 501)


if __name__ == "__main__":
    unittest.main()
