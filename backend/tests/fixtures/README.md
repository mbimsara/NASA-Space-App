# Assistant formatter fixtures

`rotation_context.synthetic.json` is **synthetic test data only**. Its placeholder
crop IDs are not catalog entries. Scores, ranks, budgets, and differences are
invented to exercise text formatting, not approved agronomic calculations.
Nothing here establishes a crop recommendation or actual NASA measurement.

The public function remains `explain(context, question, language="en")` and
returns a string. Farm profiles and API `profile` envelopes still work unchanged.
For analytical questions, pass optional `analysis`, `scenario`, and
`observations` mappings in the context. An optional top-level `candidate_id`
filters candidates by exact ID. Omit it to explain all supplied candidates.

```python
import json
from pathlib import Path
from backend.app.services.assistant import explain

path = Path("backend/tests/fixtures/rotation_context.synthetic.json")
context = json.loads(path.read_text(encoding="utf-8"))
context["candidate_id"] = "candidate-test-a"
print(explain(context, "Compare the rainfall scenario and baseline water budgets"))
```

The API contract leaves several nested structures unspecified. These **local
formatter conventions** need agreement with Dulanjaya and Bhagya before API
integration; no shared endpoint or approved analysis fixture is changed:

- `analysis` is the baseline analysis described in `docs/API_CONTRACTS.md`.
  Candidate `rank` is optional and must be supplied; the formatter does not sort
  candidates, infer ranks from scores, or assume a score scale.
- `sequence` is a list of `{season_index, crop_id}` records. Crop IDs are shown
  verbatim; no crop names are looked up or invented.
- `score_components` maps names to `{value, weight, direction}` records.
- `water_budget` contains a `{start, end}` ISO-date `period`, `demand_mm`,
  `rainfall_mm`, `effective_rainfall_mm`, `irrigation_supply_mm`, `deficit_mm`,
  and a textual `effective_rainfall_assumption`. All depths are millimeters
  over that budget's period, not automatically "per season".
- `scenario` contains `scenario_id`, `baseline_analysis_id`, `data_kind`,
  `parameters: {rainfall_change_pct}`, and recomputed `candidates` in the same
  shape. The assistant never recalculates the budget or modifies observations.
- Optional scenario `differences` is a list of `{candidate_id, score_delta,
  water_budget}` records. Its water fields use the same `_mm` names and mean
  **scenario minus baseline**. Differences must be supplied; none are calculated.
  Comparisons require a loaded baseline with a matching ID. Conflicting IDs
  raise `ValueError` instead of combining unrelated results.
- `observations` is one observation summary in the contract's shape, not a list.
  Observation rainfall is kept separate from scenario inputs and model budgets.
- Each record carries its own `data_kind`, `source_refs`, and `limitations`;
  analysis/scenario records may also carry `assumptions`. References are echoed
  only as supplied IDs, not resolved citations or evidence verified by this
  service. An `observed` label alone does not independently verify NASA origin.

Missing/null values remain unknown; zero is preserved. Missing candidates differ
from an explicit empty list (no feasible candidates supplied). Missing ranks,
differences, references, and provenance are never inferred. Questions still use
keyword matching; requests for new recommendations or forecasts are unsupported.
API-level schema validation and source resolution remain future integration work.

## Focused questions and the interactive demo

Water questions such as "Explain water budgets" and "How much water is needed?"
show baseline budgets only, including periods, units, and effective-rainfall
assumptions. "Compare water deficits" shows baseline and hypothetical deficits
and the supplied differences. Scenario questions such as "What happens if
rainfall decreases?" compare supplied baseline/scenario results without
recalculating them. Ranking questions show supplied ranks, scores, and reasons;
asking for candidate details also includes sequences and score components.
Observation records appear only when requested, and a source-only question
shows provenance and metadata without repeating the numerical analyses.

Each focused view preserves its own synthetic-data label, source IDs,
assumptions, and limitations. Missing required candidate sections are disclosed
as unknown rather than silently treated as complete results. Multiple explicit
topics can be combined. Use "show full analysis" for all result sections.

From the repository root, run `python backend/demo_assistant.py`. The `help`
command lists examples. Use `candidate candidate-test-a` or
`candidate candidate-test-b` to select one candidate, `candidate all` to reset,
and `exit` to close. Selection changes only the in-memory demo context.

Questions may name an exact candidate ID or a unique single-character suffix
alias such as "candidate A". Aliases are derived from IDs, never ranks or list
positions. A question conflicting with an active selection, naming an unknown
candidate, or selecting multiple explicit IDs is declined. Explicit "only
baseline" and "only scenario" constraints in the same question are contradictory.

Forecasts (including tomorrow/next-week questions), invented facts/citations,
record edits, unit conversions, and new minimum/maximum rankings are unsupported.
For example, "Which rotation has the lowest supplied water deficit?" cannot
establish a new ranking; ask to display the supplied deficits instead.
"Effective rainfall" and candidate-specific irrigation questions use model
budgets; farm irrigation remains unknown in the original profile fixture.

`assistant_qa_cases.py` defines 72 independently checked questions across 12
categories. `test_assistant_qa.py` runs each question against both the assistant
and a real CLI subprocess. Missing-data variations use temporary fixture copies;
the checked-in JSON files are never changed by the tests. The initial and final
executed results, reproduction commands, and scope are recorded in
`backend/tests/QA_REPORT.md`.

Run all assistant tests from the repository root:

```powershell
python -m unittest discover -s backend/tests -v
```
