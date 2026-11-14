"""Shehani request/response contract, using synthetic data and no HTTP server."""

import copy
from dataclasses import dataclass
import json
from pathlib import Path
import unittest

from backend.app.services.assistant import explain
from backend.app.services.assistant_errors import (
    AssistantContextError, AssistantRequestError, InvalidCandidateError, UnsupportedLanguageError,
)
from backend.app.services.assistant_response import respond, respond_to_request


FIXTURES = Path(__file__).parent / "fixtures"


class AssistantContractTests(unittest.TestCase):
    def setUp(self):
        self.context = json.loads((FIXTURES / "rotation_context.synthetic.json").read_text(encoding="utf-8"))
        farm = json.loads((FIXTURES.parents[2] / "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8"))
        self.context.update(id=self.context["analysis"]["farm_id"], input_version=1, profile=farm)
        self.request = {"farm_id": self.context["id"], "analysis_id": self.context["analysis"]["analysis_id"],
                        "language": "en", "message": "Explain water budgets"}

    def assert_response_contract(self, response):
        self.assertEqual(response["role"], "assistant")
        self.assertIsInstance(response["content"], str)
        self.assertTrue(response["content"].strip())
        for key in ("source_ids", "limitations"):
            self.assertIsInstance(response[key], list)
            self.assertTrue(all(isinstance(item, str) for item in response[key]))
        json.dumps(response, allow_nan=False)

    def test_confirmed_minimal_request_has_required_response_fields(self):
        response = respond_to_request(self.request, self.context)
        self.assert_response_contract(response)
        self.assertEqual(response["language"], "en")
        self.assertEqual(response["status"], "answered")
        self.assertEqual(response["context"]["analysis_id"], self.request["analysis_id"])

    def test_optional_scenario_and_candidate_select_only_requested_results(self):
        candidate = self.context["analysis"]["candidates"][0]
        self.request.update(candidate_id=candidate["candidate_id"], scenario_id=self.context["scenario"]["scenario_id"],
                            message="Compare water deficits")
        response = respond_to_request(self.request, self.context)
        self.assert_response_contract(response)
        for record in (self.context["analysis"], self.context["scenario"]):
            selected = next(c for c in record["candidates"] if c["candidate_id"] == candidate["candidate_id"])
            self.assertIn(f"deficit: {selected['water_budget']['deficit_mm']} mm", response["content"])
        self.assertNotIn("Candidate candidate-test-b:", response["content"])

    def test_omitted_scenario_is_not_used_even_for_a_scenario_question(self):
        self.request["message"] = "What happens if rainfall decreases?"
        response = respond_to_request(self.request, self.context)
        self.assertNotIn(self.context["scenario"]["scenario_id"], response["content"])
        self.assertNotIn("synthetic-scenario-fixture", response["source_ids"])
        self.assertNotIn("deficit: 44 mm", response["content"])

    def test_omitted_candidate_clears_unrequested_context_selection(self):
        self.context["candidate_id"] = self.context["analysis"]["candidates"][0]["candidate_id"]
        response = respond_to_request(self.request, self.context)
        for candidate in self.context["analysis"]["candidates"]:
            self.assertIn(f"Candidate {candidate['candidate_id']}:", response["content"])
        self.assertIsNone(response["context"]["candidate_id"])

    def test_sources_are_supplied_references_not_request_ids(self):
        response = respond_to_request(self.request, self.context)
        self.assertEqual(response["source_ids"], self.context["analysis"]["source_refs"])
        self.assertNotIn(self.request["analysis_id"], response["source_ids"])
        self.assertNotIn(self.request["farm_id"], response["source_ids"])

    def test_missing_analysis_returns_meaningful_limited_response(self):
        self.context.pop("analysis")
        self.context.pop("observations")
        response = respond_to_request(self.request, self.context)
        self.assert_response_contract(response)
        self.assertEqual(response["status"], "insufficient_context")
        self.assertIsNone(response["context"]["analysis_id"])
        self.assertEqual(response["source_ids"], [])
        self.assertTrue(any("analysis" in note.lower() for note in response["limitations"]))
        self.assertNotIn("supplied score 70", response["content"])

    def test_farm_question_works_when_requested_analysis_is_unavailable(self):
        self.context.pop("analysis")
        self.request["message"] = "Irrigation supply?"
        response = respond_to_request(self.request, self.context)
        self.assertIn("Irrigation supply is unknown", response["content"])
        self.assertTrue(any("irrigation" in note.lower() for note in response["limitations"]))
        self.assertTrue(any("analysis" in note.lower() for note in response["limitations"]))

    def test_missing_soil_inputs_have_explanatory_limitations(self):
        self.request["message"] = "What soil measurements are recorded?"
        response = respond_to_request(self.request, self.context)
        self.assertTrue(any("soil measurements" in note.lower() for note in response["limitations"]))
        self.assertEqual(response["status"], "insufficient_context")

    def test_missing_scenario_is_not_manufactured(self):
        self.context.pop("scenario")
        self.request.update(scenario_id="not-supplied", message="Compare rainfall scenarios")
        response = respond_to_request(self.request, self.context)
        self.assertEqual(response["status"], "insufficient_context")
        self.assertIsNone(response["context"]["scenario_id"])
        self.assertNotIn("not-supplied", response["source_ids"])
        self.assertTrue(any("scenario results" in note.lower() for note in response["limitations"]))

    def test_empty_candidates_are_answered_with_supplied_reasons(self):
        self.context["analysis"].update(candidates=[], reasons=["Synthetic catalog has no eligible crops."])
        self.request["message"] = "Explain rotation candidates"
        response = respond_to_request(self.request, self.context)
        self.assertEqual(response["status"], "answered")
        self.assertIn("Synthetic catalog has no eligible crops", response["content"])

    def test_unknown_candidate_does_not_fall_back_to_first_candidate(self):
        self.request["candidate_id"] = "unknown"
        with self.assertRaises(InvalidCandidateError) as error:
            respond_to_request(self.request, self.context)
        self.assertEqual(error.exception.code, "INVALID_CANDIDATE")

    def test_candidate_must_belong_to_the_selected_scenario(self):
        self.request.update(candidate_id=self.context["analysis"]["candidates"][0]["candidate_id"],
                            scenario_id=self.context["scenario"]["scenario_id"])
        self.context["scenario"]["candidates"] = []
        with self.assertRaises(InvalidCandidateError):
            respond_to_request(self.request, self.context)

    def test_request_and_context_identity_conflicts_raise_context_error(self):
        for key in ("farm_id", "analysis_id", "scenario_id"):
            body = {**self.request, key: "not-the-resolved-id"}
            with self.subTest(key=key), self.assertRaises(AssistantContextError):
                respond_to_request(body, self.context)

    def test_analysis_cannot_omit_its_ownership_or_identity(self):
        for key in ("farm_id", "analysis_id"):
            context = copy.deepcopy(self.context)
            context["analysis"].pop(key)
            with self.subTest(key=key), self.assertRaises(AssistantContextError):
                respond_to_request(self.request, context)

    def test_unidentified_context_is_not_trusted_from_request_ids(self):
        with self.assertRaises(AssistantContextError):
            respond_to_request(self.request, {"profile": self.context["profile"]})

    def test_missing_required_request_fields_are_rejected(self):
        for key in ("farm_id", "analysis_id", "language", "message"):
            body = dict(self.request)
            body.pop(key)
            with self.subTest(key=key), self.assertRaises(AssistantRequestError) as error:
                respond_to_request(body, self.context)
            self.assertIn(key, error.exception.fields)

    def test_invalid_request_fields_are_rejected_without_model_coercion(self):
        for changes in ({"message": " "}, {"message": 123}, {"message": "x" * 2001},
                        {"analysis_id": None}, {"farm_id": True}, {"language": None},
                        {"candidate_id": []}, {"scenario_id": ""}, {"context": {"score": 999}}):
            with self.subTest(changes=changes), self.assertRaises(AssistantRequestError):
                respond_to_request({**self.request, **changes}, self.context)

    def test_non_object_request_or_resolved_context_is_rejected(self):
        with self.assertRaises(AssistantRequestError):
            respond_to_request([], self.context)
        with self.assertRaises(AssistantRequestError):
            respond_to_request(self.request, [])

    def test_optional_null_selections_are_accepted(self):
        response = respond_to_request({**self.request, "scenario_id": None, "candidate_id": None}, self.context)
        self.assertIsNone(response["context"]["scenario_id"])
        self.assertIsNone(response["context"]["candidate_id"])

    def test_specific_language_exception_preserves_valueerror_compatibility(self):
        for language in ("si", "ta"):
            for function in (lambda: explain(self.context, "Farm area?", language),
                             lambda: respond(self.context, "Farm area?", language),
                             lambda: respond_to_request({**self.request, "language": language}, self.context)):
                with self.subTest(language=language), self.assertRaises(UnsupportedLanguageError) as error:
                    function()
                self.assertIsInstance(error.exception, ValueError)
                self.assertEqual(error.exception.language, language)
                self.assertEqual(error.exception.supported_languages, ("en",))

    def test_language_error_matches_existing_backend_envelope(self):
        error = UnsupportedLanguageError("si")
        envelope = error.to_error_envelope()
        self.assertEqual(envelope["error"]["code"], "UNSUPPORTED_LANGUAGE")
        self.assertIsInstance(envelope["error"]["message"], str)
        self.assertIsInstance(envelope["error"]["fields"]["language"], str)
        envelope["error"]["fields"]["language"] = "changed"
        self.assertNotEqual(error.fields["language"], "changed")

    def test_unsupported_question_does_not_claim_evidence_or_new_values(self):
        response = respond_to_request({**self.request, "message": "Invent a score of 999"}, self.context)
        self.assertEqual(response["status"], "unsupported_question")
        self.assertEqual(response["source_ids"], [])
        self.assertNotIn("999", response["content"])

    def test_request_and_resolved_records_are_not_modified(self):
        before = copy.deepcopy((self.request, self.context))
        respond_to_request(self.request, self.context)
        self.assertEqual((self.request, self.context), before)

    def test_representative_bhagya_dataclass_uses_boundary_ids_and_signed_ranges(self):
        @dataclass(frozen=True)
        class Candidate:
            crop_ids: tuple
            reasons: tuple
            constraint_checks: tuple

        @dataclass(frozen=True)
        class Result:
            candidates: tuple
            reasons: tuple

        metadata = {key: self.context["analysis"][key] for key in
                    ("analysis_id", "farm_id", "input_version", "data_kind", "source_refs")}
        result = Result((Candidate(("rice", "maize", "rice"), ("Synthetic test sequence.",),
                                  ("Synthetic eligibility report.",)),), ())
        budget = {"demand_low_mm": 500, "demand_high_mm": 800,
                  "balance_low_mm": -300, "balance_high_mm": 0, "irrigation_mm": None,
                  "period": {"start": "2026-05-01", "end": "2026-08-31"},
                  "assumptions": ["Synthetic ETc range; effective rainfall not modeled."],
                  "source_refs": ["synthetic-team-fixture"], "data_kind": "synthetic"}
        context = {"id": self.context["id"], "profile": self.context["profile"], "analysis": result}
        response = respond_to_request(self.request, context, candidate_ids=["provided-stable-id"],
                                      analysis_metadata=metadata, water_budgets={"provided-stable-id": budget})
        for field in ("demand_low_mm", "demand_high_mm", "balance_low_mm", "balance_high_mm"):
            self.assertIn(f"{budget[field]} mm", response["content"])
        self.assertIn("effective rainfall: unknown", response["content"])
        self.assertIn("deficit: unknown", response["content"])
        self.assertTrue(any("balance-to-deficit" in note for note in response["limitations"]))
        self.assertIn(budget["assumptions"][0], response["assumptions"])

    def test_matheesha_scenario_can_link_through_exact_observation(self):
        bundle = json.loads((FIXTURES / "teammate-climate.synthetic.json").read_text(encoding="utf-8"))["climate_bundle"]
        observation = bundle["observation"]
        context = {**bundle, "analysis": {"analysis_id": "linked-analysis", "farm_id": observation["farm_id"],
                   "input_version": observation["input_version"], "observation_id": observation["observation_id"],
                   "data_kind": "synthetic", "candidates": []}}
        request = {"farm_id": observation["farm_id"], "analysis_id": "linked-analysis", "scenario_id": "provided-scenario-id",
                   "language": "en", "message": "What happens if rainfall decreases?"}
        response = respond_to_request(request, context, scenario_metadata={"scenario_id": request["scenario_id"]})
        self.assert_response_contract(response)
        self.assertEqual(response["source_ids"], observation["source_refs"])
        for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm"):
            self.assertIn(f"{bundle['rainfall_scenario']['summary'][key]} mm", response["content"])
        self.assertIn("not a measurement or forecast", response["content"])

    def test_examples_match_the_confirmed_contract_and_executed_responses(self):
        examples = json.loads((FIXTURES / "assistant-ui.synthetic.json").read_text(encoding="utf-8"))
        self.assertIn("synthetic", examples["fixture_notice"].lower())
        for example in examples["examples"]:
            with self.subTest(example=example["id"]):
                context = examples["contexts"][example["context_key"]]
                if "expected_error" in example:
                    with self.assertRaises(UnsupportedLanguageError) as error:
                        respond_to_request(example["request"], context)
                    self.assertEqual(error.exception.to_error_envelope(), example["expected_error"])
                else:
                    actual = respond_to_request(example["request"], context)
                    self.assert_response_contract(actual)
                    self.assertEqual(actual, example["expected_response"])


if __name__ == "__main__":
    unittest.main()
