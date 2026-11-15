import unittest

from pydantic import ValidationError

from backend.app.schemas.feedback import FeedbackRequest


class FeedbackContractTests(unittest.TestCase):
    def test_accepts_farmer_outcome_without_yield(self):
        item = FeedbackRequest(season_index=1, planted_on="2025-01-01", harvested_on="2025-04-01")
        self.assertIsNone(item.yield_value)

    def test_yield_requires_unit_and_dates_are_ordered(self):
        with self.assertRaises(ValidationError):
            FeedbackRequest(season_index=1, yield_value=20)
        with self.assertRaises(ValidationError):
            FeedbackRequest(season_index=1, planted_on="2025-04-01", harvested_on="2025-01-01")


if __name__ == "__main__":
    unittest.main()
