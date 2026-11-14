# Deterministic assistant QA report

Executed on 14 November 2026, Windows / Python 3.13.7, branch `akash-dev`.
No external APIs, paid services, package installation, branch changes, commits,
or pushes were used. Existing pending work was retained.

## Actual execution

| Run | Executed unittest cases | Passed | Failed | Errors |
| --- | ---: | ---: | ---: | ---: |
| New QA suite before fixes | 153 | 102 | 51 | 0 |
| Complete regression after fixes | 211 | 211 | 0 | 0 |
| Separate real-CLI rerun after regression | 81 | 81 | 0 | 0 |

The final 211 unique tests comprise the original 40 tests, 18 existing focused
routing tests, 72 new direct question tests, 72 new subprocess question tests,
and 9 new CLI lifecycle tests. The separate 81-test rerun repeats CLI tests;
it does not represent 81 additional unique cases. Unittest counts are method
counts; some lifecycle and original tests also contain subtests.

The data validator was actually executed and passed. It still reports that the
shared crop catalog is empty and needs research/approval before recommendations.

## Question coverage

Each category has six distinct questions, each executed through both Python
and a real CLI process. The 72-question catalogue lives in
`backend/tests/assistant_qa_cases.py`, with descriptive category names and
independently implemented assertions.

| Category | Questions | Initial failing executions / 12 | Final passed / 12 |
| --- | ---: | ---: | ---: |
| Farm identity, coordinates, area, units | 6 | 4 | 12 |
| Irrigation and missing information | 6 | 0 | 12 |
| Soil and crop history | 6 | 2 | 12 |
| Candidates, ranks, scores, reasons | 6 | 4 | 12 |
| Water demand, effective rainfall, supply, deficits | 6 | 8 | 12 |
| Baseline/hypothetical scenarios | 6 | 2 | 12 |
| Observations, provenance, source IDs | 6 | 0 | 12 |
| Missing and zero values | 6 | 3 | 12 |
| Unsupported requests and forecasts | 6 | 4 | 12 |
| Wording, punctuation, capitalization | 6 | 2 | 12 |
| Unknown candidates and conflicting requests | 6 | 10 | 12 |
| Requests to invent facts/citations | 6 | 10 | 12 |
| **Total question executions** | **72** | **49 / 144** | **144 / 144** |

The remaining two initial failures were CLI lifecycle tests: bare candidate
commands and tab-separated/case-insensitive candidate selection. All nine
lifecycle tests now pass. They also exercise help/exit/quit, blank input, EOF,
control characters, unknown-selection persistence, full analysis, and execution
from a different working directory. EOF is tested through stdin closure; a real
interactive terminal Ctrl+C event was not separately automated in this suite.

## Independent fixture oracle

Tests read the checked-in JSON directly, without using the assistant's response
or the production demo loader as expected output. Expected crop IDs, values,
units, periods, source references, assumptions, and limitations come from the
fixtures and documented formatter conventions.

For analytical output, assertions associate each displayed metric with its
candidate and baseline/scenario/difference section. They check ranks, scores,
water depths in mm, supplied deltas, periods, sequences, score components, and
source metadata. Focused questions also assert absence of unrelated sections.
Farm checks preserve hectares, WGS84 coordinates, and unknown irrigation/soil
inputs. Every question case checks the synthetic label. Scenario cases check
that results are explicitly hypothetical and not observations or forecasts.

Missing-data variations remove fields or replace them with null in memory and
temporary fixture copies only. The real subprocess demo reads those temporary
copies through a launcher that overrides its fixture root. The checked-in JSON
and crop catalog are unchanged. The fixture's actual zero deficit for candidate
B is checked without replacing missing information with zero.

## Verified defects and fixes

1. **Named candidates were ignored.** "How much water does candidate A need?"
   returned both candidates. Exact IDs and unique one-character ID-suffix
   aliases now resolve before formatting. Aliases never depend on rank/order.
2. **Unknown/conflicting selections returned unrelated results.** Unknown IDs,
   multiple explicit IDs, a question conflicting with an active selection, and
   simultaneous baseline-only/scenario-only requests now receive an explicit
   unavailable/unknown response rather than another candidate's values.
3. **Effective rainfall used the wrong view.** "What is the effective rainfall?"
   returned observation rainfall. It now uses supplied model-budget values.
   Candidate-specific irrigation also uses the budget; farm irrigation remains
   unknown. "require" now routes like "need" and "required".
4. **Future requests could display historical observations.** "What is tomorrow's
   rainfall?" now declines before ordinary rainfall routing, as do unavailable
   new minimum/maximum rankings such as "lowest supplied water deficit".
5. **Instruction-like invention/edit requests were not declined.** They returned
   supplied analysis sections. Tests did not observe the requested fake `999`
   values being invented; this defect concerned refusal/routing behavior.
   Such requests now receive a read-only unavailable response.
6. **Common farm wording was missed.** "What is this farm called?", "Where is my
   farm?", and "Which crops did I grow before?" now route to recorded facts or
   the appropriate unknown-history explanation.
7. **Missing candidates crashed CLI startup.** A temporary fixture without the
   `candidates` key produced a real `KeyError`. Candidate-menu initialization now
   tolerates missing/null candidates while the assistant explains unavailable
   results.
8. **CLI command parsing was whitespace-sensitive.** A bare `candidate` now shows
   usage; tabs and case variations in valid IDs work. Unknown IDs preserve the
   active selection, and `candidate all` resets it.

The 51 initial failed executions share these root causes; they are not 51
distinct production defects. Existing scientific values, calculation behavior,
source IDs, full-analysis support, and original test files were preserved.

## Files changed during this QA task

- `backend/app/services/assistant.py`: centralized read-only/unavailable checks
  before factual routing and small farm-language aliases.
- `backend/app/services/assistant_results.py`: candidate resolution/conflict
  checks and corrected water-topic routing.
- `backend/demo_assistant.py`: resilient missing-candidate handling, command
  parsing, canonical-ID lookup, and explanatory help.
- `backend/tests/assistant_qa_cases.py`: 72-case catalogue and independent oracle.
- `backend/tests/test_assistant_qa.py`: generated direct/CLI tests and lifecycle
  tests using stdlib unittest, subprocess, and temporary directories.
- `backend/tests/fixtures/README.md`: supported aliases, refusal policies, and QA
  documentation links.
- `backend/tests/QA_REPORT.md`: this execution report.

## Remaining unsupported capabilities and untested scope

Forecasts, new scientific calculations, new crop advice, newly derived extrema
rankings, unit conversions, record edits, multiple explicit candidate selections
in one question, and invented/resolved citations remain unsupported. Use one
candidate or all candidates to view supplied results. English keyword routing
is not general natural-language understanding. Sinhala/Tamil remain unsupported.

All fixture records are synthetic, including records named observations. No
live NASA access, agronomic validity, external source identity, LLM behavior,
network behavior, or cross-platform terminal behavior was tested or inferred.
The tests cover the enumerated questions and controlled missing-data variations;
they do not prove correctness for arbitrary language or every possible malformed
nested JSON document. There is still no API endpoint or full schema validator.

## Reproduce from the repository root

```powershell
python -m unittest discover -s backend/tests -v
python scripts/validate_data.py
python -m unittest backend.tests.test_assistant_qa.CLIQuestionTests backend.tests.test_assistant_qa.CLILifecycleTests -v
```

To run only the new QA suite (153 tests), or try the demo:

```powershell
python -m unittest backend.tests.test_assistant_qa -v
python backend/demo_assistant.py
```
