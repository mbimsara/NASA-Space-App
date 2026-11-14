# Assistant API

`POST /api/v1/assistant/messages` explains existing persisted facts. It reuses
Akash's deterministic English-only service; it is not a general conversational
LLM, translation service, agronomic adviser or NASA client.

Example using **explicitly synthetic test data**, with IDs replaced by those
returned by the local farm and rotation APIs:

```json
{
  "farm_id": "synthetic-farm-id",
  "analysis_id": "synthetic-analysis-id",
  "language": "en",
  "message": "What is the recorded irrigation supply?"
}
```

Optional `candidate_id` selects one existing candidate. Optional `scenario_id`
adds the selected hypothetical scenario. Empty IDs and blank messages are
invalid. Unknown body fields, including client-supplied context, are rejected.

For the repository's synthetic farm with unknown irrigation, the response is:

```json
{
  "role": "assistant",
  "content": "Context includes synthetic demonstration data, not actual NASA observations or validated agronomic advice. This profile contains synthetic demonstration inputs, not real farm observations. Irrigation supply is unknown.",
  "source_ids": [],
  "limitations": [
    "Context includes synthetic demonstration data, not actual NASA observations or validated agronomic advice."
  ],
  "status": "insufficient_context",
  "language": "en",
  "assumptions": []
}
```

The four frontend contract fields are `role`, `content`, `source_ids` and
`limitations`. Additive fields are `status`, `language` and `assumptions`.
Statuses are `answered`, `insufficient_context` or `unsupported_question`.
Successful explanations and supported empty/missing-data explanations return
HTTP 200. Responses use `Cache-Control: no-store`.

## Supported questions and language

Akash's keyword-based service explains recorded farm area/location, irrigation,
soil tests, history, priorities and exclusions, candidate sequences/scores/checks,
existing water budgets, hypothetical scenarios, observations and provenance.
"Show full analysis" requests all supplied analytical sections. It does not
infer a rank from array order or claim that heuristic scores are measurements.

Only `language: "en"` is supported. Sinhala (`si`), Tamil (`ta`) and other
languages return 422 / `UNSUPPORTED_LANGUAGE`; no English text is labeled as another
language. Translation and any future external LLM require a separate design.

Requests for crop recommendations, forecasts, yield predictions, fabricated
measurements, record edits or unsupported topics receive HTTP 200 with
`status: "unsupported_question"` and Akash's explicit limitation text. Questions
do not supply new trusted farm facts. Keyword routing has limited natural-language
understanding; it is not a general question-answering system.

## Context and provenance

The server resolves the farm and rotation analysis from SQLite, checks ownership
and input versions, and loads the exact saved observation snapshot. A supplied
scenario must belong to the same analysis and agree with its original farm,
observation, catalog/model versions and saved inputs. Candidate IDs must exist
in the selected baseline or scenario; scenario selection never falls back to a
candidate available only in the baseline. No saved-plan ID is accepted by this
request contract, and unrelated saved plans are not added to context.

Outdated analyses return 409 instead of combining historical results with a
new farm profile. Historical saved plans remain readable through their own API.
Observation cache expiry alone does not invalidate a matching saved snapshot.

The adapter maps persisted effective score weights to the explainer's `weight`
field, per-season `water_budget_range` to `water_budgets`, and keyed
`baseline_differences` to the explainer's list of supplied differences. Textual
water periods are retained as disclosed limitations while dates remain unknown;
no crop dates are inferred. No ranks, scores, water conversions, rainfall changes
or agronomic formulas are calculated. Unknown water results remain unknown.

Akash's rendering trace selects `source_ids` from the records actually rendered;
the server does not manufacture citations or label farmer-entered area as NASA
data. Supplied HTTP(S) URLs remain URLs. Optional missing references are disclosed
as unknown. Missing required observation snapshots or malformed provenance
produce 503. Synthetic context and selected hypothetical scenarios are disclosed
even for farm-only questions. Scenario explanations report stored parameters and
differences, never recalculate climate effects.

## Errors, storage and upstream ownership

| Condition | HTTP / code |
| --- | --- |
| Unknown farm, analysis, scenario or selected-result candidate | 404 / `NOT_FOUND` |
| Cross-farm, mismatched or inconsistent persisted references | 409 / `CONTEXT_CONFLICT` |
| Analysis input version differs from current farm | 409 / `VERSION_CONFLICT` |
| Unsupported language | 422 / `UNSUPPORTED_LANGUAGE` |
| Invalid body | 422 / `VALIDATION_ERROR` |
| Missing/malformed persisted data, failed normalization or database failure | 503 / `SERVICE_UNAVAILABLE` |

No new tables, migrations or message persistence are added. The endpoint reads
only; all farm, observation, analysis, scenario and plan records remain unchanged.
There are no live NASA or external AI requests.

The four modules `app/services/assistant.py`, `assistant_results.py`,
`assistant_normalization.py` and `assistant_response.py`, together with the
[upstream integration notes](app/services/ASSISTANT_INTEGRATION.md), are copied
byte-for-byte from `origin/akash-dev` commit
`9e13c4c8cb9bbb5dfb56089b0ca436ac00ce598d`. Their explanation and normalization
logic is unchanged. Database resolution, HTTP validation and shape adaptation
live separately in `assistant_context.py` and the API route. No teammate app,
crop catalog, crop formula or NASA algorithm is modified.
