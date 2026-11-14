"""Offline compatibility with pinned teammate contracts, not live NASA tests.

Dataclass fields below mirror Bhagya's 454b4c1 public output shapes; values are
invented test examples. No teammate application, model calculator or SDK runs.
"""

import copy
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import unittest

from backend.app.services.assistant import explain
from backend.app.services.assistant_normalization import (
    normalize_context, normalize_observation, normalize_rainfall_scenario,
    normalize_rotation, normalize_water_budget,
)
from backend.app.services.assistant_response import respond


@dataclass(frozen=True, slots=True)
class RotationCandidate:
    crop_ids: tuple
    reasons: tuple
    constraint_checks: tuple


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    candidates: tuple
    reasons: tuple


@dataclass(frozen=True, slots=True)
class WaterBudget:
    crop_demand_mm: float
    baseline_rainfall_mm: float
    scenario_rainfall_mm: float
    irrigation_mm: float
    available_water_mm: float
    balance_mm: float
    coverage_percent: float
    assumptions: tuple


@dataclass(frozen=True, slots=True)
class WaterBudgetRange:
    crop_id: str
    demand_low_mm: float
    demand_high_mm: float
    baseline_rainfall_mm: float
    scenario_rainfall_mm: float
    irrigation_mm: float
    available_water_mm: float
    balance_low_mm: float
    balance_high_mm: float
    coverage_low_percent: float
    coverage_high_percent: float
    demand_basis: str
    model_version: str
    assumptions: tuple


@dataclass(frozen=True, slots=True)
class WaterDemandRange:
    crop_id: str
    low_mm: float
    high_mm: float
    nominal_mm: float
    basis: str
    model_version: str
    source_url: str
    limitations: tuple


FIXTURES = Path(__file__).parent / "fixtures"


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.bundle = json.loads((FIXTURES / "teammate-climate.synthetic.json").read_text(encoding="utf-8"))["climate_bundle"]
        self.observation = self.bundle["observation"]
        self.result = CandidateGenerationResult((
            RotationCandidate(("rice", "maize", "rice"), ("Synthetic feasibility report.",),
                              ("Synthetic eligibility check.",)),
            RotationCandidate(("maize", "rice", "maize"), ("Another synthetic feasibility report.",), ()),
        ), ())
        self.ids = ["boundary-option-a", "boundary-option-b"]
        self.metadata = {"analysis_id": "synthetic-boundary-analysis", "data_kind": "synthetic",
                         "source_refs": ["synthetic-team-fixture"], "catalog_version": "synthetic-catalog",
                         "limitations": ["Invented output shapes, not validated farm advice."]}
        self.period = {"start": "2026-05-01", "end": "2026-08-31"}
        self.scalar = WaterBudget(600, 500, 400, 100, 500, -100, 83.333333,
                                  ("Synthetic budget: effective rainfall is not modeled.",))
        self.range = WaterBudgetRange("maize", 500, 800, 500, 400, 100, 500,
                                     -300, 0, 62.5, 100, "seasonal_crop_water_need_etc",
                                     "synthetic-water-model", ("Synthetic ETc screening range, not gross irrigation delivery.",))

    def rotation(self, **options):
        return normalize_rotation(self.result, candidate_ids=self.ids, metadata=self.metadata, **options)

    def water(self, value=None, **options):
        return normalize_water_budget(value or self.scalar, period=self.period,
                                      metadata={"data_kind": "synthetic", **options})

    def test_domain_dataclasses_preserve_order_and_constraints(self):
        actual = self.rotation()
        first = actual["candidates"][0]
        self.assertEqual([s["crop_id"] for s in first["sequence"]], list(self.result.candidates[0].crop_ids))
        self.assertEqual([s["season_index"] for s in first["sequence"]], [1, 2, 3])
        self.assertEqual(first["candidate_id"], self.ids[0])
        self.assertEqual(first["constraint_checks"][0]["rule"], self.result.candidates[0].constraint_checks[0])
        self.assertIsNone(first["constraint_checks"][0]["passed"])

    def test_no_candidate_ids_are_generated(self):
        with self.assertRaisesRegex(ValueError, "Stable candidate IDs"):
            normalize_rotation(self.result)

    def test_id_count_duplicates_and_conflicts_are_rejected(self):
        for identifiers in (["only-one"], ["same", "SAME"], ["", "other"]):
            with self.subTest(ids=identifiers), self.assertRaises(ValueError):
                normalize_rotation(self.result, candidate_ids=identifiers)
        with self.assertRaises(ValueError):
            normalize_rotation({"candidates": [{"candidate_id": "original"}]}, candidate_ids=["replacement"])

    def test_unranked_candidates_have_no_manufactured_scores_or_ranks(self):
        actual = self.rotation()
        for candidate in actual["candidates"]:
            self.assertNotIn("rank", candidate)
            self.assertNotIn("score", candidate)
        answer = explain({"analysis": actual}, "Explain rankings")
        self.assertIn("unranked", answer)
        self.assertIn("supplied score unknown", answer)
        self.assertNotIn("supplied rank 1", answer)

    def test_constraints_are_explained_without_invented_pass_status(self):
        answer = explain({"analysis": self.rotation()}, "Explain constraint checks")
        self.assertIn(self.result.candidates[0].constraint_checks[0], answer)
        self.assertIn("unknown", answer)
        self.assertNotIn("supplied score", answer)
        self.assertNotIn("Water budget period", answer)

    def test_structured_failed_constraint_and_note_are_preserved(self):
        analysis = normalize_rotation({"candidates": [{"candidate_id": "chosen", "constraint_checks": [
            {"rule": "Synthetic water condition", "passed": False, "note": "Synthetic missing input"}
        ]}]})
        answer = explain({"analysis": analysis}, "Explain constraints")
        self.assertIn("Synthetic water condition: failed", answer)
        self.assertIn("Synthetic missing input", answer)

    def test_scalar_water_aliases_preserve_signed_balance(self):
        actual = self.water()
        self.assertEqual(actual["demand_mm"], self.scalar.crop_demand_mm)
        self.assertEqual(actual["irrigation_mm"], self.scalar.irrigation_mm)
        self.assertEqual(actual["irrigation_supply_mm"], self.scalar.irrigation_mm)
        self.assertEqual(actual["balance_mm"], self.scalar.balance_mm)
        self.assertNotIn("deficit_mm", actual)
        self.assertNotIn("effective_rainfall_mm", actual)
        self.assertEqual(actual["period"], self.period)

    def test_range_bounds_basis_version_and_zero_are_preserved(self):
        actual = self.water(self.range)
        for key in ("demand_low_mm", "demand_high_mm", "balance_low_mm", "balance_high_mm",
                    "demand_basis", "model_version", "coverage_low_percent", "coverage_high_percent"):
            self.assertEqual(actual[key], getattr(self.range, key))
        self.assertNotIn("demand_mm", actual)
        self.assertNotIn("deficit_mm", actual)

    def test_demand_only_range_does_not_use_nominal_as_scalar(self):
        demand = WaterDemandRange("rice", 450, 700, 575, "seasonal_crop_water_need_etc", "test-range",
                                  "https://example.invalid/synthetic-reference", ("Synthetic example only.",))
        actual = normalize_water_budget(demand)
        self.assertEqual((actual["demand_low_mm"], actual["demand_high_mm"]), (demand.low_mm, demand.high_mm))
        self.assertEqual(actual["nominal_mm"], demand.nominal_mm)
        self.assertNotIn("demand_mm", actual)
        self.assertIsNone(actual["period"]["start"])
        self.assertEqual(actual["source_url"], demand.source_url)

    def test_per_season_budgets_are_explicitly_bound_not_aggregated(self):
        budget = self.water(self.range, season_index=2, source_refs=["synthetic-water-range"])
        actual = self.rotation(water_budgets={self.ids[0]: [budget]})
        answer = explain({"analysis": actual, "candidate_id": self.ids[0]}, "Explain signed balances and water demand ranges")
        for expected in ("season index 2", "crop ID maize", "no aggregation", "500 mm", "800 mm", "-300 mm", "0 mm"):
            self.assertIn(expected, answer)
        self.assertIn("effective rainfall: unknown", answer)
        self.assertIn("deficit: unknown", answer)
        self.assertIn(self.range.model_version, answer)
        self.assertIn(self.range.assumptions[0], answer)
        self.assertNotIn("80%", answer)

    def test_explicit_budget_binding_rejects_unknown_ids_or_wrong_step(self):
        with self.assertRaises(ValueError):
            self.rotation(water_budgets={"unknown": self.water()})
        with self.assertRaises(ValueError):
            self.rotation(water_budgets={self.ids[0]: [self.water(self.range, season_index=1)]})

    def test_invalid_water_values_ranges_units_and_periods_are_rejected(self):
        cases = ({"demand_low_mm": 800, "demand_high_mm": 500},
                 {"balance_low_mm": 0, "balance_high_mm": -300},
                 {"irrigation_mm": -1}, {"crop_demand_mm": True},
                 {"balance_mm": float("nan")}, {"unit": "liters"},
                 {"period": {"start": "2026-08-31", "end": "2026-05-01"}},
                 {"period": " "}, {"period": 3})
        for case in cases:
            with self.subTest(case=case), self.assertRaises((TypeError, ValueError)):
                normalize_water_budget(case)

    def test_water_unknowns_are_preserved_not_zero_filled(self):
        actual = normalize_water_budget({"irrigation_mm": None, "balance_mm": None})
        self.assertIsNone(actual["irrigation_supply_mm"])
        self.assertIsNone(actual["balance_mm"])
        self.assertNotIn("deficit_mm", actual)

    def test_water_alias_conflicts_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_water_budget({"crop_demand_mm": 500, "demand_mm": 600})

    def test_matheesha_observation_aliases_complete_total(self):
        actual = normalize_observation(self.observation)
        self.assertEqual(actual["summary"]["rainfall_mm"], self.observation["summary"]["rainfall_total_mm"])
        self.assertEqual(actual["coverage"], self.observation["coverage"])
        self.assertEqual(actual["data_kind"], "synthetic")
        self.assertEqual(actual["source_refs"], self.observation["source_refs"])

    def test_raw_normalizer_shape_uses_sources_and_summary_dates(self):
        raw = copy.deepcopy(self.observation)
        raw["sources"] = raw.pop("source_refs")
        raw.pop("period")
        raw.pop("coverage")
        actual = normalize_observation(raw)
        self.assertEqual(actual["period"], self.observation["period"])
        self.assertEqual(actual["source_refs"], self.observation["source_refs"])

    def test_null_complete_total_does_not_use_partial_sum(self):
        raw = copy.deepcopy(self.observation)
        raw["summary"]["rainfall_total_mm"] = None
        raw["summary"]["precipitation_valid_days"] -= 1
        raw["coverage"]["precipitation_valid_days"] -= 1
        actual = normalize_observation(raw)
        self.assertIsNone(actual["summary"]["rainfall_mm"])
        self.assertEqual(actual["summary"]["rainfall_available_days_mm"], raw["summary"]["rainfall_available_days_mm"])
        response = respond({"observations": actual}, "Explain observations")
        self.assertIn("rainfall: unknown", response["content"])
        self.assertEqual(response["status"], "insufficient_context")

    def test_dulanjaya_alias_and_json_model_protocol(self):
        raw = copy.deepcopy(self.observation)
        raw["summary"]["rainfall_mm"] = raw["summary"]["rainfall_total_mm"]
        raw["coverage"]["available_days"] = raw["coverage"]["expected_days"]
        raw["units"] = {"rainfall_mm": "mm", "mean_temperature_c": "C"}

        class ModelDump:
            def model_dump(self, *, mode):
                if mode != "json":
                    raise AssertionError("Expected JSON-mode serialization")
                return raw

        actual = normalize_observation(ModelDump())
        self.assertEqual(actual["summary"]["rainfall_mm"], raw["summary"]["rainfall_mm"])
        self.assertIsNot(actual, raw)

    def test_observation_conflicting_aliases_are_rejected(self):
        raw = copy.deepcopy(self.observation)
        raw["summary"]["rainfall_mm"] = 999
        with self.assertRaises(ValueError):
            normalize_observation(raw)

    def test_incomplete_coverage_with_known_total_is_rejected(self):
        raw = copy.deepcopy(self.observation)
        raw["coverage"]["precipitation_valid_days"] -= 1
        raw["summary"]["precipitation_valid_days"] -= 1
        with self.assertRaises(ValueError):
            normalize_observation(raw)

    def test_observation_units_coverage_and_dates_are_validated(self):
        for changes in ({"units": {"rainfall_total_mm": "mm/day"}},
                        {"coverage": {"expected_days": 7, "precipitation_valid_days": 8}},
                        {"period": {"start": "2025-01-02", "end": "2025-01-07"}}):
            raw = copy.deepcopy(self.observation)
            raw.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                normalize_observation(raw)

    def test_date_objects_become_iso_dates_without_period_invention(self):
        actual = normalize_water_budget({}, period={"start": date(2026, 5, 1), "end": date(2026, 8, 31)})
        self.assertEqual(actual["period"], self.period)

    def test_full_climate_bundle_normalization_and_explanation(self):
        actual = normalize_context(self.bundle)
        self.assertEqual(actual["observations"]["summary"]["rainfall_mm"], self.observation["summary"]["rainfall_total_mm"])
        answer = explain(actual, "What happens if rainfall decreases?")
        scenario = self.bundle["rainfall_scenario"]
        for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm"):
            self.assertIn(f"{scenario['summary'][key]} mm", answer)
        self.assertIn("Rainfall-only hypothetical", answer)
        self.assertIn("not a measurement or forecast", answer)
        self.assertNotIn("supplied score", answer)
        self.assertNotIn("Candidate unknown", answer)

    def test_rainfall_only_scenario_has_no_fabricated_ids_or_candidates(self):
        actual = normalize_context(self.bundle)["scenario"]
        self.assertNotIn("scenario_id", actual)
        self.assertNotIn("analysis_id", actual)
        self.assertNotIn("candidates", actual)
        self.assertEqual(actual["data_kind"], "synthetic")
        self.assertEqual(actual["period"], self.observation["period"])
        self.assertEqual(actual["source_refs"], self.observation["source_refs"])

    def test_rainfall_scenario_standalone_missing_provenance_stays_unknown(self):
        actual = normalize_rainfall_scenario(self.bundle["rainfall_scenario"])
        self.assertNotIn("data_kind", actual)
        self.assertEqual(actual["source_refs"], [])
        answer = explain({"scenario": actual}, "Explain rainfall scenario")
        self.assertIn("Data kind is unknown", answer)
        self.assertIn("unknown to unknown", answer)

    def test_zero_and_missing_rainfall_differences_are_preserved(self):
        for value in (0, None):
            raw = copy.deepcopy(self.bundle["rainfall_scenario"])
            raw["summary"]["difference_mm"] = value
            response = respond({"scenario": raw}, "Explain rainfall scenario")
            expected = "0 mm" if value == 0 else "unknown"
            self.assertIn(f"supplied difference (scenario minus baseline): {expected}", response["content"])
            self.assertEqual(response["status"], "answered" if value == 0 else "insufficient_context")

    def test_rainfall_baseline_provenance_and_total_conflicts_are_rejected(self):
        for metadata in ({"data_kind": "modeled"}, {"period": self.period}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                normalize_rainfall_scenario(self.bundle["rainfall_scenario"], observation=self.observation, metadata=metadata)
        raw = copy.deepcopy(self.bundle["rainfall_scenario"])
        raw["summary"]["baseline_rainfall_mm"] = 999
        with self.assertRaises(ValueError):
            normalize_rainfall_scenario(raw, observation=self.observation)

    def test_invalid_scenario_change_and_coverage_are_rejected(self):
        for change in (True, float("inf"), -101, 101):
            raw = copy.deepcopy(self.bundle["rainfall_scenario"])
            raw["rainfall_change_pct"] = change
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_rainfall_scenario(raw)
        raw["rainfall_change_pct"] = -30
        raw["summary"]["valid_days"] -= 1
        with self.assertRaises(ValueError):
            normalize_rainfall_scenario(raw)

    def test_response_has_required_fields_and_actual_used_references(self):
        response = respond(self.bundle, "Explain rainfall scenario")
        for key in ("role", "content", "source_ids", "limitations", "status", "language", "assumptions"):
            self.assertIn(key, response)
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["language"], "en")
        self.assertEqual(response["status"], "answered")
        self.assertEqual(response["source_ids"], self.observation["source_refs"])
        for assumption in self.bundle["rainfall_scenario"]["assumptions"]:
            self.assertIn(assumption, response["assumptions"])
        for limitation in self.observation["limitations"]:
            self.assertIn(limitation, response["limitations"])

    def test_response_does_not_collect_unselected_candidate_budget_sources(self):
        raw = {"analysis": self.result, "candidate_id": self.ids[0]}
        budgets = {self.ids[0]: self.water(source_refs=["synthetic-selected-source"]),
                   self.ids[1]: self.water(source_refs=["synthetic-unselected-source"])}
        response = respond(raw, "Explain water budgets", candidate_ids=self.ids,
                           analysis_metadata=self.metadata, water_budgets=budgets)
        self.assertIn("synthetic-selected-source", response["source_ids"])
        self.assertNotIn("synthetic-unselected-source", response["source_ids"])
        self.assertIn(self.scalar.assumptions[0], response["assumptions"])

    def test_rank_question_does_not_claim_unrendered_water_sources(self):
        response = respond({"analysis": self.result}, "Explain rankings", candidate_ids=self.ids,
                           analysis_metadata=self.metadata,
                           water_budgets={self.ids[0]: self.water(source_refs=["synthetic-water-only"])})
        self.assertNotIn("synthetic-water-only", response["source_ids"])
        self.assertEqual(response["status"], "insufficient_context")

    def test_missing_and_unsupported_statuses_are_structural(self):
        response = respond({"profile": {"data_kind": "synthetic", "irrigation_supply_mm_per_season": None}}, "Irrigation supply?")
        self.assertEqual(response["status"], "insufficient_context")
        self.assertEqual(response["source_ids"], [])
        response = respond(self.bundle, "Predict tomorrow's rainfall")
        self.assertEqual(response["status"], "unsupported_question")
        self.assertEqual(response["source_ids"], [])
        self.assertIn("synthetic", response["content"].lower())

    def test_empty_candidates_are_a_successful_result(self):
        response = respond({"analysis": CandidateGenerationResult((), ("Synthetic catalog has no approved crops.",))},
                           "Explain rotation candidates", analysis_metadata=self.metadata)
        self.assertEqual(response["status"], "answered")
        self.assertIn("Synthetic catalog has no approved crops", response["content"])

    def test_languages_are_not_silently_relabelled(self):
        for language in ("si", "ta", "fr"):
            with self.subTest(language=language), self.assertRaisesRegex(ValueError, "Only English"):
                respond(self.bundle, "Explain observations", language)

    def test_farmer_input_is_not_labelled_nasa_or_synthetic(self):
        response = respond({"profile": {"data_kind": "farmer_input", "area_ha": 1.5}}, "Farm area?")
        self.assertIn("farmer-entered", response["content"])
        self.assertNotIn("synthetic", response["content"])

    def test_modeled_and_heuristic_labels_are_distinct(self):
        # Values remain invented test values; this exercises caller-supplied
        # production provenance labels and does not establish any NASA retrieval.
        analysis = {"data_kind": "modeled", "score_kind": "heuristic", "candidates": [{"candidate_id": "test",
                    "rank": 1, "score": 0.7, "score_kind": "heuristic"}]}
        response = respond({"analysis": analysis}, "Explain rankings")
        self.assertIn("Model estimates, not measured NASA observations", response["content"])
        self.assertIn("Score kind: heuristic", response["content"])
        self.assertIn("analysis score kind: heuristic", response["content"])
        self.assertNotIn("Synthetic test data", response["content"])

    def test_full_analysis_preserves_all_extended_views(self):
        context = {"analysis": self.rotation(water_budgets={self.ids[0]: self.water(self.range)}),
                   "observations": self.observation, "scenario": self.bundle["rainfall_scenario"]}
        actual = normalize_context(context)
        answer = explain(actual, "show full analysis")
        for expected in ("Supplied crop sequence", "Constraint", "signed balance lower bound",
                         "Rainfall-only hypothetical", "Observation record", "Coverage:"):
            self.assertIn(expected, answer)

    def test_normalization_and_rendering_do_not_mutate_inputs(self):
        before = copy.deepcopy(self.bundle)
        normalized = normalize_context(self.bundle)
        response = respond(self.bundle, "Explain scenario")
        self.assertEqual(self.bundle, before)
        normalized["observations"]["summary"]["rainfall_mm"] = 999
        response["source_ids"].append("not-a-real-reference")
        self.assertEqual(self.bundle, before)

    def test_conflicting_context_ids_and_versions_are_rejected(self):
        for key, value in (("farm_id", "different"), ("observation_id", "different"), ("input_version", 2)):
            metadata = {**self.metadata, **{key: value}}
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize_context({"analysis": self.result, "observations": self.observation},
                                  candidate_ids=self.ids, analysis_metadata=metadata)

    def test_unknown_selected_id_is_rejected_at_integration_boundary(self):
        with self.assertRaises(ValueError):
            normalize_context({"analysis": self.result, "candidate_id": "missing"}, candidate_ids=self.ids)

    def test_provenance_versions_and_sources_are_not_invented(self):
        actual = normalize_rotation(self.result, candidate_ids=self.ids)
        for key in ("data_kind", "catalog_version", "model_version", "analysis_id"):
            self.assertNotIn(key, actual)
        self.assertEqual(actual["source_refs"], [])

    def test_boundary_options_require_actual_results(self):
        with self.assertRaises(ValueError):
            normalize_context({}, candidate_ids=self.ids)
        with self.assertRaises(ValueError):
            normalize_context({}, scenario_metadata={"scenario_id": "not-generated"})

    def test_metadata_conflicts_and_wrong_collection_types_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_rotation({"data_kind": "synthetic", "candidates": []}, metadata={"data_kind": "modeled"})
        for value in ({"candidates": "bad"}, {"source_refs": "bad"}, {"data_kind": "heuristic"}):
            with self.subTest(value=value), self.assertRaises((ValueError, TypeError)):
                normalize_rotation(value)

    def test_normalized_climate_context_is_reusable_and_idempotent(self):
        context = normalize_context(self.bundle)
        self.assertEqual(normalize_context(context), context)
        self.assertEqual(respond(context, "Explain rainfall scenario"), respond(self.bundle, "Explain rainfall scenario"))

    def test_farm_envelope_must_match_observation_identity_and_version(self):
        for envelope in ({"id": "another-farm", "input_version": self.observation["input_version"], "profile": {}},
                         {"id": self.observation["farm_id"], "input_version": 2, "profile": {}}):
            with self.subTest(envelope=envelope), self.assertRaises(ValueError):
                normalize_context({**envelope, "observations": self.observation})

    def test_period_length_must_match_expected_day_count(self):
        raw = copy.deepcopy(self.observation)
        raw["period"]["end"] = "2025-01-08"
        raw["summary"]["end"] = "2025-01-08"
        with self.assertRaises(ValueError):
            normalize_observation(raw)

    def test_coverage_requires_positive_integral_expected_days(self):
        for value in (0, True, "7", -1):
            raw = copy.deepcopy(self.observation)
            raw["coverage"] = {"expected_days": value}
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_observation(raw)

    def test_rainfall_scenario_identity_conflicts_are_rejected(self):
        for metadata in ({"farm_id": "other"}, {"observation_id": "other"},
                         {"input_version": 2}, {"baseline_observation_id": "other"}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                normalize_rainfall_scenario(self.bundle["rainfall_scenario"], observation=self.observation, metadata=metadata)

    def test_unknown_objects_and_invalid_profile_values_are_rejected(self):
        for context in ({"profile": object()}, {"profile": {"area_ha": float("inf")}},
                        {"profile": {"irrigation_supply_mm_per_season": -1}},
                        {"profile": {"data_kind": "invented-kind"}}):
            with self.subTest(context=context), self.assertRaises((TypeError, ValueError)):
                normalize_context(context)

    def test_invalid_source_url_is_not_returned_as_a_citation(self):
        for url in ("javascript:alert(1)", "not-a-url", ""):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_water_budget({}, metadata={"source_url": url})

    def test_budget_source_url_is_preserved_without_generated_reference_ids(self):
        url = "https://example.invalid/synthetic-reference"
        response = respond({"analysis": self.result}, "Explain water budgets", candidate_ids=self.ids,
                           analysis_metadata=self.metadata,
                           water_budgets={self.ids[0]: self.water(source_url=url)})
        self.assertIn(url, response["content"])
        self.assertIn(url, response["source_ids"])
        self.assertEqual(set(response["source_ids"]), {url, *self.metadata["source_refs"]})

    def test_unavailable_candidates_cannot_receive_unbound_budgets(self):
        with self.assertRaises(ValueError):
            normalize_rotation({}, water_budgets={"unknown": self.water()})

    def test_normalized_legacy_context_keeps_supplied_values(self):
        original = json.loads((FIXTURES / "rotation_context.synthetic.json").read_text(encoding="utf-8"))
        response = respond(original, "Compare water deficits")
        self.assertEqual(response["status"], "answered")
        for record in (original["analysis"], original["scenario"]):
            for candidate in record["candidates"]:
                self.assertIn(f"deficit: {candidate['water_budget']['deficit_mm']} mm", response["content"])
        self.assertNotIn(original["observations"]["source_refs"][0], response["source_ids"])

    def test_supplied_step_metadata_and_null_components_are_retained(self):
        candidate = {"candidate_id": "chosen", "crop_ids": ["rice"], "score_components": None,
                     "sequence": [{"season_index": 1, "crop_id": "rice", "season_label": "maha"}]}
        actual = normalize_rotation({"candidates": [candidate]})["candidates"][0]
        self.assertEqual(actual["sequence"][0]["season_label"], "maha")
        self.assertEqual(actual["score_components"], {})

    def test_constraint_metadata_is_collected_only_when_checks_are_rendered(self):
        raw = {"analysis": {"candidates": [{"candidate_id": "chosen", "constraint_checks": [
            {"rule": "Synthetic rule", "passed": None, "source_refs": ["synthetic-rule-source"],
             "limitations": ["Synthetic reported check only."]}
        ]}]}}
        checks = respond(raw, "Explain constraint checks")
        rankings = respond(raw, "Explain rankings")
        self.assertIn("synthetic-rule-source", checks["source_ids"])
        self.assertNotIn("synthetic-rule-source", rankings["source_ids"])
        self.assertIn("Synthetic reported check only.", checks["limitations"])
        self.assertIn("Synthetic reported check only.", checks["content"])


if __name__ == "__main__":
    unittest.main()
