import json
import unittest
from pathlib import Path
from backend.services.climate_handoff import season_inputs, observation_envelope


def example():
    path = Path(__file__).resolve().parents[1] / "data/fixtures/climate-bundle.synthetic.json"
    return json.loads(path.read_text(encoding="utf-8"))


class HandoffTests(unittest.TestCase):
    def test_fixture_scenario_and_season(self):
        data = example()
        self.assertEqual(data["observation"]["data_kind"], "synthetic")
        self.assertEqual(data["rainfall_scenario"]["summary"]["baseline_rainfall_mm"], 35)
        self.assertEqual(data["rainfall_scenario"]["summary"]["scenario_rainfall_mm"], 24.5)
        self.assertEqual(data["season_inputs"]["rainfall_total_mm"], 35)

    def test_season_unknowns_and_outside_period(self):
        obs = example()["observation"]
        obs["daily"][0]["precipitation_mm_per_day"] = None
        result = season_inputs(obs, "2025-01-01", "2025-01-03")
        self.assertIsNone(result["rainfall_total_mm"])
        self.assertIsNone(result["crop_water_demand_mm"])
        self.assertEqual(result["rain_valid_days"], 2)
        with self.assertRaises(ValueError):
            season_inputs(obs, "2024-12-31", "2025-01-07")

    def test_envelope_ids_and_baseline_isolation(self):
        obs = example()["observation"]
        obs["sources"] = obs["source_refs"]
        result = observation_envelope(obs, "farm-new", "obs-new", 2)
        result["daily"][0]["temperature_c"] = 99
        self.assertEqual(obs["daily"][0]["temperature_c"], 25)
        with self.assertRaises(ValueError):
            observation_envelope(obs, "farm-new", "obs-new", True)
