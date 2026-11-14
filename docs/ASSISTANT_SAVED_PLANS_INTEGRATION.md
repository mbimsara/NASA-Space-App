# Assistant and saved-plan integration on canonical main

This feature starts directly at main commit
431b5a540087b4dc8dd524ffc79afb93f8834cc8. It does not merge the legacy
integration branch or introduce its persistence tables.

## Reused code and scope

The five deterministic assistant service modules, CLI, seven original test
modules and synthetic formatter fixtures were selectively copied from f1c1738.
Their tested request wrapper is the same interface used by integration 8816cd5.
The normalizer/formatter additionally validate and explain main's supplied
observation_rainfall comparison. They do not calculate its values.

New code consists of two route modules, strict request/response schemas, a shared
canonical snapshot resolver, saved-plan persistence and integration tests.
Main's farm, observation, rotation and scenario models/services and all scientific
domain calculations remain unchanged. The only existing application wiring change
registers the routers and maps unsupported assistant languages. CI additionally
includes the repository root for the original assistant test imports.

## Task 2: Assistant API

POST /api/v1/assistant/messages accepts:

    {
      "farm_id": "<persisted farm>",
      "analysis_id": "<persisted canonical analysis>",
      "scenario_id": "<optional persisted analysis scenario>",
      "candidate_id": "<optional stable candidate ID>",
      "language": "en",
      "message": "What happens if rainfall decreases?"
    }

Maximum message length: 2000 characters. No client-supplied context is accepted.
The route calls respond_to_request(request.model_dump(), resolved_context).
The resolver uses rotation_analysis_snapshots, rotation_scenario_snapshots and
observation_snapshots directly. Original JSON is validated on copies and is not
rewritten into legacy scientific structures.

All responses contain role='assistant', content, source_ids and limitations.
Optional status, language, assumptions and context identify the selected records.
References come from selected structured evidence, including supplied URLs;
explanation text is never scraped for citations. Farm-only answers may have no
source IDs when the farm supplied none.

English is the only implemented language. Sinhala (si) and Tamil (ta), as well
as other unsupported language strings, receive HTTP 422 with the existing
error envelope and code UNSUPPORTED_LANGUAGE. Missing/invalid fields use
VALIDATION_ERROR. Unknown selected records/candidates return 404 NOT_FOUND;
cross-farm/scenario relationships return 409 CONTEXT_MISMATCH; an outdated
analysis returns 409 VERSION_CONFLICT. Unavailable or inconsistent persisted
context returns a controlled 503 SERVICE_UNAVAILABLE.

Requested/effective weights remain separate. No candidate rank is inferred from
array order or scores. Seasonal water ranges and signed balances retain mm,
sources, assumptions and unknown dates. Seasonal budgets take precedence over
an optional scalar aggregate (the original assistant contract); the aggregate
is still retained unmodified in stored snapshots. Descriptive scalar periods are
accepted without invented dates. Whole observation-period scenario totals are
explained separately from future-season water inputs. Candidate-keyed
score_change values preserve their candidate identity. No balance-to-deficit
formula, effective-rainfall factor, forecast or recommendation is introduced.

The standalone explain(context, question, language='en') interface is unchanged.
The standalone demo remains runnable with python backend/demo_assistant.py.
Its fixtures and the UI examples in backend/tests/fixtures/assistant-ui.synthetic.json
are invented test data, never actual NASA retrievals.

## Task 3: Saved-plan API

Main had no saved-plan routes or table at this base. The implementation preserves
the existing frontend call:

- POST /api/v1/farms/{farm_id}/plans
- POST /api/v1/plans (same request with farm_id in the body)
- GET /api/v1/plans?farm_id=...&limit=20&offset=0 (array, maximum limit 100)
- GET /api/v1/plans/{plan_id}

Creation requires analysis_id, candidate_id, expected_input_version, and optionally
scenario_id. Success is HTTP 201 with {"plan_id": "..."}.
Unknown IDs return 404, relationship/version conflicts 409, malformed requests 422,
and inconsistent stored context/storage failures 503.

A new append-only saved_plan_snapshots table references only main's canonical
farm, analysis, scenario and observation tables. App startup creates this additional
table through the existing SQLAlchemy metadata/lifespan convention; it does not
alter those existing tables or migrate legacy integration databases.

Creation validates the farm version, analysis ownership, observation/farm snapshot
identity, selected candidate, scenario baseline/version/observation/sequence,
provenance and observation-period comparison. A conditional farm-version check
inside the write transaction rejects a farm edit between validation and insertion.
There are no plan edit/delete endpoints.

Retrieval preserves the frontend fields:

- input_snapshot: original farm profile from the observation snapshot.
- candidate_snapshot: exact selected baseline or hypothetical scenario candidate.
- analysis_snapshot: source/assumption/limitation/model metadata plus
  analysis_created_at, as expected by Shehani's current UI.

Additive fields make the full historical records available to reports, calendars
and offline clients:

- analysis_result_snapshot: full original baseline analysis.
- scenario_snapshot: full selected hypothetical scenario, or null.
- observation_snapshot: original observation payload, including coverage,
  units, provider metadata and source references.
- observation_id: the selected canonical observation identity.

Reads validate embedded identity and snapshot consistency; they do not fetch
observations, read the current catalog, or substitute a changed farm profile.
The JSON can be cached by the existing frontend offline mechanism. No crop
calendar dates or irrigation schedules are generated; only originally supplied
farmer dates and model outputs are retained.

The full analysis request/catalog input bundle was not persisted by main.
The plan metadata discloses this limitation; it does not reconstruct those
historical inputs from today's catalog. Exact producer payloads remain intact.
Farm scoping follows main's prototype conventions; this change does not introduce
a new authentication or ownership system.

## Verification and reproduction

Use the documented backend installation (including the local rotation package)
and frontend locked dependencies. No additional application dependency is needed.
These local checks used synthetic fixtures only. Backend tests mock NASA access;
pytest-socket additionally restricts network access. The real HTTP test binds
only to loopback and runs the actual app against temporary SQLite.

From the repository root in an activated backend environment, PowerShell:

    $env:PYTHONPATH = "$PWD\backend;$PWD"
    $env:PYTHONDONTWRITEBYTECODE = "1"
    $env:NASA_POWER_ENABLED = "false"
    $env:DATABASE_URL = "sqlite:///:memory:"
    python -m pytest backend/tests --allow-hosts=127.0.0.1,::1 -ra
    python -m unittest discover -s backend/tests -p "test_assistant*.py" -v
    python -m pytest backend/tests/test_canonical_assistant_plans.py --allow-hosts=127.0.0.1,::1 -v
    python -m pytest backend/tests/test_canonical_assistant_plans.py -k real_loopback_http_journey --allow-hosts=127.0.0.1,::1 -v
    python -m pytest tests --disable-socket --allow-unix-socket -ra
    python scripts/validate_data.py
    npm --prefix frontend test
    npm --prefix frontend run typecheck
    npm --prefix frontend run build
    npm --prefix frontend run lint

On Linux, PYTHONPATH uses ':' instead of ';'. The backend CI retains its
--disable-socket --allow-unix-socket flags; only the explicit real-HTTP test
allows loopback via a pytest marker. Windows asyncio uses loopback socketpairs,
so the local backend run uses the loopback allowlist for all tests.

The real TCP test creates a farm, retrieves a synthetic observation, generates a
canonical analysis, creates a hypothetical scenario, asks the assistant, checks
both unsupported languages, saves a selected plan, retrieves every full snapshot,
edits the farm and verifies the saved plan is unchanged. Other regressions cover
baseline saves, list pagination, missing/zero inputs, source URLs, range units,
signed balances, unknown rankings, 404/409/422/503, atomic version checking and
corrupt persisted context. Separately passing module suites are not the only
integration evidence.

Local-only environments, copied node_modules, build outputs, databases and QA logs
are excluded from the feature commit. Publishing or opening a pull request is a
separate step requiring approval.

## Executed local results

Final code verification on 2026-11-14 (Windows, Python 3.13):

| Check | Actual result |
| --- | --- |
| Complete backend suite | 492 passed, 0 failed; 195 unittest subtests passed |
| Original assistant tests | 316 passed separately; also included in the final backend run |
| New canonical API/SQLite regressions | 57 passed, included in the backend total |
| Existing main backend cases | 119 passed, included in the backend total |
| Real loopback HTTP journey | Passed, included in the 57 new cases |
| Frontend unit tests | 102 passed across 13 files |
| TypeScript / production build / lint | All exit 0 |
| Shared rotation/climate tests | 61 passed, 2 skipped (optional HDF5 dependency absent) |
| Shared data validator | PASS |

The distinct Python/backend/shared/frontend test total is 655 passed, 0 failed,
2 skipped, plus 195 unittest subtests. Repeated assistant runs are not added to
that total. The backend emits a Starlette/httpx deprecation warning; dependencies
were not changed to suppress it. Linux/GitHub CI and a browser-driven UI journey
were not executed locally; the real TCP API journey and existing frontend tests
provide separate, explicitly bounded evidence. No actual NASA data was retrieved.

No integration blocker was found for Tasks 2 and 3 in these checks. Main's draft
crop catalog and missing dated future-season inputs still constrain real agronomic
results; the tests use an explicitly synthetic approved test catalog, and unavailable
scientific values remain unknown. Sinhala/Tamil remain deliberately unsupported.
The original full analysis request/catalog bundle remains unavailable and is disclosed.

Commit preparation is limited to feature/assistant-saved-plans-final. Existing
team branches are preserved; publishing and merging require separate approval.

## Review manifest

The four existing-file edits are application router/error wiring, the backend CI
import path, backend README status and API contract documentation. Remaining files
are the selective assistant import, canonical integration, test assets and this handoff.

- `.github/workflows/backend-tests.yml`
- `backend/README.md`
- `backend/app/api/routes/assistant.py`
- `backend/app/api/routes/plans.py`
- `backend/app/main.py`
- `backend/app/models/plan.py`
- `backend/app/schemas/assistant.py`
- `backend/app/schemas/plan.py`
- `backend/app/services/assistant.py`
- `backend/app/services/assistant_context.py`
- `backend/app/services/assistant_errors.py`
- `backend/app/services/assistant_normalization.py`
- `backend/app/services/assistant_response.py`
- `backend/app/services/assistant_results.py`
- `backend/app/services/plans.py`
- `backend/app/services/snapshot_context.py`
- `backend/demo_assistant.py`
- `backend/tests/assistant_qa_cases.py`
- `backend/tests/fixtures/README.md`
- `backend/tests/fixtures/assistant-ui.synthetic.json`
- `backend/tests/fixtures/rotation_context.synthetic.json`
- `backend/tests/fixtures/teammate-climate.synthetic.json`
- `backend/tests/test_assistant.py`
- `backend/tests/test_assistant_compatibility.py`
- `backend/tests/test_assistant_contract.py`
- `backend/tests/test_assistant_merged_contracts.py`
- `backend/tests/test_assistant_qa.py`
- `backend/tests/test_assistant_results.py`
- `backend/tests/test_assistant_routing.py`
- `backend/tests/test_canonical_assistant_plans.py`
- `docs/API_CONTRACTS.md`
- `docs/ASSISTANT_SAVED_PLANS_INTEGRATION.md`
