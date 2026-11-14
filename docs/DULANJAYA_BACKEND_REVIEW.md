# Selective backend branch review

Review branch: `integration/dulanjaya-backend-review`. No commit, push, merge,
reset of main or PR creation was performed. Changes remain available for review.

## References and review coverage

Remote references were fetched before comparison:

| Reference | Commit |
| --- | --- |
| Review branch base and latest `origin/main` | `58e4a58b197682ea0fcad46afac0bab25c32a526` |
| Earlier `origin/dulanjaya/backend` | `28404adc76a324beeea802075bfe4c13035b9534` |
| Task 4: `origin/dulanjaya/live-mode` | `1e1eb6385a698ed7f6473108b6a5f26434865f5a` |
| Main/backend merge base | `fc7f3f601d5d46dfdf775c449d361278b1d9aeaf` |

The fetched main does **not** contain Task 4 yet. Task 4 is preserved on its own
committed branch and was tested in an untouched detached checkout against this
review's backend. No frontend files from either branch are changed here.
The initial tracked working tree was clean; existing untracked
`frontend/test-results/` artifacts were left alone and are not part of this port.

The old branch changed 47 paths since the fork. A tip-to-tip diff additionally
shows newer main/frontend/scientific work absent from that old branch. These
absences are not deletion requests. The [complete TSV inventory](reviews/dulanjaya-backend-inventory.tsv)
classifies 252 paths, splitting rename sides and including two identical documents
changed on the old branch. Each row records main/legacy blob IDs, whether the old
branch changed it since the fork, the decision and reason.

## Incorporated

1. **Atomic analysis-save version guard.** The legacy branch's conditional-update
   approach is adapted to canonical `persist_analysis`. Main previously refreshed
   the farm before saving, leaving a check-to-insert race. A conditional no-op
   farm UPDATE now rechecks the version and holds SQLite's writer lock through
   the canonical INSERT/commit. A concurrent edit returns existing 409
   `VERSION_CONFLICT`; it inserts no outdated analysis and changes no farm values.
2. **Strict rotation integer fields.** `input_version` and `seasons` now reject
   boolean/string/floating-point JSON coercion. Frontend integer requests remain
   valid. Main's required season labels, 201 success and result schemas remain.
3. **Selection-level assistant warnings.** The HTTP bridge retains synthetic and
   hypothetical warnings in `limitations` even for farm-only questions that do
   not render those analytical sections. Akash's explanation, normalization,
   request wrapper and citation trace remain unchanged; no source IDs are added.
4. **28 canonical regression cases** adapted from useful older coverage:
   strict integers, a separate writer editing after calculation, unchanged farms
   on success, both localhost CORS origins/error envelopes, required season
   identity, missing/null observations, safe commit failures for all three saved
   result types, baseline/scenario plan retrieval in a fresh Python process,
   distinct repeated saves, historical reads after catalog/model changes and
   focused-answer disclosures. Existing canonical fixtures and models are reused.
5. **Adapted HTTP integration probe.** The useful Node/Vite/Axios client probe,
   disposable server and bounded Windows cleanup are rewritten for canonical
   main. No legacy services/tables, obsolete response assertions or automatic
   live-NASA phase are retained.
6. **Task 4 browser wrapper.** Temporary configuration runs Task 4's unchanged
   Playwright tests against the reviewed backend, not its checkout's backend.
   No frontend source/configuration is rewritten. Tests own disposable SQLite
   and reject occupied application ports rather than reusing another server.

## Excluded and why

| Old work | Decision |
| --- | --- |
| `backend/agrosphere_rotation/` | Exclude duplicate package: all seven Python modules are byte-identical to main's `src/agrosphere_rotation/`. Keep one package/editable install. |
| Old rotation/scenario/plan ORM models | Keep canonical `rotation_analysis_snapshots`, `rotation_scenario_snapshots`, `saved_plan_snapshots`. Do not add `rotation_analyses`, `climate_scenarios` or `saved_plans`. No DB migration. |
| Wholesale analytical services/routes | Main has newer seasonal outputs, observation-period rainfall comparisons, scenario retrieval, canonical context validation, root/list plan APIs and stronger assistant contracts. Preserve them. |
| Optional season labels, 200 creation responses | Do not weaken main/Task 4's required labels and canonical 201 contracts. |
| Old scenario serialization and blanket unavailable-water behavior | Preserve main's supported calculations, `score_change`, observation comparison and null handling for genuinely unavailable inputs. |
| Older assistant functions/unbounded messages | Keep newer `respond_to_request`, typed errors, diagnostics, comparison support, source trace and 2000-character limit. Only integration-level warnings were adapted. |
| Legacy original request/catalog input bundle | Deferred: main did not persist that bundle. Adding old tables or reconstructing it from today's catalog would be unsafe. Any additive storage change needs a separate migration/versioned contract. |
| Catalog-based plan revalidation from that bundle | Not portable to main's historical records. Keep canonical producer snapshots and their disclosed limitations; do not pretend missing original inputs are available. |
| Bulk older tests | Adapt missing scenarios rather than importing obsolete models, fixture conventions, status codes and delta fields. Main's richer tests remain intact. |
| Standalone old API/integration documents | Do not copy stale table names, payloads, engine pins, optional-season claims, limitations or test counts. Update current docs and record review evidence here instead. |
| Old frontend integration report | Historical only: it predates Task 4 and includes now-resolved UI/lockfile gaps. New verification appears below. |
| Old integration scripts verbatim | They import legacy `RotationService`, expect obsolete `hypothetical`/delta shapes and automatically attempt NASA. Adapt infrastructure to canonical main and stay offline. |
| Bhagya catalog review/scoring spec documents | Already byte-identical on main; no port or approval change. |
| Older CI/setup | Keep root/backend PYTHONPATH, editable package installation, frontend CI and shared-data checks. The old setup would lose required imports/scientific package availability. |
| Apparent frontend/science/data/script/test removals | Exclude all removals. They reflect newer main work missing from the older branch, not useful changes to import. |

All compared paths, including setup and documents outside the 47 old-branch
changes, have individual decisions in the TSV. No original crop values, approval
decisions, NASA algorithms or scientific formulas are changed.

## Verification performed

| Check | Result |
| --- | --- |
| Complete canonical backend | **520 passed; 195 subtests passed** (492 existing tests + 28 additions) |
| Shared scientific tests | **61 passed, 2 skipped**: optional SMAP HDF5 dependency absent |
| Main frontend | **102 tests passed**, TypeScript/build/lint passed |
| Unmodified Task 4 frontend | **114 tests passed**, TypeScript/build/lint passed |
| Task 4 client over real HTTP against reviewed backend | Passed: CORS, farm CRUD/409, observations, required-label/null errors, canonical rotations/scenarios, assistant/si/ta errors, both plan types and zero candidates |
| Actual Edge + Task 4 UI + reviewed backend | **4 passed, 3 skipped**: full farm-form-to-plan-reload journey, missing observation/404/409/422, network/HTTP errors, English retry and stale context |
| Shared data / whitespace / source preservation | Passed |

The three browser skips are separately gated empty-catalog, live-NASA and
frontend-fixture-mode cases. No external NASA/AI calls were needed or claimed in
this review. Both integration launchers block NASA and use disposable SQLite,
the existing explicitly synthetic provider fixture and a temporary fictional
test crop. No original draft entry is approved. Zero candidates are exercised by
the client probe and existing canonical backend tests.

Existing Starlette/httpx and React Router migration notices remain nonblocking.
The Task 4 detached worktree remains available for repeating checks; its tracked
source is clean. The initial frontend test artifacts are not included in changes.

## Changed files

- `backend/app/services/rotations.py`, `backend/app/api/routes/rotations.py`:
  canonical atomic-save guard and 409 mapping.
- `backend/app/schemas/rotation.py`: strict integer request fields only.
- `backend/app/services/assistant_context.py`: HTTP selection disclosures only.
- `backend/tests/test_backend_port_regressions.py`: 28 adapted cases.
- `backend/tests/integration/serve_frontend_probe.py`, `frontend_probe.mjs`,
  `run_frontend_probe.py`, `run_task4_browser.py`: isolated canonical probes.
- `backend/README.md`, `docs/API_CONTRACTS.md`, `docs/ARCHITECTURE.md`: focused
  current-contract updates and review links.
- This report and `docs/reviews/dulanjaya-backend-inventory.tsv`.

No ORM model, scientific package, data, frontend or CI workflow is modified.

## Reproduce

From the review repository root, PowerShell:

```powershell
$env:PYTHONPATH = "$PWD\backend;$PWD"
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:NASA_POWER_ENABLED = 'false'
backend/.venv/Scripts/python.exe -m pytest backend/tests --allow-hosts=127.0.0.1,::1 -ra
backend/.venv/Scripts/python.exe -m pytest tests --disable-socket --allow-unix-socket -ra
backend/.venv/Scripts/python.exe scripts/validate_data.py
git diff --check
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run lint
```

For Task 4, use a detached checkout of its recorded ref, run `npm ci` in its
frontend and repeat its tests/typecheck/build/lint. With ports 8000/5173 free,
run these from this review repository:

```powershell
backend/.venv/Scripts/python.exe backend/tests/integration/run_frontend_probe.py "PATH_TO_TASK4_FRONTEND"
backend/.venv/Scripts/python.exe backend/tests/integration/run_task4_browser.py "PATH_TO_TASK4_FRONTEND"
```

The wrappers use **this reviewed backend** with the supplied untouched frontend.
The browser wrapper requires Task 4's Playwright dependency and installed Edge
on Windows, or an installed channel selected with `PLAYWRIGHT_CHANNEL`.
Configuration/results/DBs are temporary and removed after tests.

## Remaining review considerations

Review the intentional strict-integer validation, and coordinate Task 4's
separate PR/base before combining in main. Production crop approvals and dated
seasonal climate/demand alignment remain scientific-owner work. No request/catalog
snapshot migration is attempted. This is a reviewable working tree, not an
already created or published PR.
