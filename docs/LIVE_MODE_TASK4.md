# Task 4 — Complete Live Frontend Mode

Completed locally in `NASA-Space-App-New`, branch `dulanjaya/live-mode`, starting
from a clean working tree. No merge, commit, push or PR was performed. Backend
application/models and all scientific algorithms and production catalogs remain
unchanged.

## Result and behavior

The real frontend-to-FastAPI workflow is implemented and verified. Live mode
defaults to `VITE_USE_FIXTURES=false` and
`VITE_API_BASE_URL=http://localhost:8000/api/v1`. Only literal `true` enables
synthetic fixtures; malformed mode values fail explicitly. No API/network error
switches data modes.

Selections, drafts and offline plan caches now have separate mode/API-URL
namespaces. Legacy unscoped storage is not imported, overwritten or deleted,
because its data origin cannot safely be established. Fixture mode stays a
separate opt-in demonstration, with a ribbon on both landing and workspace pages.

Farm version changes clear the observation reference. Late observations/analyses
from previous versions are rejected, and the observation view reloads on version
changes. Refresh clears previously displayed data. Rotation requests require a
current observation, explicit season labels, valid catalog and positive weights.
Scenario/assistant/plan actions respect stale versions and connectivity. Assistant
messages honor the backend's 2000-character limit and conversations reset on farm
version changes.

Plan reads use an explicitly labeled, same-mode offline copy only on a connection
failure. Authoritative 404/409/422/503 responses are no longer hidden by old cache
entries. Malformed proxy error envelopes become controlled `ApiClientError`s;
field errors, status codes and user cancellation remain intact. Duplicate sidebar
React keys discovered after plan saves were corrected without replacing the UI.

Task 4's integration scope is complete. Production recommendations still require
owner-approved crops; unavailable seasonal water inputs remain unknown. The
successful complete downstream browser workflow uses explicitly synthetic,
isolated test inputs and does not imply production agronomic approval.

## Verification

| Check | Result |
| --- | --- |
| Complete backend pytest suite | 492 passed; 195 subtests passed |
| Shared scientific tests | 61 passed, 2 skipped: optional SMAP HDF5 dependency absent |
| Frontend unit tests | 114 passed in 15 files |
| TypeScript / production build / lint | All passed |
| Shared-data validation | Passed; production catalog unchanged |
| Default real-browser suite (Edge) | Four scenarios passed |
| Separate empty-catalog browser run | Passed |
| Separate actual live NASA browser run | Passed |
| Separate fixture-mode browser run | Passed, with no FastAPI requests |

The backend emits one existing Starlette/httpx deprecation warning. Browser runs
emit existing nonblocking React Router v7 migration notices. Environment-specific
browser cases are intentionally skipped in the default run and executed through
their separate commands below.

The full browser journey performs real cross-origin HTTP calls from Vite at
`localhost:5173` to FastAPI at `localhost:8000/api/v1`: farm form → observations →
rotation → scenario → assistant → save scenario plan → retrieval and page reload.
It also captures desktop/mobile plan screenshots under ignored `frontend/test-results`.

Error coverage includes actual backend stale versions (409), missing records
(404), null observation validation (422), and both unsupported assistant languages
(422 `UNSUPPORTED_LANGUAGE`) followed by successful English retries in the UI.
Error-only browser routes additionally exercise 404/409/422/503 and refused
connections. They never inject successful climate/crop responses. Frontend unit
tests assert that failures do not invoke fixture functions and preserve field
errors and cancellation. Existing backend tests independently cover service 503s.

### Synthetic tests versus live NASA

`e2e/serve_backend.py` is an opt-in test launcher, not an application route. It
allocates disposable SQLite and starts the real app before the browser begins.
Default tests normalize the repository's existing explicitly synthetic fixture,
preserve missing values and block NASA requests. A fictional crop is confined to
a temporary test catalog for downstream selection/persistence. No original draft
entry is approved or modified. Its catalog version is retained for the test UI
contract; synthetic labels remain visible. These tests prove workflow and API
compatibility, not agronomic correctness or measured field conditions.

The empty-catalog run substitutes a temporary empty research-pending catalog and
verifies no candidates/save controls appear, while scenarios and assistant remain
usable. The actual live NASA run disables all provider/catalog overrides. It
retrieves real POWER estimates at an isolated test farm's coordinates, asserts
`data_kind: modeled` and real source information, and verifies the original
production catalog returns zero candidates. An outage fails that opt-in test;
there is no fabricated fallback.

The fixture-mode browser run separately opts into local demonstration functions,
asserts the visible banner and verifies zero FastAPI requests. It is not counted
as live integration. Existing server processes are not reused: occupied ports
cause Playwright startup to fail rather than touch somebody else's database.

## Files changed

New:

- `frontend/src/api/config.ts`, `config.test.ts`, `live.test.ts`.
- `frontend/playwright.config.ts`.
- `frontend/e2e/serve_backend.py`, `live-mode.spec.ts`.
- `docs/LIVE_MODE_TASK4.md`.

Modified:

- `frontend/.env.example`, `.gitignore`, `package.json`, `package-lock.json`, `README.md`, `QA_CHECKLIST.md`.
- `frontend/src/api/client.ts`, `index.ts`.
- `frontend/src/components/layout/AppShell.tsx`, `Sidebar.tsx`.
- `frontend/src/hooks/useAppStore.ts`, `useAppStore.test.ts`, `useSavePlan.ts`.
- `frontend/src/pages/ObservationsPage.tsx`, `RotationPage.tsx`, `ScenarioPage.tsx`, `AssistantPage.tsx`, `PlanPage.tsx`.
- `frontend/src/utils/draft.ts`, `offlineCache.ts`, `offlineCache.test.ts`.
- `docs/API_CONTRACTS.md`.

Playwright is a locked development dependency, not an application runtime
dependency. Browser artifacts, local environments and SQLite files are ignored.
No environment-specific `.env.local` was added.

## Local setup

From the repository root in PowerShell (Python 3.12; Node 24/npm 11):

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-ci.txt -e .
$env:PYTHONPATH = "$PWD\backend;$PWD"
$env:DATABASE_URL = 'sqlite:///./live-mode-local-test.db'
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use a new disposable database path for manual testing to preserve existing farm
records. In a second terminal, from `frontend`:

```powershell
npm ci
$env:VITE_USE_FIXTURES = 'false'
$env:VITE_API_BASE_URL = 'http://localhost:8000/api/v1'
npm run dev -- --host localhost --port 5173
```

For the separate demo, explicitly set `VITE_USE_FIXTURES='true'` and restart Vite.
The mode is build-time configuration, not a response to backend availability.

## Repeat automated checks

From the repository root:

```powershell
$env:PYTHONPATH = "$PWD\backend;$PWD"
$env:DATABASE_URL = 'sqlite:///:memory:'
$env:NASA_POWER_ENABLED = 'false'
backend/.venv/Scripts/python.exe -m pytest backend/tests --allow-hosts=127.0.0.1,::1 -ra
backend/.venv/Scripts/python.exe -m pytest tests --disable-socket --allow-unix-socket -ra
backend/.venv/Scripts/python.exe scripts/validate_data.py
git diff --check
```

From `frontend`, after stopping manual servers on test ports 8000/5173:

```powershell
npm test
npm run typecheck
npm run build
npm run lint
npm run test:e2e
$env:E2E_CATALOG = 'empty'
npm run test:e2e -- --grep 'empty catalog'
Remove-Item Env:E2E_CATALOG
$env:E2E_LIVE_NASA = '1'
npm run test:e2e -- --grep 'actual live NASA'
Remove-Item Env:E2E_LIVE_NASA
$env:E2E_FRONTEND_FIXTURES = '1'
npm run test:e2e -- --grep 'explicit fixture'
Remove-Item Env:E2E_FRONTEND_FIXTURES
```

Installed Edge is used on Windows. Elsewhere run `npx playwright install chromium`.
`PLAYWRIGHT_CHANNEL` selects another installed Chromium channel;
`AGROSPHERE_PYTHON` can override the backend interpreter. If the default ports
are unavailable, set `E2E_BACKEND_PORT` and `E2E_FRONTEND_PORT` before running
the suite (for example, `8011` and `5174`). The launcher always
allocates its own DB. Only `E2E_LIVE_NASA=1` permits actual NASA calls.

Remaining limits: no approved production candidates, missing dated seasonal
water inputs, English-only assistant, optional SMAP HDF5 dependency absent, and
the noted upstream deprecation notices. None is masked with fixture results.
