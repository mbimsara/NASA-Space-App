"""Regression checks for focused answers with every fixture loaded."""

import copy
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from backend.app.services.assistant import explain
from backend.demo_assistant import load_context, main


class FocusedAssistantTests(unittest.TestCase):
    def setUp(self):
        self.context = load_context()

    def test_water_question_excludes_unrelated_results(self):
        answer = explain(self.context, "Explain water budgets")
        for expected in ("demand: 200 mm", "effective rainfall: 80 mm",
                         "irrigation supply: 100 mm", "deficit: 20 mm", "deficit: 0 mm",
                         "2026-01-01 to 2026-03-31", "80% of rainfall"):
            self.assertIn(expected, answer)
        for unrelated in ("Hypothetical scenario", "Observation record", "supplied score",
                          "Supplied crop sequence", "Score components", "Supplied reasons"):
            self.assertNotIn(unrelated, answer)

    def test_water_alternative_wording_has_the_same_focused_answer(self):
        expected = explain(self.context, "Explain water budgets")
        for question in ("How much water is needed?", "How much water do crops need?",
                         "What is the water requirement?"):
            with self.subTest(question=question):
                self.assertEqual(explain(self.context, question), expected)

    def test_focused_water_keeps_only_its_own_metadata(self):
        answer = explain(self.context, "Water budgets?")
        self.assertIn("Synthetic test data, not actual NASA observations", answer)
        for key in ("source_refs", "assumptions", "limitations"):
            for entry in self.context["analysis"][key]:
                self.assertIn(entry, answer)
        self.assertNotIn("synthetic-scenario-fixture", answer)
        self.assertNotIn("synthetic-observation-fixture", answer)

    def test_water_budget_for_selected_candidate_excludes_other_candidates(self):
        self.context["candidate_id"] = "candidate-test-b"
        answer = explain(self.context, "Explain water budgets for the selected candidate")
        self.assertIn("Candidate candidate-test-b", answer)
        self.assertIn("demand: 160 mm", answer)
        self.assertNotIn("Candidate candidate-test-a", answer)
        self.assertNotIn("supplied score", answer)
        self.assertNotIn("Supplied crop sequence", answer)

    def test_rainfall_decrease_question_compares_supplied_values(self):
        answer = explain(self.context, "What happens if rainfall decreases?")
        for expected in ("Baseline analysis", "Hypothetical scenario", "rainfall change: -30%",
                         "rainfall: 100 mm", "rainfall: 70 mm", "deficit: 20 mm",
                         "deficit: 44 mm", "deficit: 24 mm", "scenario minus baseline",
                         "not a rainfall observation or forecast"):
            self.assertIn(expected, answer)
        for unrelated in ("Observation record", "mean temperature", "Supplied crop sequence",
                          "Score components", "Supplied reasons"):
            self.assertNotIn(unrelated, answer)

    def test_scenario_water_question_excludes_scores(self):
        answer = explain(self.context, "Compare baseline and scenario water budgets")
        self.assertIn("deficit: 20 mm", answer)
        self.assertIn("deficit: 44 mm", answer)
        self.assertIn("deficit: 24 mm", answer)
        self.assertNotIn("supplied score", answer)
        self.assertNotIn("score difference", answer)
        self.assertNotIn("Observation record", answer)

    def test_deficit_comparison_excludes_other_budget_metrics(self):
        answer = explain(self.context, "Compare water deficits")
        for expected in ("deficit: 20 mm", "deficit: 44 mm", "deficit: 24 mm",
                         "deficit: 0 mm", "deficit: 4 mm", "2026-01-01 to 2026-03-31"):
            self.assertIn(expected, answer)
        for unrelated in ("demand:", "effective rainfall:", "irrigation supply:",
                          "supplied score", "Observation record"):
            self.assertNotIn(unrelated, answer)

    def test_scenario_metadata_stays_attached_to_the_comparison(self):
        answer = explain(self.context, "Compare water deficits")
        for section in ("analysis", "scenario"):
            for key in ("source_refs", "assumptions", "limitations"):
                for entry in self.context[section][key]:
                    self.assertIn(entry, answer)
        self.assertNotIn("synthetic-observation-fixture", answer)

    def test_unknown_deficit_and_missing_deltas_are_not_recalculated(self):
        self.context["candidate_id"] = "candidate-test-a"
        self.context["scenario"]["candidates"][0]["water_budget"]["deficit_mm"] = None
        self.context["scenario"].pop("differences")
        answer = explain(self.context, "Compare water deficits")
        self.assertIn("deficit: unknown", answer)
        self.assertIn("Baseline differences are unknown; this service does not calculate them", answer)
        self.assertNotIn("deficit: 44 mm", answer)

    def test_another_requested_rainfall_change_does_not_create_results(self):
        answer = explain(self.context, "What happens if rainfall decreases by 50%?")
        self.assertIn("Supplied rainfall change: -30%", answer)
        self.assertIn("no new scenario is calculated", answer)
        self.assertNotIn("-50%", answer)

    def test_rankings_are_focused_on_baseline_scores_and_reasons(self):
        for question in ("Explain crop rankings", "Why is this rotation ranked first?",
                         "What are the rotation scores?"):
            with self.subTest(question=question):
                answer = explain(self.context, question)
                self.assertIn("supplied rank 1; supplied score 70", answer)
                self.assertIn("supplied rank 2; supplied score 60", answer)
                self.assertIn("Invented first-place baseline ranking", answer)
                for unrelated in ("Water budget", "Hypothetical scenario", "Observation record",
                                  "Supplied crop sequence", "Score components"):
                    self.assertNotIn(unrelated, answer)

    def test_comparative_rankings_exclude_water_budgets(self):
        answer = explain(self.context, "Compare crop rankings")
        self.assertIn("supplied rank 1; supplied score 70", answer)
        self.assertIn("supplied rank 2; supplied score 55", answer)
        self.assertIn("score difference (scenario minus baseline): -15", answer)
        self.assertNotIn("Water budget", answer)
        self.assertNotIn("deficit:", answer)
        self.assertNotIn("Observation record", answer)

    def test_multiple_requested_topics_can_be_combined(self):
        answer = explain(self.context, "Explain rotation scores and water budgets")
        self.assertIn("supplied score 70", answer)
        self.assertIn("demand: 200 mm", answer)
        self.assertNotIn("Hypothetical scenario", answer)
        self.assertNotIn("Observation record", answer)

    def test_farm_questions_use_profile_instead_of_modeled_irrigation(self):
        cases = (
            ("Irrigation supply?", "Irrigation supply is unknown"),
            ("What are the soil measurements?", "Soil measurements are unknown"),
            ("What is the farm area?", "1.0 hectares"),
            ("What are my priority weights?", "water: 0.5, soil: 0.3, climate: 0.2"),
        )
        for question, expected in cases:
            with self.subTest(question=question):
                answer = explain(self.context, question)
                self.assertIn(expected, answer)
                self.assertIn("synthetic demonstration inputs", answer)
                self.assertNotIn("Baseline analysis", answer)
                self.assertNotIn("irrigation supply: 100 mm", answer)

    def test_observation_and_source_views_do_not_dump_candidate_results(self):
        answer = explain(self.context, "Explain rainfall observations")
        self.assertIn("Observation record", answer)
        self.assertIn("rainfall: 100 mm", answer)
        self.assertNotIn("Baseline analysis", answer)
        self.assertNotIn("Hypothetical scenario", answer)
        sources = explain(self.context, "What are the source references?")
        self.assertIn("synthetic-baseline-fixture", sources)
        self.assertIn("synthetic-scenario-fixture", sources)
        self.assertIn("synthetic-observation-fixture", sources)
        self.assertNotIn("supplied score", sources)
        self.assertNotIn("demand: 200 mm", sources)
        self.assertNotIn("mean temperature:", sources)

    def test_full_analysis_is_still_explicitly_available(self):
        answer = explain(self.context, "show full analysis")
        for expected in ("Baseline analysis", "Hypothetical scenario", "Observation record",
                         "Supplied crop sequence", "Score components", "demand: 200 mm",
                         "supplied score 70", "mean temperature: 27 Celsius"):
            self.assertIn(expected, answer)
        self.assertGreater(len(answer), len(explain(self.context, "Water budgets?")))

    def test_focused_calls_do_not_change_fixtures_or_selection(self):
        self.context["candidate_id"] = "candidate-test-a"
        before = copy.deepcopy(self.context)
        for question in ("Water budgets?", "Compare deficits", "Explain rankings", "show full analysis"):
            first = explain(self.context, question)
            self.assertEqual(first, explain(self.context, question))
        self.assertEqual(before, self.context)

    def test_cli_selection_help_and_full_analysis(self):
        questions = iter(("help", "candidate candidate-test-a", "Explain water budgets",
                          "candidate not-a-candidate", "candidate all", "show full analysis", "exit"))
        output = io.StringIO()
        with patch("builtins.input", side_effect=lambda prompt: next(questions)), redirect_stdout(output):
            self.assertEqual(main(), 0)
        text = output.getvalue()
        self.assertIn("show full analysis", text)
        self.assertIn("Selected candidate: candidate-test-a", text)
        self.assertIn("Unknown candidate. Available IDs:", text)
        self.assertIn("Selected all candidates", text)
        focused = text.split("Assistant [SYNTHETIC DATA]:", 2)[1]
        self.assertIn("candidate-test-a", focused)
        self.assertNotIn("Candidate candidate-test-b", focused)
        self.assertNotIn("Observation record", focused)
        self.assertIn("Observation record", text.split("Assistant [SYNTHETIC DATA]:", 2)[2])


if __name__ == "__main__":
    unittest.main()
