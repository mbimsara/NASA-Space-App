# API contracts — proposed v0.1

Owner: Dulanjaya. Reviewers: all module owners. Farm POST/GET/PATCH, health, observations, and rotation-analysis endpoints are implemented. Observations use Matheesha's NASA POWER adapter; rotations call Bhagya's shared domain package and persist immutable snapshots. Analysis scenarios, the deterministic assistant and immutable saved plans are implemented; see the canonical integration details below. Use `/api/v1` and JSON; freeze changes together before independent development.

The implemented climate functions and proposed serializer are documented in [the climate handoff](CLIMATE_HANDOFF.md). Its committed synthetic bundle is the current integration example. The observation serializer exposes separate temperature/rain coverage and the adapter's explicit `rainfall_total_mm` field; the simplified example below predates that implementation. Dulanjaya should adopt/review that payload when implementing the route rather than assume the abbreviated example is a complete schema.

## Conventions

WGS84 coordinates; hectares; millimeters; Celsius; ISO dates; timezone-bearing timestamps. Unknown values are `null`, never assumed zero. Responses carry `data_kind` (`observed`, `modeled`, `synthetic`, or `mixed`) where appropriate, source references, and assumptions. Never relabel synthetic fixtures as NASA observations.

Farm mutation input follows [the farm schema](../data/schemas/farm.schema.json). Server metadata is returned as `{ "id": "farm-demo-001", "input_version": 1, "profile": { ... } }`. Client-generated fixture IDs are examples only; the server allocates persistent IDs.

| Method / route | Input | Result |
| --- | --- | --- |
| POST `/farms` | Farm profile | 201: farm envelope |
| GET `/farms/{id}` | Farm ID | 200: farm envelope |
| PATCH `/farms/{id}` | `expected_input_version` and a complete replacement `profile` | 200: envelope with incremented version; 409 on version conflict |
| GET `/farms/{id}/observations?start=YYYY-MM-DD&end=YYYY-MM-DD` | Inclusive dates; start <= end | Observation summary below |
| GET `/observations/{observation_id}` | Persistent observation ID | 200: original immutable observation envelope; 404 if absent |
| POST `/observations/{observation_id}/rainfall-scenarios` | `rainfall_change_pct` from -100 to 100 | Hypothetical uniform scaling of the stored daily rainfall baseline; missing values are preserved and the snapshot is unchanged |
| POST `/farms/{id}/rotations` | `input_version`, `observation_id`, `seasons`, ordered `season_labels`, `catalog_version`, `priority_weights` | 201: immutable rotation analysis |
| POST `/analyses/{id}/scenarios` | `rainfall_change_pct` from -100 to 100 for the prototype | New hypothetical scenario linked to baseline, recalculated candidates and deltas |
| POST `/assistant/messages` | `farm_id`, `analysis_id`, optional `scenario_id`/`candidate_id`, `language` (`en`; `si`/`ta` return 422 `UNSUPPORTED_LANGUAGE`), `message` (1 to 2000 characters) | Explanation, source IDs, limitations; server verifies context IDs belong together |
| POST `/farms/{id}/plans` | `analysis_id`, optional `scenario_id`, `candidate_id`, `expected_input_version` | 201: saved plan ID and snapshot references |
| GET `/plans/{id}` | Plan ID | Saved candidate, input snapshot, sources, assumptions, model versions |

For the prototype PATCH requires the whole profile to avoid ambiguous nested merge behavior. A changed profile makes older analyses outdated; reads remain available, but saving as a current plan requires the expected version to match. Follow-on report/calendar/feedback endpoints will be specified when their schemas are agreed.

## Observation summary shape

```json
{
  "observation_id": "obs-demo-001",
  "farm_id": "farm-demo-001",
  "input_version": 1,
  "data_kind": "synthetic",
  "period": {"start": "2025-01-01", "end": "2025-01-31"},
  "retrieved_at": null,
  "source_refs": ["synthetic-fixture-v1"],
  "spatial_resolution": null,
  "coverage": {"expected_days": 31, "available_days": 31},
  "summary": {"rainfall_mm": 100, "mean_temperature_c": 27},
  "limitations": ["Invented values for interface development; not NASA data."]
}
```

The values above are invented. The implemented POWER response extends this abbreviated example
with Matheesha's normalized `daily`, `monthly`, source/API/parameter metadata and provider
coordinates; see [backend integration details](../backend/README.md#climate-observations).
`summary.rainfall_mm` aliases `rainfall_total_mm`. Coverage includes separate
`temperature_valid_days` and `precipitation_valid_days`; `available_days` counts days with
both variables present. `missing_data` lists missing dates separately per variable.
POWER retains `data_kind: modeled`, not observed. Full-period rainfall is null when any
rainfall day is missing; partial sums are labeled separately. Units and aggregation descriptions
are explicit. Provider resolution and retrieval time remain null when unknown. API metadata
must not be interpreted as a source dataset release version. Observation IDs now identify persisted immutable snapshots in `observation_snapshots`.
Repeated requests for the same farm/version, coordinates, period and provider settings reuse a
fresh snapshot (default 24 hours). Expiry or a farm edit creates a new snapshot; old IDs remain
readable by `/observations/{observation_id}`. Source retrieval timestamps are never replaced by
cache-hit times. Expired refresh failures return 503, without silent stale or synthetic fallback.
Responses include `X-Observation-Cache` and `X-Observation-Expires-At` headers.

Future rotation analyses should reference the persisted snapshot ID and validate farm ownership
and the current expected input version using `require_observation_for_analysis`. Unknown IDs
map to 404, and mismatched/outdated farm versions to 409. Expiry alone does not invalidate a
historical reference. Recheck the farm version when committing an analysis result.

Both dates are required in exact YYYY-MM-DD form with
`1981-01-01 <= start <= end < today (UTC)`. Unknown farm strings return 404; invalid query
fields/dates return the existing 422 envelope. Disabled, absent or failed services return
503 with error code `SERVICE_UNAVAILABLE` when no fresh matching cache exists. Storage failures
also return 503. Partial coverage is a 200 response with disclosed
null values and limitations, never synthetic fallback data.

## Analysis shape

Required fields: `analysis_id`, `farm_id`, `input_version`, `observation_id`, `catalog_version`, `model_version`, `data_kind`, `created_at`, `candidates`, `assumptions`, `source_refs`, and `limitations`.

Each candidate has `candidate_id`, `sequence` (season index and approved crop ID), `score`, `score_components`, `water_budget`, `reasons`, and `constraint_checks`. Score components disclose weights and direction. Water budgets disclose period, demand, rainfall, effective rainfall assumptions, irrigation supply, and deficit in consistent units. Do not use missing demand data as zero.

For `rotation-score-0.1`, return `water_budget_range` per season/crop rather
than one opaque plan-level value. Each record includes demand low/high,
baseline/scenario rainfall, entered irrigation, conservative coverage and
balance ranges, demand basis, water-model version, assumptions, and
limitations. A plan aggregate is optional and must not replace per-season
records.

Until an effective-rainfall method is reviewed, preserve historical
`rainfall_total_mm`, return `effective_rainfall_mm: null`, and disclose that
total rainfall is used only for provisional screening. Do not expose a
placeholder effective-rainfall fraction as approved output.

Irrigation is nullable. When known, send
`irrigation_basis: "field_applied_depth"`; when unknown, send both irrigation
value and basis as `null`. A literal zero is a known zero, not missing data.
Unknown irrigation makes water-budget outputs and water-based score components
null rather than silently creating a rainfed assumption.

Score components are `water_sufficiency`, `crop_diversity`, and nullable
`scenario_resilience`, as specified in
[`ROTATION_SCORING_SPEC.md`](ROTATION_SCORING_SPEC.md). Return requested and
effective weights. Constraint checks use `{ "rule", "passed", "note" }`.
The score is a heuristic comparison, not a yield prediction.

No feasible candidates is a valid successful response with `candidates: []` and reasons. This differs from a provider or computation failure. Score formulas and catalog values require Bhagya's approval before a complete numerical analysis fixture is published.

Scenario responses include `scenario_id`, `baseline_analysis_id`, parameters, recomputed candidates/metrics, baseline differences, and explicit hypothetical labels. Set effective rainfall consistently with the documented model; do not multiply the historical observation record in place.

## Errors and validation

```json
{"error":{"code":"VALIDATION_ERROR","message":"Area must be positive.","fields":{"area_ha":"Must be greater than zero."}}}
```

Use 400 for malformed requests, 404 for unknown resources, 409 for version/context conflicts, 422 for field/domain validation, and 503 for unavailable dependencies. Avoid exposing credentials/provider internals. Validate coordinate ranges, chronological dates, compatible units, catalog IDs, supported languages, three-to-five seasons, nonnegative weights with positive total, and relationships among farm/analysis/scenario/candidate IDs. Normalize priority weights on the server and return the effective weights.

## Canonical assistant and saved-plan integration

See [the integration handoff](ASSISTANT_SAVED_PLANS_INTEGRATION.md) for the implemented
request/response fields, canonical snapshot tables, controlled errors and offline tests.
The existing farm-scoped plan POST and plan GET remain compatible with the frontend.
POST `/plans` additionally accepts `farm_id` in the body; GET `/plans` requires a
`farm_id` query and supports `limit`/`offset`. Saved plans include full immutable
`analysis_result_snapshot`, `scenario_snapshot` and `observation_snapshot` fields,
while retaining the frontend's `input_snapshot`, `candidate_snapshot` and
`analysis_snapshot` metadata. No scientific calculations or calendar dates are inferred.

## Selective backend safeguards

Rotation `input_version` and `seasons` require JSON integers; booleans, numeric
strings and floats return 422. Valid frontend integer requests are unchanged.
Saving a rotation atomically rechecks the farm version while holding the SQLite
writer lock; an edit before insertion returns 409 `VERSION_CONFLICT` without
saving an outdated analysis. Existing result schemas and scenario behavior remain.

Assistant responses additionally retain selected-context synthetic/hypothetical
warnings in `limitations` even for farm-only questions. The explanation and
rendered-evidence source selection remain unchanged. See
[review decisions and verification](DULANJAYA_BACKEND_REVIEW.md).
