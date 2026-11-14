# Assistant integration phase 1

These are pure Python integration adapters, not an HTTP contract or database
resolver. They use only the standard library and do not import teammate apps,
call providers, run crop calculations, or allocate IDs.

Shehani has now confirmed the request and four required response fields.
`respond_to_request(request, resolved_context, **boundary_options)` implements
that assistant-side boundary. See [the backend handoff](../../ASSISTANT_HANDOFF.md)
for required IDs, controlled missing-result behavior, the typed language error,
and seven synthetic UI examples. Dulanjaya still owns the HTTP endpoint.

Inspected remote-tracking snapshots:

- Bhagya `zerokali20`: `454b4c1bc73cbabdf235b98d803aaf137a916666`.
- Matheesha `matheesha/nasa-power-integration`: `c580b4fc620212f5450e388ed951e7cef5c014f6`.
- Dulanjaya `dulanjaya/backend`: `f6a7d24d0ca76f2aa87c79635f8b0b911de9e702`.
- Shehani `branch-shehani`: `03a46b7718c4d7802baeedd8cfc6d5de8f612d4a`.

## Public entry points

The original `assistant.explain(context, question, language="en") -> str` still
works with its existing fixture context. To consume new teammate outputs, use
`normalize_context` before `explain`, or use the new `respond` wrapper:

```python
from backend.app.services.assistant_normalization import normalize_context
from backend.app.services.assistant import explain
from backend.app.services.assistant_response import respond

context = normalize_context(teammate_context, **boundary_options)
text = explain(context, "Explain water balances")
response = respond(teammate_context, "Explain water balances", **boundary_options)
```

Inputs may be mappings, stdlib dataclasses (including frozen/slots classes), or
already-created Pydantic models exposing `model_dump(mode="json")`. The adapters
produce independent dictionaries/lists, serialize dates as ISO strings, and do
not modify inputs. No Pydantic installation is needed to import or test them.

Run this complete offline example from the repository root:

```python
import json
from pathlib import Path
from backend.app.services.assistant_response import respond

fixture = json.loads(Path(
    "backend/tests/fixtures/teammate-climate.synthetic.json"
).read_text(encoding="utf-8"))
response = respond(fixture["climate_bundle"], "What happens if rainfall decreases?")
print(json.dumps(response, indent=2, ensure_ascii=False))
```

This example is explicitly synthetic, not a NASA retrieval.

## Bhagya: unranked generation and stable IDs

Pass `CandidateGenerationResult` under `analysis`. The coordinator must supply
`candidate_ids`, an ordered list containing one stable ID per generated
candidate. The assistant never creates an ID from a position, crop name, rank,
hash, or UUID. Existing JSON candidates with IDs do not require this option.
Duplicate, conflicting, blank, or missing IDs are rejected.

```python
context = normalize_context(
    {"analysis": generation_result},
    candidate_ids=server_candidate_ids,
    analysis_metadata=persisted_analysis_metadata,
    water_budgets=explicit_budget_bindings,
)
```

`analysis_metadata` may carry actual `analysis_id`, `farm_id`, `input_version`,
`observation_id`, `data_kind`, `catalog_version`, `model_version`, `score_kind`,
`source_refs`, `assumptions`, and `limitations`. Supply values from the producer
or persistence boundary. Unknown versions and provenance stay unknown. Metadata
cannot silently overwrite a different supplied value.

Ordered `crop_ids` become sequence steps with one-based indices. Existing step
metadata is retained when the ordered crop IDs agree. These indices describe
sequence positions, not ranks. Missing scores and ranks remain absent. Tuples
become lists. Constraint strings become reports with `passed: null`; a string
does not independently establish a structured pass/fail result. Existing
`{rule, passed, note}` checks preserve explicit booleans, notes and evidence.

`score_kind: "heuristic"` is distinct from `data_kind`. A heuristic score is not
a measured quantity. The adapter preserves explicit components and may convert
a list of named components to the formatter's name-keyed mapping; it never
computes a score or infers a ranking from list order.

The merged `rotation-score-0.1` components retain and explain
`requested_weight` and `effective_weight` separately. Null and zero remain
distinct. The legacy `weight` field is still supported; it is not relabeled as
either new field. The assistant validates supplied weights but never normalizes
them, derives an effective weight, or recalculates the total score.

## Water quantities and explicit crop/season binding

`normalize_water_budget(value, period=..., metadata=...)` accepts Bhagya's
`WaterBudget`, `WaterBudgetRange`, or `WaterDemandRange` shapes:

- `crop_demand_mm` is also exposed as `demand_mm`.
- `irrigation_mm` is also exposed as `irrigation_supply_mm`, preserving null/zero.
- Demand-only `low_mm`/`high_mm` become `demand_low_mm`/`demand_high_mm`.
- Signed `balance_mm`, `balance_low_mm`, `balance_high_mm`, coverage percentages,
  total/scenario rainfall, demand basis, model version and assumptions remain
  supplied values. Nominal demand remains a reference, never a substitute for a
  range.
- No balance-to-deficit conversion, midpoint calculation, range aggregation,
  effective-rainfall calculation or default 80% factor is applied. An absent
  deficit or effective-rainfall value is unknown.
- Budget periods accept `{start, end}` ISO dates or a nonblank descriptive
  string, such as `"3-season aggregate"`. A string becomes
  `{"label": "3-season aggregate", "start": null, "end": null}`. A period object
  may also retain a supplied `label`. Explanations show the label and supplied
  dates separately; missing dates stay unknown. Observation and rainfall-only
  scenario periods still require date objects. Water depths must already be mm;
  conversions are not performed.

Engine budget dataclasses omit dates and some source metadata. The coordinator
must retain those from the corresponding climate/demand inputs:

```python
from backend.app.services.assistant_normalization import normalize_water_budget

budget = normalize_water_budget(
    engine_budget,
    period=actual_crop_period,
    metadata={
        "crop_id": actual_crop_id,
        "season_index": actual_season_index,
        "data_kind": supplied_budget_kind,
        "source_refs": supplied_source_references,
        "limitations": supplied_water_model_limitations,
    },
)
explicit_budget_bindings = {stable_candidate_id: [budget]}
```

Bindings are keyed by supplied candidate IDs. Optional season indices and crop
IDs are checked against that candidate's sequence. Multiple crop-cycle budgets
are rendered separately as `water_budgets`; they are never silently treated as
one whole-rotation total. Budget source URLs can be retained as supplied URLs;
the wrapper does not create citation registry IDs for them.

The merged API/frontend field `candidate.water_budget_range` accepts either a
list of per-season records or the older single record. It is also exposed as
the formatter's `water_budgets` list, preserving order, crop/season identities,
units, dates/labels, signed balances, assumptions and sources. Missing season
indices are not filled from array order. Null means unavailable; an empty list
means no supplied season budgets. If both aliases are supplied, their normalized
values must agree. A separately supplied optional aggregate remains in context
but never replaces the per-season explanation or contributes unrendered sources.

## Rotation scenario differences

The merged frontend's scenario shape is supported directly:

```python
scenario = {
    # These IDs must come from resolved records.
    "scenario_id": persisted_scenario_id,
    "baseline_analysis_id": persisted_analysis_id,
    "candidates": supplied_scenario_candidates,
    "baseline_differences": supplied_differences_by_candidate_id,
}
```

`baseline_differences[candidate_id].score_change` is exposed as
`differences[*].score_delta`, retaining the original field and supplied candidate
ID. Supplied `rank_baseline` and `rank_scenario` are explained separately; they
do not assign a rank to a candidate missing its own rank. Other supplied fields
and difference-record sources, assumptions and limitations are preserved.
Signed, zero and null score differences stay unchanged; scores are never
subtracted by the assistant. A missing difference remains unknown.

Mapping keys must be nonblank candidate IDs and match an explicit row ID, when
present. With available scenario candidates, mapping keys must identify those
candidates. Legacy `differences` lists remain supported. If both representations
are supplied, they must agree after alias normalization; conflicts and duplicate
IDs are rejected. Normalization is safe to repeat and does not mutate inputs.

## Matheesha and Dulanjaya: observations and rainfall-only scenarios

`normalize_context` accepts Matheesha's `climate_bundle` (`observation` and
`rainfall_scenario`) or an explicit context with `observations` and `scenario`.
Other bundle sections are retained but not interpreted as crop advice.

`normalize_observation` accepts both raw normalized POWER output and envelopes:

- `sources` aliases to `source_refs`.
- `summary.rainfall_total_mm` aliases to `summary.rainfall_mm`, including null.
  Conflicting aliases are rejected; available-days rainfall is never used as
  the complete-period total.
- Coverage, provider, units, retrieval time, resolution, missing-data metadata,
  daily/monthly arrays, API metadata and limitations are retained. Counts and
  period length must agree; incomplete rainfall cannot have a non-null full
  total. Temperature means keep their producer's available-day semantics.

Dulanjaya's HTTP response already supplies the rainfall alias, identifiers and
coverage. Already-instantiated Pydantic responses can be passed directly. The
adapters do not start his application or open its database.

`normalize_rainfall_scenario` preserves `kind: hypothetical_rainfall_scenario`,
the supplied change, baseline/scenario totals, difference, coverage and
assumptions. It links to a supplied observation's provenance and dates when
available, checking IDs, period, provenance, and baseline rainfall consistency.
It does not allocate a scenario/analysis ID or add candidates. Standalone
scenarios with missing metadata remain explicitly unknown.

NASA POWER inputs labeled `modeled` remain modeled. Farmer profiles labeled
`farmer_input` remain farmer-entered. Synthetic fixture labels are retained.
Hypothetical status is separate from the baseline data kind; it is never
presented as a forecast or measured rainfall. The adapter cannot independently
verify a caller's provenance claim or source URL.

## Structured responses and errors

`respond(...)` returns Shehani's required `role`, `content`, `source_ids`, and
`limitations`, plus `status`, `language`, and `assumptions`.

Evidence is captured while rendering the selected sections/candidates. Source
IDs and notes are not extracted from prose, and sources of unrendered budgets
or unselected candidates are not included. Supplied HTTP(S) source URLs are
retained as references, not relabeled with fabricated IDs.

Statuses are `answered`, `insufficient_context`, or `unsupported_question`.
These are intentionally coarse: an answer may contain some unknown optional
fields; no claim of complete agronomic validation is made. Explicit empty
candidate lists remain successful, with their supplied reasons.

Malformed structures raise TypeError/ValueError. Unsupported languages raise
`UnsupportedLanguageError`, a ValueError subclass; no English response is labeled
Sinhala/Tamil. Dulanjaya should map it to 422 `UNSUPPORTED_LANGUAGE` using its
`to_error_envelope()` method, as documented in the handoff.

## Remaining boundary agreements

- Stable candidate, analysis and scenario IDs, snapshot storage and ownership.
- Exact crop-cycle dates, rainfall windows, irrigation entry basis and per-season
  bindings. Structural validation does not validate agronomic applicability.
- Verify Shehani's range/balance UI and nullable scores/ranks against actual
  backend records, including constraint reports with unknown pass status.
- Source registry conventions and which source URLs belong to each calculation.
- Any future effective-rainfall or deficit formula requires Bhagya's approval.
- HTTP implementation of the confirmed response/error contract and verification
  of unsupported-language UI behavior against that endpoint.

No HTTP routes, database code, LLMs, provider requests, or scientific formulas
were added. `python -m unittest discover -s backend/tests -v` runs legacy and
compatibility tests; `python scripts/validate_data.py` validates shared data.
The compatibility suite uses copied synthetic climate data and representative
dataclasses/model stubs, not live NASA data or teammate application execution.
