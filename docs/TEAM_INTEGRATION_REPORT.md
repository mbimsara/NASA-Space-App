# Team integration — 14 November 2026

Integration branch: `matheesha/nasa-power-integration`. Main is unchanged. Local recovery branch: `matheesha/pre-team-integration-20261114`.

## Included teammate branches

| Owner | Remote branch | Integrated source commit |
| --- | --- | --- |
| Bhagya | `zerokali20` | `656e834` |
| Dulanjaya | `dulanjaya/backend` | `f6a7d24` |
| Akash | `akash-dev` | `37df652` |
| Shehani | `branch-shehani` | `03a46b7` |
| Tharuka | `tharuk` | `4e94cce` |

Merge commits: `85161f1`, `f8140b8`, `e233f09`, `c0b9961`, `c062c4f`. Existing authorship is preserved. The two prototype directories are design references; the functional application is `frontend/`.

## Integration fixes

- The frontend live client translates the backend's `daily[]` observation fields to chart rows and formats structured spatial resolution. Null values and measured zeros remain distinct.
- Observation requests default to yesterday in UTC, matching the historical API's date restrictions. Charts can display one variable even if the other has no data; per-variable coverage is retained.
- Seasonal handoffs accept explicitly synthetic HTTPS fixture references while modeled POWER source URLs remain restricted to NASA POWER. Retrieval metadata, source references, data kind, and limitations survive the API-to-engine handoff.
- The catalog test now expects eight researched draft entries instead of an empty catalog. No crops were approved to make tests pass.
- Backend requirements use UTF-8 so standard tooling can read them. CI now checks combined Python modules/APIs and the frontend.

## Verification completed

| Check | Result |
| --- | --- |
| Combined `pytest tests backend/tests` | All 373 tests passed, including 74 passing assistant subtests |
| Frontend Vitest | 49 tests passed |
| Frontend production build | Passed |
| Frontend lint | Passed with six warnings |
| Shared data validator | Passed |
| Cross-module API → season adapter → water-budget/assistant test | Passed with synthetic provider input |
| Live NASA POWER through merged farm API | January 2025 at the Sri Lankan demo point: 31/31 rainfall and temperature days; rainfall 221.69 mm; cached observation ID reused; stored snapshot matches; seasonal metadata retained |
| Chrome fixture smoke | Loaded demo farm, rendered observation chart, generated three explicitly synthetic comparison cards; unknown irrigation/deficit remained unknown |

The live provider smoke used an isolated ignored `.cache/` database and a synthetic farm profile at the demo location. The NASA observations were modeled data, separately labeled. Tests use mocked providers; no credentials or downloaded datasets are committed. Windows API tests required execution outside the sandbox because its socket/thread restrictions stalled TestClient.

Non-blocking warnings: Starlette's existing httpx TestClient deprecation; React effect/prototype lint warnings; a large frontend bundle. npm installation also reported two moderate dependency advisories; no forced dependency upgrades were applied.

## What works, and what remains

| Boundary | Current state | Next owner action |
| --- | --- | --- |
| Farm create/read/update, validation, version conflicts | Implemented and tested | Dulanjaya: preserve these contracts when adding analytical routes |
| Farm → POWER observations → persistent cache/snapshot | Implemented; live smoke passed | Matheesha + Shehani: review real chart presentation together |
| Observation → seasonal climate input | Cross-module test passes; unknown irrigation preserved | Bhagya + Matheesha: agree effective rainfall before enabling water advice |
| Rotation/water/soil/recovery modules | Module tests pass; catalog contains eight drafts | Bhagya: finish evidence review; Dulanjaya: expose the agreed rotation response |
| Climate scenarios/twins/SMAP | Matheesha's standalone modules retained and tested | Dulanjaya + Matheesha: connect requested outputs to API; Shehani: add matching views |
| Assistant | Grounded deterministic English function and CLI pass tests | Akash + Dulanjaya: HTTP route and clear unsupported-language errors |
| Full frontend journey | Synthetic fixture implementation; observation wire adapter added | Shehani: wire analytical responses once routes exist; Tharuka: visual review |
| Saved plans | Frontend fixture implementation | Dulanjaya: persistence/endpoints with input and analysis snapshots |

**The full live application is not yet connected.** Rotation, scenario, assistant, and saved-plan HTTP endpoints are absent. Passing module tests and fixture screens do not establish those missing integrations. Draft crops must remain excluded from real recommendations. SMAP remains regional surface-moisture context; no exact field soil-health or nutrient inference is introduced.

## Reproduce

Follow `backend/README.md` for installation and API startup, and `frontend/README.md` for the UI. From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = 'backend;src'
.venv/Scripts/python.exe -m pytest tests backend/tests
.venv/Scripts/python.exe scripts/validate_data.py
```

From `frontend/`, run `npm ci`, `npm test`, `npm run build`, and `npm run lint`. Keep `VITE_USE_FIXTURES=true` for the complete synthetic demonstration. Live mode currently supports farms and observations only. Optional SMAP tests require `backend/requirements-smap.txt`; authenticated downloads remain a separate private workflow.
