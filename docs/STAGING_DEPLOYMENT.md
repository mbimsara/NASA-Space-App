# Restricted staging deployment and readiness

Status: local preparation only; no external deployment authorized. This is not a
production release. Application authentication, tenant ownership checks, deletion
and retention policy, and per-user audit trails are not implemented. Every gateway
reviewer can access every record. Use only fictional farm profiles and no personal
or commercially sensitive information. Do not import a developer's existing DB.

## Architecture and audit findings

Recommend one small, patched Linux VM with Docker Compose, encrypted persistent
disk, and SSH keys restricted to reviewers. Caddy serves the compiled React app
and proxies `/api/*` to one FastAPI worker. Both use the same HTTPS origin so browser
gateway credentials are reused without adding secrets to JavaScript. Only gateway
port **127.0.0.1:8443** is published; the API has no published port. Access through
an SSH tunnel (or a separately reviewed VPN configuration). Firewall inbound to
SSH from approved reviewer networks only; no public HTTP/API listeners.

This keeps the currently validated SQLite concurrency and immutable JSON snapshot
behavior. Do not deploy on an ephemeral/serverless filesystem, share a SQLite file
over a network filesystem, scale replicas, or add workers. Persistent disk and
backups are mandatory. Separate static hosting plus a public API is inappropriate
until identity enforcement protects both services and direct API bypass is closed.

| Finding | Treatment / remaining requirement |
| --- | --- |
| Farm, plan, feedback and climate-twin endpoints lack user ownership | Mandatory private tunnel plus gateway password; fictional records only. Real-data use is blocked pending application auth/authorization. |
| CORS is browser policy, not access control | Explicit HTTPS origin plus staging write-Origin check; authentication remains at gateway. A non-browser client can forge Origin. |
| Relative SQLite default and `create_all` startup | Staging rejects relative/in-memory/non-SQLite URLs; named volume persists across container replacement. `create_all` creates missing tables, never migrates existing columns. |
| No schema migration history | No schema/model changes in this work. Back up before each update, compare schema and test restoring a clone. Incompatible schema releases are blocked until reviewed Alembic revisions and data migration/rollback procedures exist. |
| Provider URLs can contain coordinates | Disable Uvicorn and gateway access logs; staging logs UUID, method, status and duration only. Never log bodies, questions, auth headers or query strings. Restrict operational/error logs too. |
| Optional OpenAI provider can send grounded text externally | Staging requires deterministic assistant; no API key or external AI calls. Existing development behavior is preserved. |
| NASA POWER depends on outbound network | Allow DNS and outbound HTTPS; POWER needs no secret in this adapter. Report unavailable data/503 honestly; never substitute fixtures. Optional SMAP/GPM/HLS local `.cache` artifacts are excluded and remain unavailable until separately verified and provisioned. |
| Crop catalog scientific status | Unchanged. No approved candidates is an honest successful empty analysis; saving a nonexistent candidate is prohibited. |
| Build context could include local credentials and databases | Root `.dockerignore` allows only build/runtime inputs and excludes env files, caches, credentials, tests and databases. Gateway final image contains only compiled assets plus Caddy config. |
| Existing CI covers tests but not hosting | Added staging container build, config validation and gateway HTTP smoke workflow; this does not deploy. Local Docker is unavailable here, so this gate must run before hosting approval. |
| Shared CI installed only the rotation package despite newer backend imports | Shared checks now install the existing backend/CI requirements and set `PYTHONPATH`, with external sockets disabled. |

No blanket vulnerability clearance is claimed. A local `pip-audit` scan of all 30
pinned Python requirements (no skipped packages) reported no known vulnerabilities.
Both the full `npm audit` and `npm audit --omit=dev` reported two moderate affected-package entries
(`react-router` and `react-router-dom`), covering
[open redirects](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6) and
[SSR hydration constructor injection](https://github.com/advisories/GHSA-337j-9hxr-rhxg).
This build serves a client-side SPA, not React Router SSR, but that alone does not
clear the dependency findings. Npm proposes a major upgrade to 7.x; no automatic
upgrade was applied. Review applicability/remediation or explicitly accept staging
risk before access is enabled. The audit environment/report are local ignored
artifacts under `.cache/`, not deployment inputs.

Python runtime requirements are pinned but include test packages; optional Earthdata/OpenAI packages are excluded.
Base images use version tags, not immutable digests. Before approval, build using
the lockfile, run `pip-audit` and `npm audit`, scan both final images (e.g. Trivy),
review findings, record SBOMs/digests, and pin reviewed image digests. Do not blindly
upgrade dependencies or teammates' algorithms to address findings.

## Configuration

Copy `deploy/staging/.env.example` to a **private file outside the checkout**.
Compose accepts it with `--env-file`; `chmod 600` it. Do not reuse the root local
`.env`, real NASA credentials, local DB, `.cache`, `.netrc`, SSH keys or cloud files.

| Variable | Value and location |
| --- | --- |
| `STAGING_DOMAIN` | Reviewer-only hostname, e.g. `staging.agrosphere.internal`; gateway virtual host |
| `STAGING_ORIGIN` | Exact `https://staging.agrosphere.internal:8443`, no slash/path; build-time frontend URL and backend CORS origin |
| `STAGING_USER` | Gateway reviewer account name; not application identity |
| `STAGING_PASSWORD_HASH` | Caddy bcrypt hash, single-quoted in Compose env file to preserve dollar signs; never plaintext |
| `APP_ENV` | Compose sets `staging`; disables docs/OpenAPI, enables Host/Origin checks and minimal request logging |
| `DATABASE_URL` | Compose fixes `sqlite:////var/lib/agrosphere/agrosphere.db`; volume mounted at that directory, owned by UID 10001 |
| `CORS_ORIGINS` | Compose sets exact `STAGING_ORIGIN`; no wildcard, localhost or HTTP default in staging |
| `NASA_POWER_ENABLED` | `true`; real NASA provider remains unmodified |
| `OBSERVATION_CACHE_TTL_SECONDS` | `86400`; cache expiry is not a backup policy |
| `ASSISTANT_PROVIDER` | `deterministic`; English only, si/ta return 422 |
| `VITE_USE_FIXTURES` | Image build fixes `false`; no runtime fallback to demo results |
| `VITE_API_BASE_URL` | Image build sets `${STAGING_ORIGIN}/api/v1`; rebuild gateway if origin changes |

All `VITE_*` values are public bundle contents. Put no credentials there. Root
`.env.example` remains for local development; it is excluded from image builds.
Do not set test-only `AGROSPHERE_E2E`, `E2E_*` or probe flags in staging.

## Deployment procedure (after review, not executed by this change)

1. Provision a dedicated Linux VM, Docker Engine/Compose v2, SSH keys, encrypted
   persistent disk, host updates and inbound firewall. Confirm `docker ps` and
   host firewall policy cannot expose ports 8000/443/8443 publicly. Docker group
   membership grants root-equivalent access; restrict it to operators.
2. Review source and tests. Use an approved immutable source revision/artifact,
   not an unreviewed moving branch. Copy the example env outside the checkout.
   Generate a gateway password hash interactively (no plaintext CLI argument):

   ```sh
   docker run --rm -it caddy:2-alpine caddy hash-password
   chmod 600 /secure/agrosphere-staging.env
   ```

   Put the hash in the single-quoted value; use a strong unique password shared
   only with authorized reviewers. Missing credentials stop Compose; placeholders
   must be replaced. Rotation means updating the hash and recreating gateway.
3. From repository root, validate and build. Keep full rendered config private
   because it contains the password hash:

   ```sh
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml config --quiet
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml build --pull
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml run --rm --no-deps gateway caddy validate --config /etc/caddy/Caddyfile
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml up -d
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml ps
   ```

   Runtime command is `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
   --no-access-log --no-proxy-headers` **inside the unpublished container only**.
   Do not use `--reload`, Vite dev server, or `vite preview` for hosting.
4. Caddy uses its internal CA, persisted in `caddy_data`, for this private name.
   Copy **only the public root certificate**, distribute it through a trusted
   channel and verify its fingerprint; trust it on reviewer machines:

   ```sh
   docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml cp gateway:/data/caddy/pki/authorities/local/root.crt ./staging-root.crt
   ```

   Never distribute the CA private key. Do not bypass browser TLS warnings or use
   curl `-k` as a deployment procedure. An organization-issued cert/VPN DNS can
   replace the private CA only after reviewing that configuration.
5. Reviewer: map `staging.agrosphere.internal` to `127.0.0.1` in local hosts and
   open `ssh -N -L 8443:127.0.0.1:8443 reviewer@VM`. Browse
   `https://staging.agrosphere.internal:8443`, sign in through gateway challenge.
   The exact origin, hostname, port and frontend build must agree.
   Gateway container health waits for its CA certificate to exist; it is not a
   substitute for the authenticated HTTPS checks below.
6. Verify anonymous root and `/api/v1/health` return 401, authenticated health/ready
   return 200, invalid Host is rejected, and API cannot be reached from the public
   network or directly on port 8000. Curl `--user reviewer` prompts for password:

   ```sh
   curl --cacert staging-root.crt -i https://staging.agrosphere.internal:8443/api/v1/health
   curl --cacert staging-root.crt --user reviewer https://staging.agrosphere.internal:8443/api/v1/ready
   ```

   `/health` retains its existing liveness contract. New `/ready` verifies DB
   connectivity and expected tables, returns generic 503 if unavailable, never
   calls NASA, and does not prove disk capacity, backup health or provider uptime.
   Command-line writes must also send `Origin: <STAGING_ORIGIN>`.
   Gateway authentication/body/upstream failures may return 401/413/502 outside
   the FastAPI JSON envelope; do not treat these as successful API results.
7. Use only explicitly fictional farm input. Test create/retrieve/edit, old-version
   409, real POWER observations for a small historical period, rotation, hypothetical
   scenario, English assistant, save a real selected candidate if one exists, and
   reopen plan after API restart. Check request IDs, provenance and null values.
   Verify 404, 422, 503/provider-disabled behavior and no fixture fallback. Test
   Sinhala/Tamil 422, browser offline behavior and gateway logout/credential expiry.
   Close private browser windows and clear local storage after reviewing: the
   frontend stores historical plans/drafts locally, not just on the server.
8. With an empty/unapproved catalog, the production workflow must stop honestly
   at zero candidates. Do not insert fabricated production candidates to complete
   the demo. Run the existing isolated synthetic browser harness separately for
   downstream save/retrieve coverage (commands below). Synthetic NASA-shaped input
   in that harness is explicitly labeled and is never a live NASA verification.

## Persistence, backups, rollback and monitoring

The named `database` volume retains farms, observation snapshots, rotation analysis
snapshots, scenario snapshots, saved plan snapshots and season feedback. Keep the
Compose project name stable. `down` retains named volumes; **never use `down -v`**.
Recreating a VM does not preserve its volume unless its disk is retained/restored.
No model, table, payload or scientific catalog migration is introduced here.

Before upgrades and nightly, take a consistent backup with SQLite's online backup
API; never copy a live database file alone (journal/WAL files may matter). Example
for a small staging DB, from the VM repository root, using a new unique name:

```sh
backup="staging-$(date -u +%Y%m%dT%H%M%SZ).db"
docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml exec -T backend python /app/backup_sqlite.py /var/lib/agrosphere/agrosphere.db "/var/lib/agrosphere/$backup"
docker compose --env-file /secure/agrosphere-staging.env -f deploy/staging/compose.yaml cp "backend:/var/lib/agrosphere/$backup" "/secure/backups/$backup"
chmod 600 "/secure/backups/$backup"
```

The helper refuses overwrite and performs `PRAGMA integrity_check`. Encrypt and
upload the backup to operator-managed off-host storage using a separately
provisioned key; verify upload before retiring local copies. Schedule with an
operator-owned timer; alert on backup failure/age >26h. Suggested staging retention:
7 daily and 4 weekly, target RPO 24h/RTO 4h; the operator must approve capacity,
encryption, destination and retention before enabling hosting. Back up gateway CA
material encrypted separately, or deliberately reissue/trust a new CA after loss.

Perform a restore drill before approval: stop writes, restore the backup to a new
isolated volume, set UID/GID 10001 and file mode 600, run integrity/schema checks,
start the approved image and confirm known fictional farm/observation/plan IDs and
snapshot payloads survive. Never overwrite a running DB. To roll back, stop the
stack, preserve the failed DB for analysis, restore the pre-upgrade backup to a
separate volume and start the prior reviewed image; verify readiness and records
before reopening reviewer access. `create_all` alone is not a rollback or migration.

Host monitoring must check container health/restart count, 5xx frequency, latency,
disk space/inodes, memory, certificate expiry, backup age and restore drill success.
Use authenticated HTTPS checks or internal container readiness; never add a public
health bypass. Suggested alerts: repeated readiness failure, disk >80%, backups
older than 26h. Docker logs rotate at 3 x 10MB per service; restrict operator access
and retention. Minimal request logs omit user/URL data; unhandled exception and
dependency logs still require review. No public monitoring dashboard or log sink.
Gateway has a 1MB request limit, but no per-user rate limit; keep reviewer count
small and enforce additional rate/concurrency controls before wider access.

PostgreSQL is a future migration, not a URL switch: review SQLite locking/version
guards, unique constraints/JSON snapshots, install/pin a driver, create explicit
schema revisions, migrate IDs/payloads, validate counts and relationships, and run
concurrency/persistence tests against real PostgreSQL before changing storage.

## Repeatable local verification

From repository root (PowerShell; test DBs are temporary, no external NASA/AI):

```powershell
$env:PYTHONPATH="$PWD\backend;$PWD"
$env:DATABASE_URL='sqlite:///:memory:'
$env:NASA_POWER_ENABLED='false'
backend/.venv/Scripts/python.exe -m pytest backend/tests --disable-socket --allow-unix-socket -ra
backend/.venv/Scripts/python.exe -m pytest tests --disable-socket --allow-unix-socket -ra
backend/.venv/Scripts/python.exe scripts/validate_data.py
cd frontend
npm test
npm run typecheck
npm run build
npm run lint
npm run test:e2e
$env:E2E_CATALOG='empty'
npm run test:e2e -- --grep 'empty catalog'
Remove-Item Env:E2E_CATALOG
cd ..
git diff --check
```

The default browser tests use a disposable DB, fictional test-only approved crop
and explicit synthetic observations over real loopback HTTP. They do not validate
the Docker gateway, staging HTTPS or real NASA. The separate container CI smoke
workflow builds both images and tests credential enforcement and persistence;
the operator must run it before deployment. Windows pytest-socket may require
`--allow-hosts=127.0.0.1,::1` for TestClient in place of the Unix-socket flags.

Reference design: [FastAPI container deployment](https://fastapi.tiangolo.com/deployment/docker/),
[Caddy basic authentication](https://caddyserver.com/docs/caddyfile/directives/basic_auth),
[Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https), and
[SQLite online backup](https://www.sqlite.org/backup.html).

## Local verification report and modified files

Verified on 2026-11-15: backend 562 tests and 195 subtests passed (including 16
staging regressions); frontend 120 tests passed, TypeScript/build/lint passed;
shared tests 70 passed, 2 skipped (optional HDF5 dependency); shared-data validation
passed. Browser: 4 default tests passed, 3 configuration-gated skips, plus the
separate empty-catalog test passed. The full synthetic browser journey covers
farm creation, observations, rotation, scenario, assistant, save and plan retrieval.
No live NASA or external AI requests were made by these tests. YAML/script parsing
and whitespace checks passed. Existing
Starlette/httpx deprecation and React Router future-flag warnings remain.

Files prepared:

- `backend/app/config.py`, `backend/app/main.py`, `backend/app/staging.py`:
  opt-in staging validation, Host/Origin boundary, disabled docs and minimal logs.
- `backend/app/api/routes/health.py`: additive readiness endpoint.
- `backend/tests/test_staging.py`: configuration, HTTP, restart, backup and YAML tests.
- `deploy/staging/backend.Dockerfile`, `gateway.Dockerfile`, `compose.yaml`,
  `Caddyfile`, `.env.example`, `backup_sqlite.py`, `smoke.py`: private runtime,
  static frontend build, TLS/authentication, backup and CI verification.
- `.dockerignore`, `.gitignore`, `.env.example`: build isolation and secret/storage guidance.
- `.github/workflows/staging-checks.yml`, `backend-tests.yml`, `data-checks.yml`:
  container smoke gate, test triggers and shared CI dependency/import-path repair.
- `backend/README.md`, `docs/API_CONTRACTS.md`, `docs/STAGING_DEPLOYMENT.md`:
  readiness contract, audit, instructions and operational requirements.

Remaining hosting gates: Docker/Caddy builds and authenticated HTTPS smoke have
not run locally (tools unavailable); operator must configure trusted access/TLS,
encrypted disk, off-host backup destination/schedule, restore drill and monitoring;
review dependency findings and scan final images. This is prepared for review,
not certified ready to host. Real farmer data remains prohibited pending ownership
authorization. No scientific code, database models, catalog statuses or frontend
source files were changed, and no commit, push, PR or external deployment was made.
