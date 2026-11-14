# Frontend/backend compatibility review

Tested locally on 2026-11-14 (Asia/Colombo). Backend branch:
`dulanjaya/backend`, starting at `d526a66b01e9f553f23895b0d8dddf29874ad210`.
The tracked working tree was clean before this task. Old inaccessible ignored
pytest scratch directories generated Git warnings; no tracked changes were present.
Remote branches were fetched. Shehani's latest `origin/branch-shehani` was
`0e4bd97346cf584f8e87a66b764361089350d553`, checked out as a detached worktree.
No branches were merged and no frontend source/configuration/lockfiles were changed.

## Verification results

| Check | Result |
| --- | --- |
| Complete backend suite | 225 passed; one existing Starlette/httpx deprecation warning |
| Frontend Vitest suite | 80 passed, 8 test files |
| Frontend TypeScript check | Passed |
| Frontend production build | Passed; approximately 1,125 kB minified main JS chunk, size warning |
| Shared-data validation | Passed; production catalog remains empty/research-pending |
| Whitespace check | Passed |
| Actual HTTP using unmodified frontend API facade | Passed, separately in synthetic and live modes |
| Live NASA POWER request | Succeeded; returned `modeled` provenance, never relabeled observed |
| Browser end-to-end testing | Not performed; the runner uses Vite SSR and Node/Axios, not a browser |

Local runtime: Node v24.21.0, npm 11.19.0, Python 3.12. The frontend serves at
`http://localhost:5173`, uvicorn at `http://127.0.0.1:8000`. The API facade was
loaded with `VITE_API_BASE_URL=http://localhost:8000/api/v1` and
`VITE_USE_FIXTURES=false`, supplied through the process environment. No local
environment file was added. All HTTP test data used newly allocated temporary
SQLite databases; the normal application database was never used.

### Dependency-install qualification

Standard `npm ci --no-audit --no-fund` failed with this runtime because the
committed lockfile omits `@emnapi/core@2.0.0-beta.2` and
`@emnapi/runtime@2.0.0-beta.2`. The same failure occurred with legacy peer
resolution. Testing continued using:

```text
npm install --no-save --package-lock=false --no-audit --no-fund
```

This left package.json and package-lock.json unchanged, but resolved dependencies
without the committed lockfile. Consequently the passing tests/build are evidence
for the unchanged frontend source under that installation, not proof that a
clean locked CI install works. Shehani must repair and verify the lockfile.

## Contract comparison by workflow

| Frontend request | Actual backend response / compatibility |
| --- | --- |
| `createFarm`, `createDemoFarm` | POST `/farms`, 201 `{id,input_version,profile}`; matches. Synthetic demo label retained. Form submissions add schema version and farmer-input provenance correctly. |
| `getFarm` | GET `/farms/{id}`, 200 farm envelope; matches. Unknown ID returns typed 404 error. |
| `updateFarm` | PATCH with expected version and complete profile, 200 incremented version; matches. Stale version returns 409. |
| `getObservations` | GET with ISO start/end, 200 persisted envelope; `daily`, rainfall alias, per-variable coverage, nulls, source metadata and modeled/synthetic labels match current types and chart adapter. |
| `createRotation` | Count-only requests with a valid observation/catalog return 200. Empty catalog is valid and produces `candidates: []` plus reasons/limitations. Frontend can submit null observations (422) and cannot yet supply explicit season identity. |
| `createScenario` | POST rainfall percentage, 200 scenario/baseline IDs, candidate IDs, keyed differences and limitations; matches. Additive `hypothetical`, provenance and version metadata are retained by the backend. |
| `savePlan` / `getPlan` | POST returns 201 `{plan_id}`; GET includes all `SavedPlan` fields, original farm inputs and selected metadata. Extra observation/scenario snapshots are backward-compatible. Relationships and current versions are checked. |
| `sendAssistantMessage` | Four required response fields match; additive status/language/assumptions do not break the client. English-only rejection now returns the specific code needed by its retry UI. Stale references return 409, not an answer mixing input versions. |

All resource IDs are persistent server IDs. Candidate IDs remain aligned between
the saved baseline and scenario. Null score/water values remain unknown, not
zero. Scenario differences may contain a zero diversity-score delta while water
effects remain unknown; the UI must not imply that means no climate impact.
Catalog versions match (`0.1-draft`) at these two inspected commits; no version
mismatch was found. The client bundles its catalog version, so both artifacts
must continue to be coordinated at deployment rather than ignoring validation.

CORS JSON preflights and allowed-origin headers were checked for
`http://localhost:5173`; POST/PATCH and error responses remain accessible.
The defaults also include `http://127.0.0.1:5173`. No permissive wildcard was added.

## Backend fix

`AssistantPage.tsx` explicitly tests
`error.code === "UNSUPPORTED_LANGUAGE"` to show its English retry action.
The backend's Pydantic English-only literal previously emitted the generic
`VALIDATION_ERROR`, preventing that UI branch. The validation handler now emits
422 / `UNSUPPORTED_LANGUAGE` for assistant language-literal failures, with an
English-only explanation and field details. Other validation retains its
existing status/code. Akash's service and language capabilities are unchanged.

Regression coverage checks language fallback codes, ordinary validation, CORS
preflights/error envelopes, count-only empty analyses and rejected null snapshots.

## Frontend changes to coordinate with Shehani

| File | Expected change and reason |
| --- | --- |
| `frontend/package-lock.json` (and package constraints if needed) | Regenerate with the agreed Node/npm runtime; ensure a clean `npm ci` succeeds. Do not rely on the unlocked test workaround. |
| `frontend/src/api/client.ts` — `RotationRequest` | Require a non-null observation ID for live submissions; add optional ordered `season_labels` (`maha`, `yala`, `inter-season`) matching `seasons`. The API does not infer dates or a seasonal calendar from a count. |
| `frontend/src/pages/RotationPage.tsx` | Disable generation when no observation exists for the current farm/version, show a link to load observations, and collect/send explicit season labels. Its current null submission gets 422; even an approved catalog cannot yield candidates without season identity. |
| `frontend/src/pages/ScenarioPage.tsx` / `frontend/src/hooks/useSavePlan.ts` | Add a selected-scenario-candidate save action and pass `scenario_id`. The hook supports that argument, but the inspected UI only calls saving from RotationPage without it. The backend and HTTP client support both plan types. |
| `frontend/src/pages/AssistantPage.tsx` | Warn/disable sending for an outdated analysis and offer regeneration. The current backend correctly returns 409; the page has no dedicated outdated-analysis guidance. The existing English-retry branch now works with the backend error code. |
| `frontend/src/pages/PlanPage.tsx` | Avoid presenting every reopened plan as rank 1 (`CandidateCard rank={1}`). It is a saved selection; no original ranking is stored on the candidate. |
| `frontend/src/i18n/locales/en.json` and corresponding reviewed locales | `catalog.emptyNote` currently says results shown are fixtures. Make the copy depend on fixture mode; live empty results are actual backend analyses, not fixture results. Keep the explicit no-approved-crops limitation. |
| `frontend/README.md` | Update the old time-series-only observation note: current code accepts the backend's `daily` shape via `toChartPoints`. |

RotationPage's empty-results branch renders its no-candidates message, reasons,
limitations and provenance and produces no candidate/save controls. This was
verified by source inspection, real client HTTP responses and existing store
tests with empty candidate arrays. Visual rendering and user interaction were
not verified in a browser. No frontend source edits were made in this task.

## HTTP test scope and reproducibility

The committed test runner launches its own isolated server processes, refuses
occupied ports and stops only its own processes. It closes and cleans up temporary
databases, with retries for Windows handles after process shutdown. It serves the
actual frontend through Vite and imports its unmodified `api/index.ts` facade;
this executes the real Axios client rather than manually imitating its requests.

From the backend repository root, after installing frontend dependencies in a
detached checkout:

```text
backend/.venv/Scripts/python.exe backend/tests/integration/run_frontend_http.py PATH_TO_FRONTEND
```

Synthetic mode blocks NASA network access, uses the existing explicitly synthetic
observation fixture and a temporary approved **test-only** catalog. It checks
create/read/update, stale updates, observations, typed 422 errors, count-only
empty rotations, explicit-season rotations, hypothetical scenarios, baseline and
scenario plan save/reopen, assistant context/disclosures, unsupported si/ta,
English retry and cross-farm conflicts. These downstream checks use explicit
`season_labels` through the real client, an extension **not currently supplied
by RotationPage**, and a test catalog version. They do not prove the unchanged
page can complete those actions against approved production crops.

Live mode has no observation override. It creates only a synthetic test farm,
retrieves actual NASA POWER climate estimates at its illustrative coordinates,
and tests the actual production empty catalog. Provider failure/timeouts are
reported as unavailable rather than replaced with synthetic measurements.
The successful live retrieval is distinct from all synthetic downstream tests.

The first HTTP run passed its request assertions but hit Windows temporary-file
cleanup contention. After adding bounded cleanup retries, a full second run
passed both modes and exited successfully. No browser E2E is claimed.

## Before deployment / final end-to-end checks

1. Repair the frontend lockfile and repeat locked tests, typecheck and build.
2. Coordinate explicit season/observation UI inputs. Keep empty results until
   Bhagya approves catalog entries; do not create demo recommendations in live mode.
3. Retain the current null water/scenario effects until seasonal demand/climate
   alignment is approved. Verify warnings are understandable in the browser.
4. Run the QA checklist in a real browser: new/edit/reload farm, invalid dates,
   observation refresh after edits, empty analysis UI, synthetic-only downstream
   plans, plan reload, stale analysis warnings, assistant si/ta English retry,
   failed HTTP requests and rapid farm/scenario switches. Check keyboard/mobile
   behavior and browser-enforced CORS, not just Node's HTTP response headers.
5. Resolve the build chunk warning through frontend code splitting if required
   for the deployment target; the build itself succeeds.

No commit, push, merge, PR, frontend changes, production database writes or changes
to teammate scientific/explanation algorithms were performed.
