"""Run from the repository root: python -m unittest discover -s backend/tests -v"""

import copy
import json
from pathlib import Path
import unittest

from backend.app.services.assistant import explain


FIXTURE = Path(__file__).resolve().parents[2] / "data/fixtures/farm.synthetic.json"


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.farm = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_irrigation_is_unknown_not_zero(self):
        answer = explain(self.farm, "How much irrigation supply is available?")
        self.assertIn("Irrigation supply is unknown", answer)
        self.assertNotIn("0 mm", answer)
        self.assertIn("synthetic demonstration inputs", answer)

    def test_fixture_soil_measurements_are_unknown(self):
        answer = explain(self.farm, "What are the soil measurements and pH?")
        self.assertIn("Soil measurements are unknown", answer)
        self.assertIn("no soil tests are recorded", answer)

    def test_missing_and_null_fields_are_unknown(self):
        for profile in ({}, {"irrigation_supply_mm_per_season": None,
                             "soil_tests": None, "location": None}):
            with self.subTest(profile=profile):
                answer = explain(profile, "Irrigation, soil measurements, area, name and location?")
                self.assertIn("Irrigation supply is unknown", answer)
                self.assertIn("Soil measurements are unknown", answer)
                self.assertIn("Farm area is unknown", answer)
                self.assertIn("Farm name: unknown", answer)
                self.assertIn("latitude unknown, longitude unknown", answer)

    def test_recorded_irrigation_preserves_value_units_and_zero(self):
        for value in (0, 125.5):
            with self.subTest(value=value):
                self.farm["irrigation_supply_mm_per_season"] = value
                answer = explain(self.farm, "IRRIGATION supply?")
                self.assertIn(f"{value} mm per season", answer)
                self.assertNotIn("unknown", answer)

    def test_recorded_soil_values_preserve_units_dates_and_unknowns(self):
        self.farm["soil_tests"] = [
            {"metric": "nitrogen", "value": 0, "unit": "mg/kg", "sampled_on": "2026-10-01"},
            {"metric": "ph", "value": None},
        ]
        answer = explain(self.farm, "What soil measurements are recorded?")
        self.assertIn("nitrogen: 0 (unit: mg/kg; sampled on: 2026-10-01)", answer)
        self.assertIn("ph: unknown (unit: unknown; sampled on: unknown)", answer)
        self.assertIn("Any soil measurement not listed here is unknown", answer)

    def test_fixture_name_area_location_and_kind(self):
        cases = [
            ("What is the farm name?", self.farm["name"]),
            ("What is the farm size?", "1.0 hectares"),
            ("Where is the farm located?", "latitude 8.3, longitude 80.4"),
            ("Is this real NASA data?", "Recorded data kind: synthetic"),
        ]
        for question, expected in cases:
            with self.subTest(question=question):
                self.assertIn(expected, explain(self.farm, question))

    def test_empty_history_does_not_claim_nothing_was_grown(self):
        self.assertIn("Crop history is unknown", explain(self.farm, "What was previously grown?"))

    def test_recorded_crop_history_does_not_invent_names_or_dates(self):
        self.farm["crop_history"] = [{"crop_id": "crop-001", "planted_on": "2026-01-01"}]
        answer = explain(self.farm, "Show crop history")
        self.assertIn("crop ID crop-001", answer)
        self.assertIn("planted: 2026-01-01; harvested: unknown", answer)

    def test_priority_weights_are_not_scores(self):
        answer = explain(self.farm, "What are my priority weights?")
        self.assertIn("water: 0.5, soil: 0.3, climate: 0.2", answer)
        self.assertIn("input weights, not measurements or rotation scores", answer)

    def test_missing_weights_and_exclusions_are_unknown(self):
        self.assertIn("water: unknown, soil: unknown, climate: unknown", explain({}, "Priorities?"))
        self.assertIn("Excluded crop IDs are unknown", explain({}, "Excluded crops?"))

    def test_exclusions_do_not_imply_suitability(self):
        self.assertIn("does not establish crop suitability", explain(self.farm, "Excluded crops?"))
        self.farm["excluded_crop_ids"] = ["crop-001"]
        self.assertIn("Recorded excluded crop IDs: crop-001", explain(self.farm, "Excluded crops?"))

    def test_unsupported_questions_do_not_fabricate_answers(self):
        questions = [
            "Which crop should I plant in this soil?",
            "Recommend a rotation based on irrigation.",
            "What rainfall is expected at this location?",
            "Give NASA source references for this farm.",
            "How much money will I earn?",
        ]
        for question in questions:
            with self.subTest(question=question):
                answer = explain(self.farm, question)
                self.assertIn("information is unknown", answer)
                self.assertIn("cannot provide crop recommendations", answer)

    def test_profile_envelope_matches_direct_profile(self):
        envelope = {"id": "farm-demo-001", "input_version": 1, "profile": self.farm}
        self.assertEqual(explain(self.farm, "Area?"), explain(envelope, "Area?"))

    def test_repeated_calls_are_deterministic_and_do_not_modify_context(self):
        before = copy.deepcopy(self.farm)
        question = "Irrigation supply and soil measurements?"
        self.assertEqual(explain(self.farm, question), explain(self.farm, question))
        self.assertEqual(self.farm, before)

    def test_unsupported_languages_are_explicit(self):
        for language in ("si", "ta", "fr"):
            with self.subTest(language=language), self.assertRaisesRegex(ValueError, "Only English"):
                explain(self.farm, "Area?", language)

    def test_invalid_inputs_have_clear_errors(self):
        for context in (None, [], {"profile": None}):
            with self.subTest(context=context), self.assertRaises(TypeError):
                explain(context, "Area?")
        with self.assertRaises(TypeError):
            explain(self.farm, None)
        with self.assertRaisesRegex(ValueError, "blank"):
            explain(self.farm, "  ")


if __name__ == "__main__":
    unittest.main()
