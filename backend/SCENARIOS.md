# Climate Scenario API

`POST /api/v1/analyses/{analysis_id}/scenarios` creates a saved hypothetical
comparison against an existing immutable rotation analysis. HTTP 200 is returned
only after the scenario commits successfully.

For an explicitly synthetic test baseline, replace `analysis_id` with the ID
returned by the rotation API and send:

```json
{"rainfall_change_pct": -20}
```

The parameter must be a finite JSON number between -100 and 100, inclusive.
Zero and fractional changes are accepted. Booleans, strings, null, missing fields
and additional fields return 422 with the existing validation error envelope.
The percentage describes a hypothetical adjustment, not a forecast or an edit
to the historical NASA record.

Responses contain:

- `scenario_id`, `baseline_analysis_id`, `farm_id`, original `input_version`,
  `observation_id`, and `created_at` in UTC.
- `parameters`, `hypothetical: true`, `data_kind`, `catalog_version`, baseline
  `model_version`, and `scenario_model_version` (`climate-scenario-0.1`).
- `candidates` with baseline candidate IDs, sequences, supported scores,
  component weights, constraint checks, reasons and nullable water results.
- `baseline_differences`, keyed by baseline candidate ID. Each entry has
  `score_delta`, `water_budget_delta` and `water_budget_range_delta`.
- `reasons`, `assumptions`, `source_refs` and `limitations`.

Synthetic baselines retain `data_kind: synthetic`; other hypothetical outputs
use `modeled`. All responses explicitly identify the scenario as hypothetical.
An empty baseline from the current research-pending catalog returns
`candidates: []` and `baseline_differences: {}` with explanations. It never
creates new recommended crops from unapproved records.

## Calculation support and limitations

The service replays the existing `RotationService` against the **saved catalog,
farm profile, request and observation**, using Bhagya's unchanged candidate
generator and scorer. No live NASA access or current catalog loading occurs.
Only the recorded engine commit and supported model version are accepted.
Candidate IDs remain those of the baseline so differences are unambiguous.

Current saved rotations have no approved mapping between the single observation
date range and each crop-season demand period. Consequently the rainfall
parameter is saved but **cannot yet change water results**. Bhagya's existing
water functions require matching seasonal climate and approved demand inputs;
calling them with copied rainfall or invented demand would be invalid. Water
budgets and their differences remain null. No effective-rainfall model, water
cutoff, soil benefit or missing-irrigation default is added.

The currently computable crop-diversity score is independent of rainfall and is
recomputed with Bhagya's scorer. Its delta is zero when available. If no weighted
component is available, both score and score delta remain null. A zero diversity
score change must not be interpreted as zero climate impact. The current empty
production catalog yields no crop scores at all.

Numerical water scenarios require an approved seasonal climate/demand handoff
in the rotation baseline first. Unsupported saved numerical water models return
503 rather than silently erasing their results or improvising a conversion.

## Validation and persistence

Unknown analysis IDs return 404. Conflicting saved analysis/observation ownership
or input-version metadata returns 409. Missing baseline observations, malformed
snapshots/catalogs, irreproducible baseline candidates, unsupported engine/model
versions, computation failures and database failures return 503. Provider details
are not exposed. Invalid request parameters return 422. Missing approved crops
or unavailable seasonal climate are disclosed in successful partial/empty results
when the saved baseline itself remains reproducible.

Scenarios compare the original baseline, even after the farm is edited or the
observation cache expires. They do not represent a new analysis of current farm
inputs. Baseline profiles, results and observation snapshots are never updated.

Startup adds `climate_scenarios` using SQLAlchemy `create_all`, preserving all
existing tables and rows. Each row stores a stable UUID, indexed baseline foreign
key, parameters, baseline/input/observation snapshots and full response JSON.
Repeated POSTs create separate scenario records. Internal retrieval is available
through `Session.get(ClimateScenario, scenario_id)`; no new public GET endpoint,
saved-plan API or frontend changes are included.

Run all backend tests from the repository root with
`PYTHONPATH=backend python -m pytest backend/tests -q`, followed by
`python scripts/validate_data.py`. Test fixtures block live NASA access.
