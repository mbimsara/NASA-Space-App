# Confirmed assistant contract handoff

Owner of explanation service: Akash. HTTP endpoint/resolution: Dulanjaya.
Frontend contract confirmed by Shehani. No HTTP route is implemented here.

## Python entry point

```python
from app.services.assistant_response import respond_to_request

response = respond_to_request(request_payload, resolved_context)
```

When importing from the repository root, use
`backend.app.services.assistant_response` instead. The existing
`explain(context, question, language="en") -> str` and the lower-level
`respond(context, question, language="en", **normalization_options)` remain
available.

The request is exactly:

```json
{
  "farm_id": "<persisted farm ID>",
  "analysis_id": "<persisted analysis ID>",
  "scenario_id": "<optional persisted scenario ID>",
  "candidate_id": "<optional stable candidate ID>",
  "language": "en",
  "message": "Explain water budgets"
}
```

`farm_id`, `analysis_id`, `language`, and `message` are required nonblank
strings. Optional selections may be omitted or null. Unknown request fields
are rejected, including client-supplied scientific context. The current service
limits messages to 2000 characters; mirror that limit in the HTTP schema.

`resolved_context` is supplied by the backend, not by the browser:

```python
resolved_context = {
    "id": farm.id,
    "input_version": snapshot_input_version,
    "profile": snapshot_farm_profile,
    "analysis": resolved_analysis,
    "observations": resolved_observation,
    "scenario": resolved_scenario,
}
```

Resolve/authorize the IDs before this call. Use the analysis's original farm
snapshot and input version rather than combining historical results with a
current edited profile. The service does not perform database lookups,
authorization, provider access, candidate generation, scoring, or ID allocation.

The supplied analysis must carry the requested `analysis_id` and `farm_id`.
Scenario IDs must match, and scenarios must link through the selected analysis
or, for rainfall-only scenarios, its exact observation snapshot. Unknown explicit
candidates are rejected; the service never substitutes the first candidate.
Omitting candidate selection means all candidates. Omitting scenario selection
excludes any scenario present in the caller's context, preventing stale UI/server
selections from leaking into an answer.

Bhagya dataclasses and Matheesha bundles are supported through the same
`candidate_ids`, `analysis_metadata`, `water_budgets`, and `scenario_metadata`
keyword options as `normalize_context`. Those options are server-side boundary
data, not additional request fields. See
[the normalization guide](app/services/ASSISTANT_INTEGRATION.md) for exact shapes.

## Response fields

Every successful call returns Shehani's required fields:

```json
{
  "role": "assistant",
  "content": "A deterministic explanation of supplied facts.",
  "source_ids": [],
  "limitations": []
}
```

Optional service fields currently included:

- `status`: `answered`, `insufficient_context`, or `unsupported_question`.
- `language`: `en` for successful responses.
- `assumptions`: relevant supplied assumption strings.
- `context`: validated farm/analysis/scenario/candidate IDs. Unavailable result
  IDs remain null; the request's IDs are not fabricated into result records.

Sources and supplied limitations/assumptions are captured from records actually
used during rendering. The service never extracts citations by searching prose.
It does not claim unselected candidate-budget sources. `source_ids` preserves
producer-supplied `source_refs` and supplied HTTP(S) `source_url` references
under the existing wrapper convention; it creates no registry IDs for URLs.
Analysis/farm IDs in the request do not automatically become source IDs.
If the backend requires registry-only IDs, it must supply that mapping before
rendering rather than inventing identifiers in the assistant.

Missing irrigation/soil inputs and absent analysis/scenario results add explicit
limitations. Signed balances remain signed and are not converted into deficit.
Effective rainfall is unknown when absent; no 80% factor or zero-irrigation
assumption is added. Empty candidate lists are valid results with supplied
reasons, not a computation failure.

## Unsupported languages: return 422 UNSUPPORTED_LANGUAGE

`UnsupportedLanguageError` is raised for `si` and `ta` (and other non-English
codes). It is a ValueError subclass, preserving existing error handling. It
provides `language`, `supported_languages == ("en",)`,
`code == "UNSUPPORTED_LANGUAGE"`, and `to_error_envelope()`.

Dulanjaya should catch this error **before** broader ValueError handlers and
return HTTP 422. This snippet is handoff documentation, not an added route:

```python
from fastapi.responses import JSONResponse
from app.services.assistant_errors import UnsupportedLanguageError

try:
    result = respond_to_request(request_payload, resolved_context)
except UnsupportedLanguageError as exc:
    result = JSONResponse(status_code=422, content=exc.to_error_envelope())
```

The envelope uses the backend's existing format:

```json
{
  "error": {
    "code": "UNSUPPORTED_LANGUAGE",
    "message": "Only English ('en') is supported in this milestone.",
    "fields": {
      "language": "Supported assistant languages: en. Sinhala (si) and Tamil (ta) are not implemented yet."
    }
  }
}
```

There is no silent English fallback labeled Sinhala/Tamil.

Other adapter errors expose the same envelope helper:

| Error | Suggested HTTP handling |
| --- | --- |
| `AssistantRequestError` | 422 `VALIDATION_ERROR` |
| `InvalidCandidateError` | 422 `INVALID_CANDIDATE` |
| `AssistantContextError` | 409 `CONTEXT_MISMATCH` |

Malformed producer/context payloads can still raise normalization
TypeError/ValueError. Backend-owned invalid data should be handled as an
integration/service problem, not blamed on the browser. Dulanjaya should not
expose raw provider exceptions.

An actually unknown resource remains a backend 404. Passing unavailable analysis
results to the service is different: it returns a limited successful response
with `status: insufficient_context`, meaningful limitations, and no invented
scores or recommendations. The backend decides whether its actual lookup means
not found, not ready, or a storage failure.

## Synthetic UI examples

[assistant-ui.synthetic.json](tests/fixtures/assistant-ui.synthetic.json)
contains seven examples with requests and executed expected responses/errors:

| Example ID | UI state |
| --- | --- |
| `missing-irrigation` | Unknown irrigation and unavailable analysis |
| `unranked-candidate` | Supplied sequence with unknown score/rank |
| `water-ranges-and-balances` | Demand range, signed balance, unknown effective rainfall |
| `constraint-report` | Reported constraint with unknown structured pass status |
| `rainfall-only-scenario` | Synthetic baseline versus hypothetical rainfall |
| `unsupported-sinhala` | Suggested HTTP 422 error envelope |
| `unsupported-tamil` | Suggested HTTP 422 error envelope |

`contexts` contains the synthetic resolved records; each example's `context_key`
selects one. All IDs and agronomic values are test data. None represent actual
retrieved NASA observations or approved recommendations. Expected responses are
UI snapshots; independent contract/fixture assertions also test numeric values,
units, selection, missing inputs and source handling.

The frontend can display `expected_response` or simulate the suggested 422
error until Dulanjaya implements the endpoint. These fixture IDs must not be
sent to a live database as if they identified real persisted records.

From the repository root:

```powershell
python -m unittest backend.tests.test_assistant_contract -v
python -m unittest discover -s backend/tests -v
python scripts/validate_data.py
```

Remaining blockers: HTTP integration, persistence/authorization, source registry
decisions, stable ID allocation, reviewed scoring/crop dates, UI range/unranked
support, and Sinhala/Tamil implementation and review.
