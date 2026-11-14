"""72 realistic questions through both Python and the actual demo process."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from backend.app.services.assistant import explain
from backend.tests.assistant_qa_cases import CASES, ROOT, assert_case, case_context


class DirectQuestionTests(unittest.TestCase):
    pass


class CLIQuestionTests(unittest.TestCase):
    pass


def run_cli(text, cwd=ROOT, script=None):
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(script or ROOT / "backend/demo_assistant.py")],
        input=text, capture_output=True, encoding="utf-8", cwd=cwd, timeout=10,
    )


def direct_case(case):
    def test(self):
        context = case_context(case)
        assert_case(self, case, context, explain(context, case.question))
    return test


def cli_case(case):
    def test(self):
        context = case_context(case)
        if case.mutation:
            # Exercise the real CLI against isolated copies of fixture JSON.
            # Patch ROOT through a tiny subprocess launcher, never real files.
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                farm = root / "data/fixtures/farm.synthetic.json"
                results = root / "backend/tests/fixtures/rotation_context.synthetic.json"
                farm.parent.mkdir(parents=True)
                results.parent.mkdir(parents=True)
                farm.write_text(json.dumps(context["profile"]), encoding="utf-8")
                results.write_text(json.dumps({k: v for k, v in context.items() if k != "profile"}), encoding="utf-8")
                launcher = root / "launch.py"
                launcher.write_text(
                    "import sys\nfrom pathlib import Path\n"
                    f"sys.path.insert(0, {str(ROOT)!r})\n"
                    "from backend import demo_assistant as demo\n"
                    f"demo.ROOT = Path({str(root)!r})\n"
                    "raise SystemExit(demo.main())\n", encoding="utf-8",
                )
                result = run_cli(case.question + "\nexit\n", script=launcher)
        else:
            result = run_cli(case.question + "\nexit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("You:", result.stdout)
        self.assertIn("Goodbye", result.stdout)
        marker = "Assistant [SYNTHETIC DATA]:"
        self.assertIn(marker, result.stdout, result.stdout)
        answer = result.stdout.split(marker, 1)[1].rsplit("You:", 1)[0]
        assert_case(self, case, context, answer)
    return test


for index, case in enumerate(CASES, start=1):
    name = f"test_{case.category}_{index:03d}"
    setattr(DirectQuestionTests, name, direct_case(case))
    setattr(CLIQuestionTests, name, cli_case(case))


class CLILifecycleTests(unittest.TestCase):
    def test_help_then_exit(self):
        result = run_cli("help\nexit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        for text in ("SYNTHETIC DATA", "Example questions", "show full analysis", "Goodbye"):
            self.assertIn(text, result.stdout)

    def test_blank_input_and_eof(self):
        result = run_cli("\n  \n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Assistant [", result.stdout)
        self.assertIn("Goodbye", result.stdout)

    def test_case_insensitive_exit_and_quit(self):
        for command in (" EXIT ", "QuIt"):
            with self.subTest(command=command):
                result = run_cli(command + "\n")
                self.assertEqual(result.returncode, 0)
                self.assertIn("Goodbye", result.stdout)

    def test_whitespace_candidate_command_and_selection_reset(self):
        context = case_context(CASES[0])
        identifier = context["analysis"]["candidates"][0]["candidate_id"]
        result = run_cli(f"candidate\t{identifier.upper()}\nExplain water budgets\ncandidate all\nexit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"Selected candidate: {identifier}", result.stdout)
        self.assertIn("Selected all candidates", result.stdout)
        answer = result.stdout.split("Assistant [SYNTHETIC DATA]:", 1)[1]
        other = context["analysis"]["candidates"][1]["candidate_id"]
        self.assertNotIn(f"Candidate {other}:", answer)

    def test_bare_candidate_command_prints_usage(self):
        result = run_cli("candidate\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage:", result.stdout)
        self.assertNotIn("supplied score", result.stdout)

    def test_unknown_selection_does_not_replace_previous_selection(self):
        context = case_context(CASES[0])
        identifier = context["analysis"]["candidates"][0]["candidate_id"]
        result = run_cli(f"candidate {identifier}\ncandidate unknown-id\nExplain water budgets\nexit\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Unknown candidate", result.stdout)
        answer = result.stdout.split("Assistant [SYNTHETIC DATA]:", 1)[1]
        self.assertIn(f"Candidate {identifier}:", answer)
        self.assertNotIn("Candidate unknown-id:", answer)

    def test_full_analysis_has_all_three_sections(self):
        result = run_cli("show full analysis\nexit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        for section in ("Baseline analysis", "Hypothetical scenario", "Observation record"):
            self.assertIn(section, result.stdout)

    def test_script_works_from_another_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_cli("What is the farm name?\nexit\n", cwd=directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(case_context(CASES[0])["profile"]["name"], result.stdout)

    def test_control_characters_do_not_crash_cli(self):
        result = run_cli("\x00\x01\nexit\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Goodbye", result.stdout)


if __name__ == "__main__":
    unittest.main()
