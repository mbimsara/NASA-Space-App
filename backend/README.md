# AgroSphere AI backend

FastAPI with synchronous SQLAlchemy and SQLite. Implemented endpoints:

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/api/v1/health` | Backend health response |
| POST | `/api/v1/farms` | Validate and persist a farm; return 201 with its ID and input version |
| GET | `/api/v1/farms/{farm_id}` | Retrieve a farm; return 404 if absent |
| PATCH | `/api/v1/farms/{farm_id}` | Replace the complete profile using `expected_input_version`; increment the version or return 409 |
| GET | `/api/v1/farms/{farm_id}/observations?start=YYYY-MM-DD&end=YYYY-MM-DD` | Retrieve a fresh cached snapshot or fetch and persist NASA POWER observations |
| GET | `/api/v1/observations/{observation_id}` | Read the original persisted observation snapshot |
| POST | `/api/v1/observations/{observation_id}/rainfall-scenarios` | Uniformly scale stored daily rainfall for a labeled hypothetical sensitivity test |
| POST | `/api/v1/farms/{farm_id}/rotations` | Validate context, invoke the shared rotation engine, and persist an immutable analysis |
| POST | `/api/v1/analyses/{analysis_id}/scenarios` | Apply a hypothetical `rainfall_change_pct` (-100 to 100) to a saved analysis, recompute season water budgets and scores, and persist a scenario snapshot (201) |
| GET | `/api/v1/scenarios/{scenario_id}` | Reopen a persisted scenario snapshot |

See [API contracts](../docs/API_CONTRACTS.md) for fields, units, and errors.
Assistant and immutable saved-plan endpoints are implemented; see [the integration handoff](../docs/ASSISTANT_SAVED_PLANS_INTEGRATION.md) for contracts and offline regression commands. POWER observations, database-backed caching, stable snapshot IDs, observation-based rainfall scenarios, crop-rotation analyses, and analysis climate scenarios are implemented. Analysis scenarios never modify the saved analysis or the NASA observation snapshot; seasons whose baseline water inputs are unknown keep scenario water and `scenario_resilience` as `null`. Live retrieval and cache reuse were verified on 2026-11-14.

## Installation

Use Python 3.10 or newer (verified with Python 3.12). Run these commands from the repository root.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . -r backend/requirements.txt
# Optional: configure values before starting the server.
Copy-Item .env.example .env
cd backend
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . -r backend/requirements.txt
# Optional: configure values before starting the server.
cp .env.example .env
cd backend
```

If a root `.env` already exists, edit it instead of copying over it.
No NASA credentials or AI service keys are needed for the implemented farm APIs.

## Configuration

The backend reads `.env` at the **repository root**, independently of the working directory.
Process environment variables override `.env`; missing settings use the defaults below.
Settings are read when the application is imported. Restart the server after changing them.

| Variable | Default | Format |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./agrosphere.db` | Synchronous SQLAlchemy database URL; must not be empty |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated HTTP(S) origins; whitespace and duplicates are removed |
| `NASA_POWER_ENABLED` | `true` | Enables provider access; `false` still permits fresh cached POWER snapshots |
| `OBSERVATION_CACHE_TTL_SECONDS` | `86400` | Positive integer; fresh-cache lifetime in seconds for newly created snapshots |

Example root `.env`:

```dotenv
DATABASE_URL=sqlite:///./agrosphere.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://farm.example
```

Each origin must match the browser's scheme, hostname, and port, with no path or trailing slash.
Wildcards and credentials in origins are rejected at startup. `CORS_ORIGINS=` disables
cross-origin browser access. Credential support, allowed methods (`GET`, `POST`, `PATCH`),
and allowed headers remain unchanged. CORS does not provide authentication.

For a temporary PowerShell override before startup:

```powershell
$env:DATABASE_URL = "sqlite:///./agrosphere.db"
$env:CORS_ORIGINS = "https://farm.example"
```

For a Linux/macOS override:

```bash
export DATABASE_URL='sqlite:///./agrosphere.db'
export CORS_ORIGINS='https://farm.example'
```

`APP_ENV`, `AI_API_KEY`, and `AI_MODEL` in the root example are reserved for future integrations
and are not consumed by the current backend. Keep secrets in the environment or ignored `.env`.

## Startup

With the virtual environment active, run **from `backend/`**:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: <http://127.0.0.1:8000/api/v1/health>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>

Use `data/fixtures/farm.synthetic.json` from the repository root as an explicitly synthetic
POST example. Use the returned ID in GET/PATCH requests. PATCH requires the complete profile
and current `expected_input_version`; validation errors return the existing 422 error envelope.

For a deployed server, omit `--reload`, use the deployment's host/port, and set
`CORS_ORIGINS` to the actual frontend origin(s).

## Database compatibility

The default SQLite URL is unchanged. Its relative path is resolved against the **process working
directory**, so starting in `backend/` keeps using `backend/agrosphere.db`. Starting elsewhere
with the same relative URL selects a different file. To use an existing database reliably,
set an absolute URL, such as `sqlite:////srv/agrosphere/agrosphere.db` on Linux or
`sqlite:///C:/data/agrosphere.db` on Windows. Its parent directory must exist and be writable.

Startup creates missing tables using `Base.metadata.create_all`; it does not migrate or reset
existing tables. This change leaves the farm table, stored JSON profiles, IDs, and input versions
unchanged. The new `observation_snapshots` table is created automatically at startup; existing farm tables are not altered. Back up an existing database before changing deployment paths. No manual migration is required for this additive table.

SQLite's `check_same_thread=False` option is applied only to SQLite URLs, including explicit
SQLite driver URLs. Other synchronous SQLAlchemy URLs require a separately installed driver
and a provisioned database; those external databases have not been integration-tested here.

## Automated tests

With the virtual environment active, run **from `backend/`**:

```bash
python -m pytest -q
```

The suite covers existing farm create/read/update, validation, missing IDs, and version conflicts;
configuration defaults, `.env` loading and environment precedence; origin parsing and CORS preflight;
driver-specific engine arguments; configured SQLite persistence across a process restart; and the observation API, provenance, partial coverage, provider failures, cache expiry/reuse, concurrent requests, stale farm versions, and durable snapshot references.
Tests use temporary databases, including application startup, rather than the configured farm database.
No live NASA or AI access is required. The pinned Starlette TestClient emits an upstream deprecation
warning about `httpx`; this does not fail the tests.

From the repository root, also validate shared fixtures:

```bash
python scripts/validate_data.py
```

## Climate observations

First create a farm and use its returned ID. Then request inclusive UTC calendar dates:

```bash
curl "http://127.0.0.1:8000/api/v1/farms/YOUR_FARM_ID/observations?start=2025-01-01&end=2025-01-31"
```

Use the returned immutable observation ID to explore a hypothetical rainfall change:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/observations/YOUR_OBSERVATION_ID/rainfall-scenarios" \
  -H "Content-Type: application/json" \
  -d '{"rainfall_change_pct":-30}'
```

This scales available daily rainfall uniformly, preserves missing values and dates, and never
changes the historical snapshot. It is a sensitivity test, not a weather, yield, soil, or crop
forecast. Rotation candidate recalculation remains a separate unimplemented endpoint.

Swagger UI provides the same endpoint. Both dates are required, must use `YYYY-MM-DD`,
and must satisfy `1981-01-01 <= start <= end < today (UTC)`, matching the existing POWER
adapter's historical-date policy. Unknown query parameters are rejected. IDs are looked up
as stored strings, preserving compatibility with existing farms; absent IDs, including malformed
or unknown UUID strings, return 404 without calling NASA.

The route reads the stored farm's latitude, longitude, and input version, then looks for a
fresh persisted snapshot. On a cache miss it calls the
`ObservationAdapter.observe(latitude=..., longitude=..., start=date, end=date)` boundary.
`get_observation_adapter` supplies `NASAPowerObservationAdapter` by default. It calls
Matheesha's existing `fetch` and `normalize` functions in `backend/services/nasa_power.py`.
That module and its package initializer were imported unchanged from
[`matheesha/nasa-power-integration`, commit `c580b4f`](https://github.com/mbimsara/NASA-Space-App/tree/c580b4fc620212f5450e388ed951e7cef5c014f6).
The route also exposes his rainfall-scenario function against stored snapshots. SMAP remains a
separate pipeline. No crop calculations or provider normalization algorithms were reimplemented.

The integration response preserves Matheesha's normalized `daily`, `monthly`, summary,
source, API, parameter, and resolution metadata. The original API contract's
`summary.rainfall_mm` is an alias of his `summary.rainfall_total_mm`.
`coverage.available_days` counts dates with **both** temperature and rainfall present;
separate valid-day counts and per-variable missing-date lists avoid ambiguity.
The normalizer supplies the calculations; the HTTP layer adds IDs, the farm version,
units, calculation descriptions, and explicit coverage limitations.

POWER results retain `data_kind: modeled`: regional gridded estimates are not direct
field measurements. Test adapters return `synthetic`, with explicit synthetic source labels.
The backend does not replace provider failures with fixtures or relabel modeled data as observed.

This shortened response example shows **synthetic, entirely missing test data**, not a NASA
retrieval. Real responses also include daily/monthly arrays, provider coordinates,
parameter metadata, documentation URL, API metadata, units, and aggregation descriptions.

```json
{
  "schema_version": "0.1",
  "observation_id": "server-allocated-id",
  "farm_id": "registered-farm-id",
  "input_version": 1,
  "data_kind": "synthetic",
  "provider": "NASA POWER",
  "period": {"start": "2025-01-01", "end": "2025-01-01"},
  "retrieved_at": null,
  "source_refs": ["synthetic-test-not-nasa"],
  "source_url": null,
  "spatial_resolution": null,
  "time_standard": "UTC",
  "coverage": {
    "expected_days": 1,
    "available_days": 0,
    "temperature_valid_days": 0,
    "precipitation_valid_days": 0
  },
  "summary": {
    "rainfall_mm": null,
    "rainfall_total_mm": null,
    "rainfall_available_days_mm": null,
    "mean_temperature_c": null
  },
  "missing_data": {
    "temperature_missing_dates": ["2025-01-01"],
    "precipitation_missing_dates": ["2025-01-01"]
  },
  "limitations": ["Synthetic example; every measurement is unknown."]
}
```

The full response schema is exposed through `/docs` and `/openapi.json`.
Rainfall is millimeters; daily rainfall rate is mm/day; temperature is Celsius.
Daily rates are summed over one-day intervals. A missing rainfall day makes the complete
period total null; `rainfall_available_days_mm` remains a separately labeled partial sum.
Temperature means use valid days only and are null when all days are missing. Valid zeros
are preserved. Monthly entries cover the requested dates within each month, which may be partial.
Actual source IDs, API versions and UTC retrieval timestamps come from the adapter. API
version metadata is not a dataset release version. Unknown resolution or retrieval time stays
null and is explained; no source release version is invented.

| Condition | HTTP status / error code |
| --- | --- |
| Unknown farm | 404 / `NOT_FOUND` |
| Missing, malformed, reversed, unsupported dates or extra query fields | 422 / `VALIDATION_ERROR` |
| Cache miss/expiry with disabled/missing adapter, network failure, bad provider units, or unusable provider payload | 503 / `SERVICE_UNAVAILABLE` |
| Snapshot storage failure | 503 / `SERVICE_UNAVAILABLE` |
| Unknown observation ID | 404 / `NOT_FOUND` |
| Valid payload with partial or entirely missing observations | 200, null values, coverage and limitations |

Errors use the existing `{ "error": { "code": "...", "message": "..." } }` envelope;
validation errors also include `fields`. Provider internals are not returned to callers.

### Configuration and current limits

NASA POWER requires no API key for this adapter. Allow outbound HTTPS to
`power.larc.nasa.gov` in the deployment environment. Set `NASA_POWER_ENABLED=false`
in the root `.env` or process environment to disable provider access; restart after changes.
No dynamic import path or provider URL supplied by a request is executed.

Provider calls run in FastAPI's synchronous worker thread, with the existing adapter's
60-second timeout and no retries. Fresh-cache hits do not call the provider. If the provider
is disabled or unavailable and no fresh matching snapshot exists, the API returns 503.
It does not silently serve expired data or substitute synthetic fixtures.

### Cache and immutable snapshot policy

Successful normalized responses are stored in `observation_snapshots` in the configured
database, together with a deep copy of the farm profile and its input version. The complete
response JSON preserves source/API metadata, retrieval time, units, spatial resolution,
summary/daily/monthly values, missing-date lists, and limitations. Cached-at and expiry times
are separate from the original provider retrieval time; a cache hit never rewrites that time.

The cache key includes the farm ID, input version, latitude/longitude, inclusive date range,
and the adapter's versioned namespace. The POWER namespace identifies its daily endpoint,
T2M/PRECTOTCORR parameters, AG community, UTC time standard, imported normalizer version,
and HTTP contract version. Custom/test adapters must supply a separate `cache_namespace`;
synthetic test caches cannot satisfy a real POWER request.

- The default lifetime is 86,400 seconds (24 hours), configurable using
  `OBSERVATION_CACHE_TTL_SECONDS`. Changing this setting affects new snapshots; existing
  snapshots retain their stored expiry times.
- Repeated fresh requests return the same response and stable `observation_id`, including
  after server restarts. Headers identify `X-Observation-Cache: HIT` or `MISS` and
  `X-Observation-Expires-At`. `Cache-Control: no-store` leaves reuse to the backend's
  farm/version-aware cache rather than the browser.
- Expiry causes the next request to fetch and append a new snapshot with a new ID.
  Existing snapshots are not overwritten. Expired IDs remain readable through
  `GET /api/v1/observations/{observation_id}`.
- Any farm PATCH increments its input version and selects a separate cache entry, even
  if coordinates did not change. Original snapshots retain the profile/version used before
  provider access. A farm edit during a fetch does not relabel the returned historical snapshot.
- A unique database constraint on cache key/generation resolves concurrent cache fills to
  one stored ID. Concurrent misses may still issue duplicate provider requests; there is no
  distributed request lock. Bounded collision retries can return 503 under sustained contention.
- Failed requests and unusable provider payloads are not cached. A failed expired refresh
  returns 503 and leaves older snapshots intact. Explicit ID reads still return the original
  snapshot, with its original version and retrieval date.

Snapshot storage is append-only through this service. There is currently no background
refresh, cleanup/retention job, or cross-farm cache sharing. Partial/all-missing but structurally
valid provider results use the same cache lifetime and retain their coverage disclosures.
SMAP, historical risk indicators, forecasts, scenarios, crop recommendations, and rotation
endpoints are not exposed by this route.

### Crop rotation analysis

`POST /api/v1/farms/{farm_id}/rotations` is implemented and stores an immutable
analysis snapshot. It validates the farm version, persisted observation
ownership/version, ordered season labels, and catalog version before invoking
the shared `agrosphere_rotation` package. Only approved catalog entries are
eligible, so the current research-pending catalog returns a successful empty
candidate list with explicit reasons. A single historical observation window is
not duplicated across multiple future seasons; season water fields stay unknown
until dated inputs exist for each season.

### Rotation analysis references

A future analysis can persist a foreign-key reference to `observation_snapshots.id` and
use the saved `farm_profile`, `input_version`, and `payload` without refetching NASA data.
The integration provides this validation helper; it does not run crop algorithms:

```python
from app.services.observation_cache import require_observation_for_analysis

snapshot = require_observation_for_analysis(
    db, observation_id, farm_id=farm_id, input_version=expected_input_version
)
# snapshot.payload: original response; snapshot.farm_profile: original farm inputs
```

The helper rejects unknown IDs with `ObservationNotFound` (future API: 404) and mismatched
farm/version or outdated current inputs with `ObservationContextConflict` (future API: 409).
Cache expiry alone does not invalidate a historical snapshot reference. Old snapshots remain
readable by ID after a farm edit but cannot silently be used for an analysis of new inputs.
A future analysis endpoint must also recheck the farm input version when committing its result,
especially if a calculation can overlap a farm edit. No analysis endpoint/table is implemented here.

### Live verification — 2026-11-14

The real adapter was called for the documented Sri Lankan demonstration point, latitude
8.3 and longitude 80.4, for 2025-01-01 through 2025-01-31. An additional isolated-database
API check verified fetch → persisted snapshot → cache hit with provider disabled → ID read
→ successful farm/version reference validation. No existing farm database was used for this check.

| Returned metadata/result | Actual value from the API check |
| --- | --- |
| Retrieval timestamp | `2026-11-14T09:43:09.547609Z` |
| Provider/source | NASA POWER / MERRA2 |
| API version | `v2.10.3` |
| Data kind | `modeled` |
| Temperature/rainfall coverage | 31/31 days for both variables |
| Mean temperature | 24.4877 C |
| Full-period rainfall | 221.69 mm |
| Source grid resolution | 0.5 degrees latitude × 0.625 degrees longitude |
| First/repeated request | MISS / HIT, identical response and observation ID |

These are actual retrieved gridded estimates for that historical request, not direct field
measurements or test fixture values. Provider data can be revised, so preserve each snapshot's
actual retrieval metadata. Live verification is separate from the offline automated suite.
To repeat manually, create a farm using the documented location, call the observations URL
above twice, inspect its cache headers, then fetch `/api/v1/observations/RETURNED_ID`.

### Observation tests

From `backend/`, with the virtual environment active:

```bash
python -m pytest tests/test_observations.py tests/test_observation_cache.py -q
python -m pytest -q
```

Tests inject an adapter through `app.dependency_overrides[get_observation_adapter]`.
The committed provider-shaped fixture in `backend/tests/fixtures/nasa_power.synthetic.json`
is invented test input. Test results explicitly set `data_kind: synthetic` and preserve
synthetic source IDs. Provider network access is blocked by a shared test fixture.
Tests cover leap days, coordinates, farm versions, request validation, safe errors,
metadata, partial/all-missing coverage, valid zeros, unchanged farm behavior, and the calls
to Matheesha's fetch/normalize functions. Cache tests also cover repeated requests, expiry,
provider/storage failures, version/coordinate changes, concurrent fills, process restarts,
and future analysis reference validation. No live provider data is required.
