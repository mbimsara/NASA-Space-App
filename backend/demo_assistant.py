"""Interactive synthetic-data demo. Run: python backend/demo_assistant.py"""

import json
from pathlib import Path
import textwrap

if __package__:
    from .app.services.assistant import explain
else:
    # Direct script execution puts backend/ on Python's import path.
    from app.services.assistant import explain


ROOT = Path(__file__).resolve().parents[1]
HELP = """Commands:
  help   Show these examples.
  exit   Close the demo (quit also works).
  show full analysis   Display all analysis, scenario, and observation details.
  candidate <id>       Select one candidate, for example candidate-test-a.
  candidate all        Explain all candidates (the default).

Example questions (English only):
  What is the farm name?
  What is the farm area?
  Where is the farm located?
  How much irrigation supply is available?
  What soil measurements are recorded?
  What is the crop history?
  What are my priority weights?
  Explain the rotation candidates and rankings.
  What are the rotation scores?
  Explain the water budgets.
  How much water is needed?
  How much water does candidate A need?
  Compare water deficits.
  What happens if rainfall decreases?
  Compare the hypothetical rainfall scenario and baseline.
  What are the source references?

Questions use simple keyword matching. All answers use fixed synthetic
fixtures; asking about a different rainfall change does not run a new scenario.
The demo explains supplied results and cannot generate crop recommendations.
Candidate aliases A/B refer to unique ID suffixes, not rank or list position.
Use one candidate per question, or all candidates. Reset an existing selection
with candidate all before asking for a different candidate.
"""


def load_context():
    """Load both existing fixtures relative to this script, not the terminal."""
    farm = json.loads(
        (ROOT / "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8")
    )
    context = json.loads(
        (ROOT / "backend/tests/fixtures/rotation_context.synthetic.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(farm, dict) or not isinstance(context, dict):
        raise ValueError("Demo fixtures must contain JSON objects.")
    context["profile"] = farm
    return context


def main():
    """Read questions until exit, end-of-input, or Ctrl+C."""
    try:
        context = load_context()
    except (OSError, ValueError) as error:
        print(f"Could not load demo fixtures: {error}")
        return 1

    print("AgroSphere AI Assistant - Milestones 1 and 2")
    print("SYNTHETIC DATA ONLY: invented farm inputs, placeholder crops, and test results.")
    print("These are not actual NASA observations or validated farming recommendations.")
    print("English only. Type help for examples, or exit to close.\n")
    candidate_ids = {
        candidate["candidate_id"]
        for candidate in (context.get("analysis") or {}).get("candidates", []) or []
    }
    canonical_ids = {identifier.casefold(): identifier for identifier in candidate_ids}

    while True:
        try:
            question = input("You: ").strip()
            if not question:
                continue
            command = question.casefold()
            if command in {"exit", "quit"}:
                print("Goodbye.")
                return 0
            if command == "help":
                print(f"\n{HELP}")
                continue
            parts = question.split(maxsplit=1)
            if parts[0].casefold() == "candidate":
                if len(parts) == 1:
                    print("\nUsage: candidate <id> or candidate all.\n")
                    continue
                selected = parts[1]
                if selected.casefold() == "all":
                    context.pop("candidate_id", None)
                    print("\nSelected all candidates.\n")
                elif selected.casefold() in canonical_ids:
                    identifier = canonical_ids[selected.casefold()]
                    context["candidate_id"] = identifier
                    print(f"\nSelected candidate: {identifier}.\n")
                else:
                    print("\nUnknown candidate. Available IDs: "
                          + ", ".join(sorted(candidate_ids)) + ".\n")
                continue

            try:
                answer = explain(context, question, language="en")
            except (TypeError, ValueError) as error:
                print(f"\nAssistant: Could not explain the supplied context: {error}\n")
                continue

            print("\nAssistant [SYNTHETIC DATA]:")
            for line in answer.splitlines():
                print(textwrap.fill(
                    line, width=88, initial_indent="  ", subsequent_indent="  ",
                    break_long_words=False, break_on_hyphens=False,
                ))
            print()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
