# API contracts — proposed v0.1

Owner: Dulanjaya. Reviewers: all module owners. These endpoints are not implemented. Use `/api/v1` and JSON; freeze changes together before independent development.

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
| POST `/farms/{id}/rotations` | `input_version`, `observation_id`, `seasons`, `catalog_version`, `priority_weights` | Immutable rotation analysis |
| POST `/analyses/{id}/scenarios` | `rainfall_change_pct` from -100 to 100 for the prototype | New hypothetical scenario linked to baseline, recalculated candidates and deltas |
| POST `/assistant/messages` | `farm_id`, `analysis_id`, optional `scenario_id`/`candidate_id`, `language` (`en`, `si`, `ta`), `message` | Explanation, source IDs, limitations; server verifies context IDs belong together |
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

The values above are invented. Live adapters must provide actual retrieval metadata, dataset identity/version, spatial resolution with units, aggregation method, and coverage. A missing variable is null with an explanation. Exact time-series fields are to be agreed with Matheesha before chart implementation.

## Analysis shape

Required fields: `analysis_id`, `farm_id`, `input_version`, `observation_id`, `catalog_version`, `model_version`, `data_kind`, `created_at`, `candidates`, `assumptions`, `source_refs`, and `limitations`.

Each candidate has `candidate_id`, `sequence` (season index and approved crop ID), `score`, `score_components`, `water_budget`, `reasons`, and `constraint_checks`. Score components disclose weights and direction. Water budgets disclose period, demand, rainfall, effective rainfall assumptions, irrigation supply, and deficit in consistent units. Do not use missing demand data as zero.

No feasible candidates is a valid successful response with `candidates: []` and reasons. This differs from a provider or computation failure. Score formulas and catalog values require Bhagya's approval before a complete numerical analysis fixture is published.

Scenario responses include `scenario_id`, `baseline_analysis_id`, parameters, recomputed candidates/metrics, baseline differences, and explicit hypothetical labels. Set effective rainfall consistently with the documented model; do not multiply the historical observation record in place.

## Errors and validation

```json
{"error":{"code":"VALIDATION_ERROR","message":"Area must be positive.","fields":{"area_ha":"Must be greater than zero."}}}
```

Use 400 for malformed requests, 404 for unknown resources, 409 for version/context conflicts, 422 for field/domain validation, and 503 for unavailable dependencies. Avoid exposing credentials/provider internals. Validate coordinate ranges, chronological dates, compatible units, catalog IDs, supported languages, three-to-five seasons, nonnegative weights with positive total, and relationships among farm/analysis/scenario/candidate IDs. Normalize priority weights on the server and return the effective weights.
