import copy
import json
from pathlib import Path
import unittest
from backend.services.environment import build_environment


def power():
    path = Path(__file__).resolve().parents[1] / "data/fixtures/climate-bundle.synthetic.json"
    result = json.loads(path.read_text(encoding="utf-8"))["observation"]
    result["sources"] = result["source_refs"]
    return result


def smap():
    unknown = {"accepted": False, "soil_moisture_m3_m3": None, "rejection_reason": "synthetic missing pass"}
    return {"kind": "smap_surface_soil_moisture_series", "product": "SPL3SMP_E", "version": "006",
            "data_kind": "synthetic", "units": "m3/m3", "requested_point": {"latitude": 8.3, "longitude": 80.4},
            "period": {"start": "2025-01-01", "end": "2025-01-01"},
            "coverage": {"expected_days": 1, "supplied_granule_days": 1, "accepted_AM": 0, "accepted_PM": 0},
            "daily": [{"date": "2025-01-01", "granule_supplied": True, "AM": copy.deepcopy(unknown), "PM": copy.deepcopy(unknown)}]}


class EnvironmentTests(unittest.TestCase):
    def test_committed_example_rebuilds_from_its_components(self):
        path = Path(__file__).resolve().parents[1] / "data/fixtures/environment.synthetic.json"
        example = json.loads(path.read_text(encoding="utf-8"))
        source = copy.deepcopy(example["climate"]["result"]["observation"])
        source["sources"] = source["source_refs"]
        rebuilt = build_environment(source, example["farm_id"], example["observation_id"], example["input_version"],
                                    example["soil_moisture"]["result"])
        self.assertEqual(rebuilt, example)

    def test_optional_source_and_deep_copy(self):
        inputs = power()
        result = build_environment(inputs, "farm", "obs", 1)
        self.assertEqual(result["soil_moisture"]["status"], "not_supplied")
        result["climate"]["result"]["observation"]["daily"][0]["temperature_c"] = 100
        self.assertEqual(inputs["daily"][0]["temperature_c"], 25)

    def test_periods_remain_separate(self):
        result = build_environment(power(), "farm", "obs", 1, smap())
        self.assertEqual(result["climate"]["result"]["observation"]["period"]["end"], "2025-01-07")
        self.assertEqual(result["date_label_overlap"]["end"], "2025-01-01")
        self.assertEqual(result["soil_moisture"]["status"], "no_accepted_retrievals")

    def test_incompatible_source_and_false_coverage_rejected(self):
        for change in ({"version": "005"}, {"data_kind": "satellite_retrieval"},
                       {"requested_point": {"latitude": 7, "longitude": 80}},
                       {"coverage": {"expected_days": 1, "accepted_AM": 1}}):
            item = smap()
            item.update(change)
            with self.assertRaises(ValueError):
                build_environment(power(), "farm", "obs", 1, item)
        item = power()
        item["summary"]["expected_days"] = 99
        with self.assertRaises(ValueError):
            build_environment(item, "farm", "obs", 1)
