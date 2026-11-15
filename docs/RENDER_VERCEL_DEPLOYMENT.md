# Render + Vercel restricted staging preparation

Local preparation only. Do not deploy until review and the verification gates
below are complete. Use fictional farm inputs only: application users, ownership
authorization, revocation and per-user audit trails are not implemented. Every
reviewer can read every staged record. Scientific models, catalog review statuses,
NASA adapters and API result schemas are unchanged.

The VM/Caddy work is separate on `dulanjaya/staging-deployment`. Its
`docs/STAGING_DEPLOYMENT.md` was inspected with `git show` because it is absent on
this branch. None of that branch's files were cherry-picked or overwritten. When
these PRs are combined, reconcile their optional configuration guards explicitly.

## Architecture and security boundary

Browser -> HTTPS Vercel React app -> same-origin `/api/v1/*` Vercel Node function
-> HTTPS Render FastAPI -> explicitly chosen DB.

The Vercel function independently requires HTTP Basic reviewer credentials,
checks the exact staging origin, strips cookies/client credentials, and injects a
server-only Bearer token. FastAPI hosted middleware protects **all existing routers
and unknown paths**, including reads, writes, feedback, satellite context, plans,
scenarios, assistant and preflights. Only the minimal liveness GET/HEAD path is
public for Render's probe. Guessed IDs, CORS, Vercel-only UI protection and direct
`onrender.com` requests cannot bypass the backend token. Docs/OpenAPI are disabled
in hosted mode; trusted Host names are required.

Tokens and passwords remain server secrets, never `VITE_*`. The frontend API URL
is intentionally `/api/v1`, not Render's URL: calling Render directly from the
browser would require exposing a secret or leaving the API writable. The actual
Render origin is the **server-only** `RENDER_API_BASE_URL`.

Also enable Vercel Authentication for **All Deployments**, verify it includes the
stable production alias and all generated/preview URLs. Standard Protection can
leave production domains public; do not assume it covers them. If the account does
not offer the required scope/reviewer access, resolve that before deployment. API
Basic authentication is an independent fallback boundary, not a replacement for
page protection or application identity. No credentials are embedded in rewrites.
No application-level rate limiting is added; assess gateway limits and keep the
reviewer group small. Do not expose real farmer data even after these gates pass.

## Render dashboard settings

Use New -> Web Service (or review root `render.yaml` as a Blueprint). Connecting a
repository/creating a Blueprint can trigger an initial deploy: do this only after
review. Blueprint disables subsequent automatic deployments. Do not provision a
database automatically from this manifest.

| Setting | Exact value |
| --- | --- |
| Repository | `mbimsara/NASA-Space-App` |
| Branch | Reviewed `dulanjaya/render-vercel` revision; do not deploy unreviewed main automatically |
| Runtime | Python |
| Root Directory | **Blank/repository root**, not `backend` |
| Build command | `pip install . -r backend/requirements.txt -r backend/requirements-postgres.txt` |
| Start command | `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT --workers 1 --no-access-log --no-proxy-headers` |
| Python | `PYTHON_VERSION=3.12.12` |
| Plan | Free for disposable demonstrations only |
| Health check | `/api/v1/health` |
| Auto Deploy | Off/manual |

Full context is required for `pyproject.toml`, `src/agrosphere_rotation`, and actual
`data/catalogs`/`data/schemas`. Installing only `backend/requirements.txt` from a
backend-only context omits the domain package. Do not copy/duplicate that package.
`create_all` runs at startup; health verifies process liveness, not complete DB
readiness or NASA availability. Validate authenticated DB-backed reads separately.

Set backend environment variables before the first successful start:

| Variable | Required value |
| --- | --- |
| `DEPLOYMENT_MODE` | `hosted-staging` (mandatory; local mode is not safe for public Render hosting) |
| `STAGING_BACKEND_TOKEN` | Random ASCII token >=32 characters, no whitespace; Blueprint can generate it; copy privately into Vercel server env |
| `CORS_ORIGINS` | Exact stable `https://YOUR-STAGING-PROJECT.vercel.app`, no trailing slash; no wildcards or arbitrary preview domains |
| `TRUSTED_HOSTS` | `YOUR-API.onrender.com,127.0.0.1,localhost`; hostname only, add an exact custom hostname only if configured |
| `DATABASE_URL` | Explicitly chosen below; no automatic provider URL rewriting |
| `ALLOW_EPHEMERAL_SQLITE` | Default `false`; set `true` only for the knowingly disposable SQLite demo |
| `POSTGRES_COMPATIBILITY_VERIFIED` | Default `false`; set `true` only after real PostgreSQL verification and migration/backup review |
| `NASA_POWER_ENABLED` | `true`; actual NASA POWER retrieval, never fixture fallback |
| `OBSERVATION_CACHE_TTL_SECONDS` | `86400` |
| `ASSISTANT_PROVIDER` | `deterministic`; optional external AI remains disabled for hosted staging |

**Disposable option:** set `DATABASE_URL=sqlite:////tmp/agrosphere-demo.db` and
`ALLOW_EPHEMERAL_SQLITE=true`. This starts an empty, nonpersistent demo database.
It does not move, import, reset or upgrade any existing local database. All farms,
observations, analyses, scenarios, plans and feedback may disappear on sleep,
restart or redeploy. Saved plan IDs/links must not be advertised as durable. Clear
browser stored drafts/plans between reset demonstrations; cached plans can outlive
their database. Do not upload an existing developer/farmer DB.

**Persistent option:** blocked pending the PostgreSQL checks below. A proposed
URL is explicit `postgresql+psycopg://...`, not `postgres://` or implicit psycopg2.
Choose provider-documented TLS with certificate validation, restrict external DB
access, and keep DB/service in the same region. Never print URLs with passwords.
The optional driver file installs psycopg, not a migration or a new schema version.

## Vercel dashboard settings

Import the same repository into a **separate staging project**. Do not change the
existing production frontend project. Review initial-deploy behavior before import.

| Setting | Exact value |
| --- | --- |
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Include source files outside Root Directory in Build Step | **Enabled**; required for `../data/catalogs`, fixtures and schemas imported by existing frontend code |
| Node.js | 24.x |
| Install command | `npm ci --no-audit --no-fund` |
| Build command | `npm run build` |
| Output Directory | `dist` |
| Project configuration | `frontend/vercel.json` |
| Staging production branch | Reviewed deployment branch, not the main production project |
| Automatic deployments | `vercel.json` sets `git.deploymentEnabled=false`; use a reviewed manual deployment after approval, and confirm project Git settings |
| Deployment Protection | Vercel Authentication, All Deployments; verify reviewer access and every URL |

Routes resolve `/api/*` to the protected function **before** filesystem/static
SPA fallback. Static assets keep their filesystem routes; client routes such as
`/farms/ID/rotations` and `/plans/ID` reload through `index.html`. Unknown `/api/*`
paths must return an API error, never index.html. The Vercel-native routing/runtime
still needs a real protected deployment smoke check; a local Vite build alone does
not certify Vercel function packaging.

Set these for the reviewed staging environment only, then rebuild/redeploy manually:

| Variable | Scope/value |
| --- | --- |
| `VITE_USE_FIXTURES` | Public/build: `false` |
| `VITE_API_BASE_URL` | Public/build: `/api/v1` |
| `RENDER_API_BASE_URL` | Server secret/config: exact `https://YOUR-API.onrender.com`, no `/api/v1`, query or credentials |
| `STAGING_BACKEND_TOKEN` | Server secret: same as Render; never `VITE_STAGING_BACKEND_TOKEN` |
| `STAGING_FRONTEND_ORIGIN` | Server config: exact stable HTTPS staging origin, matching backend CORS |

Do not give untrusted PR previews these secrets. Preview domains intentionally fail
the exact-origin check. The public demo has no browser sign-in prompt; the
Render bearer token remains server-only. Rotate the backend token after the
demo and coordinate the change across both services. Never log request bodies,
questions, cookies, Authorization or environment dumps. Hosting-provider access
logs may still retain URLs/query strings; use fictional coordinates and restrict
log access. No source maps or private NASA `.cache` artifacts are provisioned.

The demo frontend and same-origin API gateway are public. Do not put the Render
bearer token into localStorage, frontend source, or any `VITE_` variable.
Verify this browser behavior in the deployed smoke check. If browser/platform
authentication interaction fails, do not remove the guard: resolve the login design
or use the separately prepared private VM option. Close the private browser session
and clear site data after the demonstration.

## Free-plan limitations (checked against official docs on 2026-11-15)

Render free web services sleep after 15 idle minutes, have ephemeral local files,
cannot attach persistent disks, and share 750 active instance-hours per workspace
per month. Limits/build usage can interrupt demos; do not promise availability.
Cold starts can exceed the frontend's existing 30-second timeout. The proxy has a
25-second upstream budget and a configured function maximum of 60 seconds; it
returns honest 503 on timeout. Wake via the safe health GET before presenting,
then retry a failed read manually. Never automatically replay writes: a timed-out
POST may already have saved a result. NASA's own latency can also exceed this
budget; no fixture substitution or silent algorithm changes are permitted.

Render free PostgreSQL is a temporary trial, **not durable long-term hosting**:
1 GB, expiration after 30 days, followed by a 14-day upgrade grace period and then
deletion; no managed backups or pooling. Export/restore strategy and a paid or
otherwise durable database must be approved before relying on saved plans.
No database is created by this change. Vercel Hobby eligibility, quotas, function
limits and reviewer/protection access must be checked in the chosen account;
free usage is not guaranteed for every organization/project.

Sources: [Render free limitations](https://render.com/docs/free),
[Render Blueprint fields](https://render.com/docs/blueprint-spec),
[Vercel monorepo source access](https://vercel.com/docs/monorepos/monorepo-faq),
[Vercel protection scopes](https://vercel.com/docs/deployment-protection),
[Vercel Node functions](https://vercel.com/docs/functions/runtimes/node-js).

## SQLite -> PostgreSQL compatibility and migration gates

No database engine or model is silently changed. Local SQLite remains the default.
The existing generic SQLAlchemy tables/JSON payloads and conditional UPDATE version
guards are candidates for PostgreSQL, but SQLite tests do not prove PostgreSQL
behavior. No `postgres`/`psql` server or Docker is available locally in this session.

Added checks:

- Offline PostgreSQL DDL compilation using unchanged metadata and explicit psycopg
  driver syntax, plus fail-closed hosted DB settings.
- Opt-in real PostgreSQL tests using a new UUID-named schema, never an existing
  public schema or database reset. Tests exercise foreign keys, JSON/null/Unicode
  snapshots through the full synthetic API workflow, cache reuse, optimistic
  conflicts, competing conditional updates, immutable plan history after farm
  edits, and reconnect/read after pool disposal.
- A separate `hosted-compatibility.yml` CI job with disposable PostgreSQL 16 and
  server proxy tests. It builds/test infrastructure only and never deploys.

Run against an explicitly disposable test server (PowerShell):

```powershell
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-postgres.txt
$env:PYTHONPATH="$PWD\backend;$PWD"
$env:TEST_POSTGRES_URL='postgresql+psycopg://TEST_USER:TEST_PASSWORD@127.0.0.1:5432/TEST_DB'
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_postgres_compatibility.py --allow-hosts=127.0.0.1,::1 -ra
Remove-Item Env:TEST_POSTGRES_URL
```

The test role needs schema creation rights only in its disposable DB. Do not point
this at farmer or staging data. Real PostgreSQL tests are skipped without that URL;
DDL compilation is explicitly **not** a compatibility pass. Require green CI and
review tests against the actual provider/version before setting the acknowledgment.
Assess connection limits, reconnect behavior after provider sleep, pool sizing,
longer-running concurrent requests, and backup/restore before recommending storage.

For a future data migration: freeze writes; take a consistent SQLite backup and
integrity check; provision an empty PostgreSQL target; create reviewed Alembic
baseline/revisions (currently absent); copy tables in FK dependency order preserving
all IDs, versions, epoch timestamps, JSON nulls and Unicode; compare counts, orphan
relationships and canonicalized JSON for every snapshot; verify historic plan and
observation APIs; perform restore and rollback drills; switch configuration only
after approval. Retain the untouched source backup. `create_all` creates missing
tables, but does not migrate existing tables or copy records. No automatic copier,
destructive reset or unsupported PostgreSQL-specific algorithm change is added.

## Verification before enabling reviewers

1. Review code, public dependency advisories, hosting costs/eligibility, access
   settings and storage choice. No real farmer data. Verify ignored secret files
   and NASA credentials are absent from source and build artifacts.
2. Apply Render settings manually only after authorization. Missing/unsafe hosted
   env must fail startup. Confirm unknown direct API requests receive 401, even
   with a forged allowed Origin. Health is the only public non-record response.
3. Build Vercel with real repository catalog and fixtures disabled. Check its
   bundle has no backend token/password. Confirm anonymous frontend access is
   blocked by deployment protection and anonymous proxy access independently 401.
4. Log in through the API health navigation, then exercise create farm -> retrieve
   observations -> rotation -> hypothetical scenario -> English assistant -> save
   candidate -> reopen plan. Verify real NASA source refs and unknown quantities.
   Do not fabricate candidates if current catalog/constraints produce zero results.
5. Check stale version 409, unknown ID 404, validation/language 422, unavailable
   provider/backend 503, direct API preflight denial, and exact Host/Origin handling.
   Verify errors never become fixture success and deep links reload correctly.
6. Verify persistence only for an approved persistent DB. A disposable SQLite demo
   is expected to lose records; label that limitation to reviewers. Test TLS, cold
   starts, monitoring and backup/restore on the actual hosting accounts.
7. Disable/rotate access after the demo. Do not leave publicly writable instances.

Local commands (PowerShell, temporary DB and no live provider calls):

```powershell
$env:PYTHONPATH="$PWD\backend;$PWD"
$env:DATABASE_URL='sqlite:///:memory:'
$env:NASA_POWER_ENABLED='false'
backend/.venv/Scripts/python.exe -m pytest backend/tests --allow-hosts=127.0.0.1,::1 -ra
backend/.venv/Scripts/python.exe -m pytest tests --disable-socket --allow-unix-socket -ra
backend/.venv/Scripts/python.exe scripts/validate_data.py
node --test deploy/render-vercel/proxy.test.mjs
cd frontend
npm test
npm run typecheck
$env:VITE_USE_FIXTURES='false'
$env:VITE_API_BASE_URL='/api/v1'
npm run build
npm run lint
# Existing local real-HTTP synthetic browser harness, not hosted TLS verification:
npm run test:e2e
cd ..
git diff --check
```

Remaining blockers: real PostgreSQL compatibility/migration review; Render/Vercel
function/SPA/TLS/login smoke check; deployment protection/reviewer permissions;
durable DB and backup funding if persistence is required; dependency advisory
review; rate/usage controls and cold-start latency acceptance. Local browser HTTP
and mocked proxy tests do not certify those platform settings. No external
deployment, commit, push or PR is authorized by this preparation.

## Local verification report and changed files

Verified on 2026-11-15:

| Check | Result |
| --- | --- |
| Complete backend suite | 561 passed, 195 subtests passed; 2 real PostgreSQL tests skipped because no test server is configured |
| Hosted access/config/DDL regressions | 15 tests, included in backend count |
| Server proxy tests | 5 passed, mocked upstream; no external requests |
| Shared tests | 70 passed, 2 optional HDF5 tests skipped |
| Shared-data validation | Passed |
| Frontend | 120 tests passed; TypeScript, production build and lint passed |
| Production artifact | Built with `VITE_USE_FIXTURES=false`, `/api/v1`; actual catalog version `0.2-demo-reviewed-proxies` present in output; server-only canary token/password absent |
| Render shared package | Non-editable wheel built successfully from repository root; expected rotation modules verified inside wheel |
| Browser integration | 4 passed, 3 gated skips, explicitly synthetic isolated HTTP workflow; not hosted TLS/Vercel routing verification |
| Manifest/whitespace checks | YAML/JSON parse and `git diff --check` passed |

Existing Starlette/httpx deprecation and React Router future-flag warnings remain.
No live NASA, external AI, real PostgreSQL, Render or Vercel deployment was exercised.
The inherited shared-data GitHub workflow currently installs only rotation dev
dependencies despite newer tests importing backend modules. Its dependency and
`PYTHONPATH` repair is already in the separate VM staging PR; reconcile that PR
before requiring all CI jobs to be green. This branch's new PostgreSQL job installs
the full backend requirements explicitly. Prior staging dependency audit findings
also require review; no dependency upgrade or fresh vulnerability clearance is
claimed here.

Created files:

- `render.yaml`: whole-repository Python build and disabled auto deploy.
- `frontend/vercel.json`: protected API function before static/SPA routing, Git auto deploy disabled.
- `frontend/api/gateway.mjs`: server-only authenticated forwarding.
- `backend/app/hosted_access.py`: backend-wide hosted access guard.
- `backend/requirements-postgres.txt`: optional pinned psycopg driver.
- `backend/tests/test_hosted_deployment.py`: fail-closed settings, all-router protection and PostgreSQL DDL checks.
- `backend/tests/test_postgres_compatibility.py`: opt-in real PostgreSQL workflow/concurrency checks.
- `deploy/render-vercel/proxy.test.mjs`: server gateway regressions.
- `.github/workflows/hosted-compatibility.yml`: isolated PostgreSQL/proxy verification, no deployment.
- `docs/RENDER_VERCEL_DEPLOYMENT.md`: this guide/report.

Modified files: `backend/app/config.py`, `backend/app/main.py`,
`.github/workflows/frontend-tests.yml`, `.env.example`, `.gitignore`,
`backend/README.md`, `docs/API_CONTRACTS.md`. Frontend application source, NASA and
rotation modules, DB models and catalog contents are unchanged. All changes remain
local and uncommitted on `dulanjaya/render-vercel`.
