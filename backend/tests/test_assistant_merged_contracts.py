"""Merged teammate contracts, with explicitly synthetic values and no providers.

Expected values come from supplied fixture records and synthetic payloads below,
never from another assistant response or a recalculated scientific result.
"""

import copy
import json
from pathlib import Path
import unittest

from backend.app.services.assistant import explain
from backend.app.services.assistant_errors import UnsupportedLanguageError
from backend.app.services.assistant_normalization import (
    normalize_context, normalize_observation, normalize_rotation, normalize_water_budget,
)
from backend.app.services.assistant_response import respond, respond_to_request


FIXTURES = Path(__file__).parent / "fixtures"


class MergedContractTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((FIXTURES / "rotation_context.synthetic.json").read_text(encoding="utf-8"))
        self.analysis = self.context["analysis"]
        self.scenario = self.context["scenario"]
        self.candidate = self.analysis["candidates"][0]
        self.identifier = self.candidate["candidate_id"]
        self.period = {"start": "2026-01-01", "end": "2026-03-31"}
        # Invented screening values, not retrieved NASA data or recommendations.
        self.budget = {
            "season_index": 1, "crop_id": self.candidate["sequence"][0]["crop_id"],
            "demand_low_mm": 500, "demand_high_mm": 800,
            "balance_low_mm": -300, "balance_high_mm": 0,
            "baseline_rainfall_mm": 500, "scenario_rainfall_mm": 400,
            "irrigation_mm": 100, "available_water_mm": 500,
            "coverage_low_percent": 62.5, "coverage_high_percent": 100,
            "period": self.period, "unit": "mm", "data_kind": "synthetic",
            "demand_basis": "seasonal_crop_water_need_etc",
            "model_version": "synthetic-water-model",
            "source_refs": ["synthetic-season-one"],
            "source_url": "https://example.invalid/synthetic-season-one",
            "assumptions": ["Synthetic total rainfall screening; effective rainfall is not modeled."],
            "limitations": ["Invented inputs, not an irrigation prescription."],
        }

    def ranges(self):
        self.candidate.pop("water_budget", None)
        self.candidate["water_budget_range"] = [copy.deepcopy(self.budget)]
        return self.candidate["water_budget_range"]

    def differences(self):
        self.scenario.pop("differences", None)
        self.scenario["baseline_differences"] = {
            candidate["candidate_id"]: {"score_change": value}
            for candidate, value in zip(self.scenario["candidates"], (-7.25, 0))
        }
        return self.scenario["baseline_differences"]

    def test_requested_and_effective_weights_are_preserved_and_explained(self):
        component = {"name": "water_sufficiency", "value": 40,
                     "requested_weight": 0.5, "effective_weight": 0.625,
                     "direction": "higher_is_better"}
        self.candidate["score_components"] = [component]
        normalized = normalize_context(self.context)
        actual = normalized["analysis"]["candidates"][0]["score_components"][component["name"]]
        self.assertEqual(actual, component)
        answer = respond(self.context, "Explain score components")["content"]
        self.assertIn("requested weight 0.5, effective weight 0.625", answer)
        self.assertNotIn("weight unknown", answer)
        self.assertNotIn("weight", actual)

    def test_unknown_and_zero_weights_are_not_derived(self):
        for requested, effective in ((None, 0), (0, None)):
            with self.subTest(requested=requested, effective=effective):
                self.candidate["score_components"] = [{
                    "name": "water_sufficiency", "value": None,
                    "requested_weight": requested, "effective_weight": effective}]
                answer = respond(self.context, "Explain score components")["content"]
                self.assertIn(f"requested weight {'unknown' if requested is None else requested}", answer)
                self.assertIn(f"effective weight {'unknown' if effective is None else effective}", answer)
                self.assertIn("water_sufficiency: value unknown", answer)

    def test_legacy_weight_can_coexist_without_relabeling(self):
        component = self.candidate["score_components"]["water"]
        component.update(requested_weight=0.3, effective_weight=0.7)
        answer = respond(self.context, "Explain score components")["content"]
        self.assertIn("requested weight 0.3, effective weight 0.7, weight 0.5", answer)

    def test_invalid_separate_weights_are_rejected(self):
        for field in ("requested_weight", "effective_weight"):
            for value in (-1, True, "0.5", float("nan"), float("inf")):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.candidate["score_components"] = [{"name": "water", field: value}]
                    normalize_context(self.context)

    def test_per_season_ranges_preserve_values_units_period_and_sources(self):
        self.ranges()
        normalized = normalize_context(self.context)
        actual = normalized["analysis"]["candidates"][0]["water_budgets"][0]
        for field, value in self.budget.items():
            self.assertEqual(actual[field], value, field)
        self.assertEqual(actual["irrigation_supply_mm"], self.budget["irrigation_mm"])
        self.assertNotIn("deficit_mm", actual)
        self.assertNotIn("effective_rainfall_mm", actual)
        response = respond({**self.context, "candidate_id": self.identifier}, "Explain water budgets")
        for field, label in (("demand_low_mm", "demand lower bound"),
                             ("demand_high_mm", "demand upper bound"),
                             ("balance_low_mm", "signed balance lower bound"),
                             ("balance_high_mm", "signed balance upper bound")):
            self.assertIn(f"{label}: {self.budget[field]} mm", response["content"])
        self.assertIn("coverage lower bound: 62.5%", response["content"])
        self.assertIn("2026-01-01 to 2026-03-31", response["content"])
        self.assertIn("effective rainfall: unknown", response["content"])
        self.assertIn("deficit: unknown", response["content"])
        self.assertIn("Synthetic test data", response["content"])
        self.assertTrue(set(self.budget["source_refs"]) <= set(response["source_ids"]))
        self.assertIn(self.budget["source_url"], response["source_ids"])
        self.assertTrue(set(self.budget["assumptions"]) <= set(response["assumptions"]))
        self.assertTrue(set(self.budget["limitations"]) <= set(response["limitations"]))

    def test_seasons_remain_separate_and_selected_sources_are_scoped(self):
        ranges = self.ranges()
        second = {**copy.deepcopy(self.budget), "season_index": 2,
                  "crop_id": self.candidate["sequence"][1]["crop_id"],
                  "demand_low_mm": 300, "demand_high_mm": 450,
                  "source_refs": ["synthetic-season-two"]}
        ranges.append(second)
        other = self.analysis["candidates"][1]
        other["water_budget_range"] = [{**copy.deepcopy(self.budget), "season_index": None,
                                       "crop_id": other["sequence"][0]["crop_id"],
                                       "source_refs": ["synthetic-unselected-budget"]}]
        answer = respond({**self.context, "candidate_id": self.identifier}, "Explain water budgets")
        for budget in (self.budget, second):
            self.assertIn(f"season index {budget['season_index']}; no aggregation", answer["content"])
            self.assertIn(f"demand lower bound: {budget['demand_low_mm']} mm", answer["content"])
            self.assertTrue(set(budget["source_refs"]) <= set(answer["source_ids"]))
        self.assertNotIn("synthetic-unselected-budget", answer["source_ids"])

    def test_optional_aggregate_does_not_replace_or_cite_season_budgets(self):
        self.ranges()
        self.candidate["water_budget"] = {"period": "3-season aggregate", "demand_mm": 9999,
                                           "source_refs": ["synthetic-aggregate"]}
        answer = respond({**self.context, "candidate_id": self.identifier}, "Explain water budgets")
        self.assertNotIn("9999", answer["content"])
        self.assertNotIn("synthetic-aggregate", answer["source_ids"])
        self.assertIn("synthetic-season-one", answer["source_ids"])

    def test_single_range_object_is_supported_without_inventing_season_index(self):
        self.candidate.pop("water_budget")
        budget = copy.deepcopy(self.budget)
        budget.pop("season_index")
        self.candidate["water_budget_range"] = budget
        normalized = normalize_context(self.context)
        candidate = normalized["analysis"]["candidates"][0]
        self.assertIsInstance(candidate["water_budget_range"], dict)
        self.assertNotIn("season_index", candidate["water_budgets"][0])
        self.assertIn("season index unknown", explain(normalized, "Explain water budgets"))

    def test_missing_range_values_and_zero_irrigation_remain_distinct(self):
        self.ranges()[0].update(demand_low_mm=None, demand_high_mm=None,
                               balance_low_mm=None, balance_high_mm=0, irrigation_mm=0)
        response = respond({**self.context, "candidate_id": self.identifier}, "Explain water budgets")
        for value in ("demand lower bound: unknown", "demand upper bound: unknown",
                      "signed balance lower bound: unknown", "signed balance upper bound: 0 mm",
                      "irrigation supply: 0 mm"):
            self.assertIn(value, response["content"])
        self.candidate["water_budget_range"] = []
        self.assertIn("Water budgets are unknown", respond(self.context, "Explain water budgets")["content"])
        self.candidate["water_budget_range"] = None
        self.assertIn("demand: unknown", respond(self.context, "Explain water budgets")["content"])

    def test_invalid_range_bindings_units_and_metadata_are_rejected(self):
        for patch in ({"season_index": 2}, {"season_index": True}, {"season_index": 0},
                      {"crop_id": "unknown-crop"}, {"unit": "m"},
                      {"demand_low_mm": 900}, {"balance_low_mm": 1},
                      {"source_refs": [None]}, {"assumptions": [False]}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.ranges()[0].update(patch)
                normalize_context(self.context)

    def test_range_aliases_are_idempotent_and_conflicts_are_rejected(self):
        self.ranges()
        normalized = normalize_context(self.context)
        self.assertEqual(normalize_context(normalized), normalized)
        self.candidate["water_budgets"] = [copy.deepcopy(self.budget)]
        normalize_context(self.context)
        self.candidate["water_budgets"][0]["balance_high_mm"] = 1
        with self.assertRaisesRegex(ValueError, "Conflicting water_budgets"):
            normalize_context(self.context)

    def test_descriptive_period_is_preserved_with_unknown_dates(self):
        for label in ("3-season aggregate", "3-season cycle"):
            with self.subTest(label=label):
                normalized = normalize_water_budget({"period": label, "demand_mm": 0})
                self.assertEqual(normalized["period"], {"label": label, "start": None, "end": None})
                self.candidate["water_budget"] = {"period": label, "demand_mm": 0}
                response = respond(self.context, "Explain water budgets")
                self.assertIn(f"period: {label}; dates: unknown to unknown", response["content"])
                self.assertTrue(any("descriptive label" in note for note in response["limitations"]))

    def test_period_label_can_accompany_only_supplied_dates(self):
        period = {"label": "Synthetic first season", "start": "2026-01-01", "end": None}
        self.candidate["water_budget"] = {"period": period}
        response = respond(self.context, "Explain water budgets")
        self.assertIn("Synthetic first season; dates: 2026-01-01 to unknown", response["content"])
        normalized = normalize_water_budget({}, period=period)
        self.assertEqual(normalized["period"], period)

    def test_period_boundary_reuses_label_without_inventing_dates(self):
        budget = normalize_water_budget({}, period="3-season aggregate")
        self.assertEqual(normalize_water_budget(budget, period="3-season aggregate"), budget)
        self.assertEqual(normalize_water_budget({}, period=self.period)["period"], self.period)
        with self.assertRaises(ValueError):
            normalize_water_budget(budget, period="another period")

    def test_labels_do_not_replace_observation_dates_or_accept_invalid_periods(self):
        observation = copy.deepcopy(self.context["observations"])
        observation["period"] = "3-season aggregate"
        with self.assertRaises(TypeError):
            normalize_observation(observation)
        for value in ("", " ", 3, {"label": 3}, {"start": "2026-02-30"}):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                normalize_water_budget({"period": value})

    def test_candidate_keyed_differences_preserve_identity_values_and_unknowns(self):
        supplied = self.differences()
        # Input mapping order deliberately differs from candidate list order.
        self.scenario["baseline_differences"] = dict(reversed(list(supplied.items())))
        for value in (-7.25, 0, None):
            with self.subTest(value=value):
                supplied[self.identifier]["score_change"] = value
                actual = normalize_context(self.context)["scenario"]["differences"]
                row = next(row for row in actual if row["candidate_id"] == self.identifier)
                self.assertEqual(row["score_delta"], value)
                self.assertEqual(row["score_change"], value)
                response = respond({**self.context, "candidate_id": self.identifier}, "Compare scenario scores")
                self.assertIn(f"supplied score difference (scenario minus baseline): {'unknown' if value is None else value}",
                              response["content"])

    def test_supplied_difference_ranks_do_not_rank_candidates(self):
        self.differences()[self.identifier].update(rank_baseline=2, rank_scenario=1)
        for record in (self.analysis, self.scenario):
            for candidate in record["candidates"]:
                candidate.pop("rank", None)
        response = respond({**self.context, "candidate_id": self.identifier}, "Compare scenario scores")
        self.assertIn("Supplied baseline rank: 2", response["content"])
        self.assertIn("Supplied scenario rank: 1", response["content"])
        self.assertIn("supplied rank unknown", response["content"])
        self.assertNotIn("supplied rank 1", response["content"])

    def test_missing_differences_are_never_subtracted_from_candidate_scores(self):
        self.scenario.pop("differences")
        answer = respond(self.context, "Compare scenario scores")["content"]
        self.assertIn("Baseline differences are unknown; this service does not calculate them", answer)

    def test_invalid_difference_ids_values_ranks_and_conflicting_aliases_fail(self):
        for patch in ({"candidate_id": "different-candidate"}, {"score_delta": 99},
                      {"score_change": True}, {"score_change": "1"},
                      {"score_change": float("inf")}, {"rank_scenario": 0}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.differences()[self.identifier].update(patch)
                normalize_context(self.context)
        self.differences()["unknown-candidate"] = {"score_change": 0}
        with self.assertRaisesRegex(ValueError, "unknown candidate"):
            normalize_context(self.context)

    def test_equivalent_difference_formats_are_idempotent_and_conflicts_fail(self):
        supplied = copy.deepcopy(self.scenario["differences"])
        self.scenario["baseline_differences"] = {
            row["candidate_id"]: {**row, "score_change": row["score_delta"]} for row in supplied}
        normalized = normalize_context(self.context)
        self.assertEqual(normalize_context(normalized), normalized)
        self.scenario["baseline_differences"][self.identifier]["score_change"] = 999
        with self.assertRaises(ValueError):
            normalize_context(self.context)

    def test_difference_mapping_keys_and_duplicate_list_ids_are_rejected(self):
        for key in (None, "", " ", 1):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.differences()[key] = {"candidate_id": self.identifier, "score_change": -7.25}
                normalize_context(self.context)
        supplied = self.differences()
        self.scenario["differences"] = [
            {"candidate_id": identifier, "score_delta": row["score_change"]}
            for identifier, row in supplied.items()]
        self.scenario["differences"].append(copy.deepcopy(self.scenario["differences"][0]))
        with self.assertRaisesRegex(ValueError, "unique"):
            normalize_context(self.context)

    def test_selected_difference_sources_and_assumptions_come_from_records(self):
        supplied = self.differences()
        for identifier, row in supplied.items():
            row.update(source_refs=[f"synthetic-difference-{identifier}"],
                       assumptions=[f"Synthetic supplied difference for {identifier}."])
        response = respond({**self.context, "candidate_id": self.identifier}, "Compare scenario scores")
        selected = supplied[self.identifier]
        self.assertTrue(set(selected["source_refs"]) <= set(response["source_ids"]))
        self.assertTrue(set(selected["assumptions"]) <= set(response["assumptions"]))
        for identifier, row in supplied.items():
            if identifier != self.identifier:
                self.assertTrue(set(row["source_refs"]).isdisjoint(response["source_ids"]))
        self.assertNotIn(self.identifier, response["source_ids"])

    def test_shehani_request_and_response_preserve_selected_range_evidence(self):
        self.ranges()
        self.differences()
        farm = json.loads((FIXTURES.parents[2] / "data/fixtures/farm.synthetic.json").read_text())
        self.context.update(id=self.analysis["farm_id"], input_version=self.analysis["input_version"], profile=farm)
        body = {"farm_id": self.analysis["farm_id"], "analysis_id": self.analysis["analysis_id"],
                "scenario_id": self.scenario["scenario_id"], "candidate_id": self.identifier,
                "language": "en", "message": "Explain baseline water budgets"}
        response = respond_to_request(body, self.context)
        self.assertEqual(response["role"], "assistant")
        self.assertIsInstance(response["content"], str)
        for field in ("source_ids", "limitations"):
            self.assertIsInstance(response[field], list)
            self.assertTrue(all(isinstance(value, str) for value in response[field]))
        self.assertIn("synthetic-season-one", response["source_ids"])
        self.assertEqual(response["context"]["candidate_id"], self.identifier)
        json.dumps(response, allow_nan=False)
        for language in ("si", "ta"):
            with self.subTest(language=language), self.assertRaises(UnsupportedLanguageError):
                respond_to_request({**body, "language": language}, self.context)

    def test_normalization_and_rendering_do_not_mutate_or_infer_results(self):
        self.ranges()
        self.differences()
        for record in (self.analysis, self.scenario):
            for candidate in record["candidates"]:
                candidate.pop("rank", None)
                candidate.pop("score", None)
        original = copy.deepcopy(self.context)
        normalized = normalize_context(self.context)
        response = respond(self.context, "show full analysis")
        self.assertEqual(self.context, original)
        self.assertEqual(normalize_context(normalized), normalized)
        for candidate in normalized["analysis"]["candidates"]:
            self.assertNotIn("rank", candidate)
            self.assertNotIn("score", candidate)
        self.assertIn("supplied rank unknown; supplied score unknown", response["content"])
        allowed_sources = set(self.analysis["source_refs"] + self.scenario["source_refs"] +
                              self.context["observations"]["source_refs"] +
                              self.budget["source_refs"] + [self.budget["source_url"]])
        self.assertTrue(set(response["source_ids"]) <= allowed_sources)


if __name__ == "__main__":
    unittest.main()
