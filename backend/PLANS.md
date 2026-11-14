# Saved Plans API

Saved plans select existing persisted candidates. These endpoints do not generate
recommendations, call NASA, or rerun scientific calculations.

## Save a plan

`POST /api/v1/farms/{farm_id}/plans`

Example for an **explicitly synthetic test farm, approved test catalog and
persisted test candidate**. Replace these illustrative IDs with real API IDs:

```json
{
  "analysis_id": "synthetic-analysis-id",
  "candidate_id": "synthetic-candidate-id",
  "expected_input_version": 1
}
```

To select a hypothetical scenario candidate, also supply
`"scenario_id": "synthetic-scenario-id"`. Omission or JSON null selects the
baseline. Empty scenario strings are invalid. The candidate must exist in the
selected result; the API never falls back from a scenario to its baseline.

Successful creation returns **201** only after the database commit:

```json
{"plan_id": "server-generated-plan-uuid"}
```

Identifiers must be nonempty strings. `expected_input_version` must be a positive
JSON integer; booleans, strings and fractions are rejected. Unknown fields are
rejected. Each successful POST creates a new immutable plan with its own UUID;
repeated requests are not deduplicated.

## Reopen a plan

`GET /api/v1/plans/{plan_id}` returns **200** with the original snapshots.
The response is compatible with Shehani's `SavedPlan` TypeScript interface.
This synthetic response **excerpt** illustrates the identifying fields:

```json
{
  "plan_id": "server-generated-plan-uuid",
  "farm_id": "synthetic-farm-id",
  "analysis_id": "synthetic-analysis-id",
  "scenario_id": null,
  "candidate_id": "synthetic-candidate-id",
  "input_version": 1,
  "observation_id": "synthetic-observation-id",
  "created_at": "2026-11-14T12:00:00Z"
}
```

The complete response additionally contains:

- `candidate_snapshot`: the selected candidate verbatim, including sequence,
  nullable scores/water budgets, score components, reasons and constraint checks.
- `input_snapshot`: the complete farm profile used by the original analysis.
- `analysis_snapshot`: catalog/model versions, source references, assumptions,
  limitations, data kind and original `analysis_created_at`. For a scenario plan,
  the selected scenario's metadata preserves its additional hypothetical warnings.
- `scenario_snapshot`: the complete original scenario response, including
  parameters, `hypothetical`, scenario model version and baseline differences;
  null for a baseline plan.
- `observation_snapshot`: the historical observation response with original
  period, provider metadata, retrieval timestamp, coverage and limitations.

The GET endpoint reads only the saved plan row. Later farm edits, catalog changes,
model changes and observation cache expiry do not change a saved response. It
does not revalidate the historical plan against today's catalog or farm version.
Responses have `Cache-Control: no-store`.

## Relationships, versions and scientific restrictions

Saving requires an existing farm and analysis owned by that farm, with both the
current farm version and the analysis input version matching the expected version.
A supplied scenario must reference the same baseline and original farm/version,
observation, catalog and model. Its persisted input snapshots must agree with
the baseline. The candidate must belong to the selected result; scenario sequences
must match the original baseline sequence under the current scenario contract.

The selected candidate must retain support in the **original saved catalog**:
catalog-wide review, individual approval, season eligibility and farm exclusions
are checked without adding agronomic rules or changing algorithms. Current
research-pending empty analyses cannot be turned into saved plans by inventing
a candidate. Null metrics, synthetic labels and hypothetical limitations remain
unchanged. Saving a plan does not imply agronomic validation or field suitability.

After validation, an atomic conditional no-op farm update rechecks the expected
version and acquires SQLite's writer lock through the plan insert and commit.
A concurrent farm edit causes 409 and no plan is saved; the guard does not
increment the farm version or alter its profile.

| Condition | Status / code |
| --- | --- |
| Unknown farm, analysis, scenario, candidate in selected result, or plan | 404 / `NOT_FOUND` |
| Wrong farm/analysis/scenario/observation relationship or invalid approval context | 409 / `CONTEXT_CONFLICT` |
| Outdated request/analysis version or concurrent farm edit | 409 / `VERSION_CONFLICT` |
| Missing/invalid fields, empty IDs or invalid version type | 422 / `VALIDATION_ERROR` |
| Missing required persisted observation, malformed snapshot or storage failure | 503 / `SERVICE_UNAVAILABLE` |

Errors use the existing `{ "error": { "code": "...", "message": "..." } }`
envelope, with validation fields where applicable. No private database details
are returned.

## Storage and compatibility

SQLAlchemy startup adds `saved_plans` through `create_all`. Existing farm,
observation, rotation and scenario tables and records are preserved. Plan rows
contain stable IDs, foreign keys to all original records, original input version,
selected candidate ID, immutable response JSON and internal provenance JSON.
Internal provenance includes the complete original baseline and rotation inputs
(including catalog contents and pinned engine commit) plus scenario inputs.
The response also carries copied observations so reopening does not depend on
the observation cache or analytical services.

No update/delete/list endpoints or AI Assistant are added. Current crop-approval
and seasonal water-alignment limitations remain unchanged; successful tests use
explicit synthetic catalogs, not newly approved production recommendations.
