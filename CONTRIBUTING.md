# Contributing

## Start here

1. Read [the implementation plan](IMPLEMENTATION_PLAN.md) and [architecture](docs/ARCHITECTURE.md).
2. Agree on the [API contracts](docs/API_CONTRACTS.md) before changing shared fields.
3. Create a GitHub issue with an owner, dependency, deliverable, and acceptance check. Use [the first milestone backlog](docs/BACKLOG.md).
4. Create a short branch, for example `codex/farm-api` or `codex/observation-charts`.
5. Open a small pull request and request review from the relevant module owner.

## Local setup status

This repository contains planning documents, schemas, synthetic fixtures, and a standalone NASA POWER adapter. There is no runnable web application yet. See [adapter commands](docs/NASA_POWER.md); do not expect `npm install` or a backend server start command to work until the application scaffolds are merged.

- Frontend owner: Shehani; initialize React/TypeScript in `frontend/` and document exact prerequisites and commands there.
- Backend owner: Dulanjaya; initialize FastAPI in `backend/`, select persistence, and document environment setup, migrations, and startup there.
- Commit dependency manifests and lockfiles when scaffolding. Agree on runtime versions and record them.
- Copy `.env.example` to an ignored local environment file when configuring services. Configure the frontend separately using `frontend/.env.example`.

## Shared conventions

- Dates use ISO 8601; timestamps include a timezone. API examples use UTC.
- Internal area is hectares, water depth is millimeters, temperature is Celsius, and coordinates are WGS84 latitude/longitude. Convert explicitly at boundaries.
- Missing measurements are `null`, never zero. Scores and estimates must include assumptions and model versions.
- Synthetic data carries `data_kind: synthetic`; preserve this label in the interface.
- Frontend code never receives provider secrets. Do not commit `.env` files, access tokens, private farmer records, or uploaded field photos.
- A contract change updates documentation, fixtures, validation, and affected consumers in the same PR or an agreed coordinated sequence.
- Do not add a project license without team agreement. Check third-party data/model licenses before use.

## Review and verification

Tharuka reviews visible design changes; Matheesha reviews NASA/climate meaning; Bhagya reviews agronomic calculations; Akash reviews assistant grounding; Dulanjaya reviews API/persistence changes; Shehani reviews client integration.

Run checks relevant to the change. For shared sample data, run `python scripts/validate_data.py` using Python 3.10 or newer (standard library only). For application changes, record the actual lint/type/build/test commands once available. Include screenshots for visible changes, calculation examples for model changes, and limitations where validation is incomplete.

Merge only when the feature's acceptance checks pass and the connected demo still works. Keep follow-on features out of the critical path until the core journey is complete.
