"""Grounding checks for rotation/scenario text; no external services required."""

import copy
import json
from pathlib import Path
import unittest

from backend.app.services.assistant import explain


FIXTURE = Path(__file__).parent / "fixtures/rotation_context.synthetic.json"


class AnalysisAssistantTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def baseline_only(self):
        return {"analysis": self.context["analysis"]}

    def test_baseline_candidates_scores_sequences_and_reasons(self):
        answer = explain(self.baseline_only(), "Explain rotation candidates and rankings")
        self.assertIn("Candidate candidate-test-a: supplied rank 1; supplied score 70", answer)
        self.assertIn("Candidate candidate-test-b: supplied rank 2; supplied score 60", answer)
        self.assertIn("season 2: crop ID placeholder-crop-b", answer)
        self.assertIn("Invented first-place baseline ranking", answer)
        self.assertIn("water: value 40, weight 0.5, direction higher_is_better", answer)
        self.assertIn("test-only-no-approved-rules", answer)
        self.assertIn("not actual NASA observations", answer)
        self.assertIn("not field measurements", answer)

    def test_reports_changed_values_instead_of_hardcoded_fixture_numbers(self):
        candidate = self.context["analysis"]["candidates"][0]
        candidate.update(score=18.75, rank=9)
        candidate["water_budget"]["rainfall_mm"] = 12.25
        answer = explain(self.baseline_only(), "Explain rotation scores and water budgets")
        self.assertIn("supplied rank 9; supplied score 18.75", answer)
        self.assertIn("rainfall: 12.25 mm", answer)

    def test_water_values_units_period_and_assumption(self):
        answer = explain(self.baseline_only(), "Explain water budgets")
        for expected in ("2026-01-01 to 2026-03-31", "demand: 200 mm", "rainfall: 100 mm",
                         "effective rainfall: 80 mm", "irrigation supply: 100 mm",
                         "deficit: 20 mm", "deficit: 0 mm", "80% of rainfall"):
            with self.subTest(expected=expected):
                self.assertIn(expected, answer)
        self.assertNotIn("per season", answer)

    def test_missing_and_null_candidate_fields_are_unknown(self):
        self.context["analysis"]["candidates"] = [{"candidate_id": "incomplete", "score": None}]
        answer = explain(self.baseline_only(), "Explain rotation scores")
        for expected in ("supplied rank unknown", "supplied score unknown", "sequence: unknown",
                         "Score components: unknown", "demand: unknown", "rainfall: unknown",
                         "irrigation supply: unknown", "deficit: unknown", "period: unknown to unknown"):
            with self.subTest(expected=expected):
                self.assertIn(expected, answer)
        self.assertNotIn("0 mm", answer)

    def test_invalid_numeric_values_are_not_measurements(self):
        for value in (True, "100", float("nan"), float("inf")):
            with self.subTest(value=value):
                self.context["analysis"]["candidates"][0]["water_budget"]["rainfall_mm"] = value
                answer = explain(self.baseline_only(), "Water budget?")
                self.assertIn("rainfall: unknown", answer)

    def test_does_not_infer_ranks_from_scores_or_list_order(self):
        candidates = self.context["analysis"]["candidates"]
        for candidate in candidates:
            del candidate["rank"]
        candidates.reverse()
        answer = explain(self.baseline_only(), "Explain rankings")
        self.assertEqual(answer.count("supplied rank unknown"), 2)
        self.assertNotIn("supplied rank 1", answer)
        self.assertIn("Ranks are not inferred", answer)

    def test_explicit_selection_does_not_choose_another_candidate(self):
        context = self.baseline_only()
        context["candidate_id"] = "candidate-test-b"
        answer = explain(context, "Explain the rotation candidate")
        self.assertIn("Candidate candidate-test-b", answer)
        self.assertNotIn("Candidate candidate-test-a", answer)
        context["candidate_id"] = "not-supplied"
        answer = explain(context, "Explain the rotation candidate")
        self.assertIn("Candidate not-supplied is unknown", answer)
        self.assertNotIn("supplied score 70", answer)

    def test_empty_candidates_differ_from_missing_candidates(self):
        context = self.baseline_only()
        del context["analysis"]["candidates"]
        self.assertIn("Candidates and their rankings, scores, and water budgets are unknown",
                      explain(context, "Rotation?"))
        context["analysis"].update(candidates=[], reasons=["No eligible test crops."])
        answer = explain(context, "Rotation?")
        self.assertIn("No feasible candidates were supplied", answer)
        self.assertIn("No eligible test crops", answer)

    def test_scenario_reports_both_results_and_supplied_differences(self):
        self.context["candidate_id"] = "candidate-test-a"
        answer = explain(self.context, "Compare baseline and rainfall scenario")
        for expected in ("Hypothetical scenario scenario-synthetic-dry", "rainfall change: -30%",
                         "supplied rank 1; supplied score 70", "supplied rank 2; supplied score 55",
                         "rainfall: 100 mm", "rainfall: 70 mm", "deficit: 20 mm", "deficit: 44 mm",
                         "score difference (scenario minus baseline): -15", "deficit: 24 mm",
                         "not a rainfall observation or forecast"):
            with self.subTest(expected=expected):
                self.assertIn(expected, answer)

    def test_zero_rainfall_change_and_zero_differences_are_preserved(self):
        self.context["scenario"]["parameters"]["rainfall_change_pct"] = 0
        self.context["scenario"]["differences"][0]["score_delta"] = 0
        self.context["scenario"]["differences"][0]["water_budget"]["deficit_mm"] = 0
        answer = explain(self.context, "Scenario differences?")
        self.assertIn("Supplied rainfall change: 0%", answer)
        self.assertIn("score difference (scenario minus baseline): 0", answer)
        self.assertIn("deficit: 0 mm", answer)

    def test_missing_scenario_values_and_differences_are_not_calculated(self):
        self.context["scenario"].pop("parameters")
        self.context["scenario"].pop("differences")
        self.context["scenario"]["candidates"][0]["water_budget"]["rainfall_mm"] = None
        answer = explain(self.context, "Rainfall scenario?")
        self.assertIn("Supplied rainfall change: unknown", answer)
        self.assertIn("rainfall: unknown", answer)
        self.assertIn("Baseline differences are unknown; this service does not calculate them", answer)
        self.assertNotIn("rainfall: 0 mm", answer)

    def test_comparison_requires_loaded_matching_baseline(self):
        self.context.pop("analysis")
        answer = explain(self.context, "Compare scenario and baseline")
        self.assertIn("Baseline comparison is unknown", answer)
        self.assertNotIn("score difference (scenario minus baseline): -15", answer)

    def test_missing_baseline_link_does_not_imply_a_match(self):
        del self.context["scenario"]["baseline_analysis_id"]
        self.assertIn("Baseline comparison is unknown", explain(self.context, "Scenario?"))

    def test_conflicting_baseline_and_observation_ids_are_rejected(self):
        mutations = [
            ("scenario", "baseline_analysis_id", "other-analysis"),
            ("observations", "observation_id", "other-observation"),
            ("observations", "farm_id", "other-farm"),
        ]
        for section, key, value in mutations:
            with self.subTest(key=key):
                context = copy.deepcopy(self.context)
                context[section][key] = value
                with self.assertRaises(ValueError):
                    explain(context, "Compare rainfall scenario")

    def test_source_ids_assumptions_and_limitations_are_reported_verbatim(self):
        answer = explain(self.context, "What are the source references?")
        for section in ("analysis", "scenario", "observations"):
            for source in self.context[section]["source_refs"]:
                self.assertIn(source, answer)
            for limitation in self.context[section]["limitations"]:
                self.assertIn(limitation, answer)
        self.assertIn("All crop IDs, ranks, scores, and budgets are invented", answer)
        self.assertIn("supplied IDs only", answer)

    def test_missing_sources_do_not_borrow_references_or_invent_nasa_sources(self):
        context = self.baseline_only()
        for value in (None, []):
            with self.subTest(value=value):
                context["analysis"]["source_refs"] = value
                answer = explain(context, "Source references?")
                self.assertIn("Source references (supplied IDs only): unknown (none supplied)", answer)
                self.assertNotIn("synthetic-baseline-fixture", answer)
                self.assertNotIn("https://", answer)
        del context["analysis"]["source_refs"]
        self.assertIn("unknown (none supplied)", explain(context, "Sources?"))

    def test_provenance_is_per_record_not_inherited_from_observations(self):
        # Simulate caller-supplied provenance labels, not real retrieved NASA data.
        self.context["analysis"]["data_kind"] = "modeled"
        self.context["observations"]["data_kind"] = "observed"
        answer = explain(self.context, "Explain NASA observations and the scenario")
        self.assertIn("Model estimates, not measured NASA observations", answer)
        self.assertIn("Observed data as labeled by the supplied context", answer)
        self.assertIn("NASA origin is not independently verified", answer)
        self.assertIn("Hypothetical scenario scenario-synthetic-dry; baseline analysis ID: "
                      "analysis-synthetic-001. Synthetic test data", answer)

    def test_unknown_and_mixed_provenance_are_not_claimed_as_observed(self):
        context = self.baseline_only()
        del context["analysis"]["data_kind"]
        self.assertIn("Data kind is unknown", explain(context, "Rotation?"))
        context["analysis"]["data_kind"] = "mixed"
        self.assertIn("individual values cannot be classified", explain(context, "Rotation?"))

    def test_observation_values_have_their_own_period_and_units(self):
        context = {"observations": self.context["observations"]}
        answer = explain(context, "Explain rainfall observations")
        self.assertIn("Observation period: 2026-01-01 to 2026-03-31", answer)
        self.assertIn("rainfall: 100 mm; mean temperature: 27 Celsius", answer)
        self.assertIn("Retrieved at: unknown", answer)
        self.assertNotIn("rainfall: 70 mm", answer)

    def test_missing_observations_do_not_turn_scenario_rainfall_into_measurements(self):
        self.context.pop("observations")
        answer = explain(self.context, "Explain rainfall scenario and observations")
        self.assertIn("Observation record unknown", answer)
        self.assertIn("NASA origin cannot be established", answer)
        self.assertIn("mean temperature: unknown", answer)

    def test_new_recommendations_and_forecasts_remain_unsupported(self):
        for question in ("Recommend a rotation", "Which crop should I plant?", "Forecast rainfall"):
            with self.subTest(question=question):
                self.assertIn("information is unknown", explain(self.context, question))

    def test_combined_context_preserves_farm_answers(self):
        self.context["profile"] = {"irrigation_supply_mm_per_season": 45}
        self.assertEqual(explain(self.context, "Irrigation supply?"),
                         "Recorded irrigation supply is 45 mm per season.")

    def test_analytical_context_is_unchanged_and_answers_are_deterministic(self):
        before = copy.deepcopy(self.context)
        first = explain(self.context, "Compare rainfall scenario and rotation budgets")
        self.assertEqual(first, explain(self.context, "Compare rainfall scenario and rotation budgets"))
        self.assertEqual(before, self.context)
        self.assertEqual(self.context["observations"]["summary"]["rainfall_mm"], 100)

    def test_wrong_nested_shapes_raise_clear_type_errors(self):
        for context in ({"analysis": []}, {"analysis": {"candidates": "invalid"}},
                        {"analysis": {"source_refs": "not-a-list"}}):
            with self.subTest(context=context), self.assertRaises(TypeError):
                explain(context, "Explain rotation")


if __name__ == "__main__":
    unittest.main()
