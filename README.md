# AgroSphere AI

A farming decision-support platform for NASA Space Apps Challenge 2026: **Field Shift: Adapting Farms with NASA Data**.

AgroSphere combines Earth observations, farmer inputs, and local agronomy to help farmers compare crop rotations. Every feature supports the same farm profile and rotation decision.

## Start here

The repository includes a runnable React frontend and FastAPI backend with SQLite farm persistence, validation, version checks, and environment-based database/CORS configuration. Farm observations integrate Matheesha's NASA POWER adapter. Rotation scoring is implemented as a Python domain package; its HTTP endpoint and the scenario, assistant, and saved-plan endpoints remain to be connected.

| Resource | Purpose |
| --- | --- |
| [Implementation plan](IMPLEMENTATION_PLAN.md) | Detailed responsibilities for all six members |
| [Contributing](CONTRIBUTING.md) | Setup status, workflow, review and verification |
| [Architecture](docs/ARCHITECTURE.md) | System boundaries and open decisions |
| [API contracts](docs/API_CONTRACTS.md) | Proposed endpoints, fields, units and errors |
| [First milestone backlog](docs/BACKLOG.md) | Concrete starting tasks and acceptance checks |
| [Data sources](docs/DATA_SOURCES.md) | NASA integration research register |
| [Climate handoff](docs/CLIMATE_HANDOFF.md) | Working module interface, examples and teammate integration instructions |
| [Environment contract](docs/ENVIRONMENT_CONTRACT.md) | Unified POWER/SMAP response, reproducible examples and twin sensitivity |
| [SMAP preparation](docs/SMAP.md) | Verified public discovery, quality filtering and account/download prerequisites |
| [SMAP automation](docs/SMAP_AUTOMATION.md) | Private local sign-in, resumable subset jobs, retries and coverage checks |
| [Attribution](docs/ATTRIBUTION.md) | NASA POWER credit and metadata requirements |
| [Agronomy rules](docs/AGRONOMY_RULES.md) | Evidence and model review process |
| [Design handoff](docs/DESIGN.md) | Tharuka's design system as integrated into Shehani's functional frontend |
| [Demo guide](docs/DEMO.md) | Connected walkthrough and fallback rules |
| [Shared data](data/README.md) | Synthetic farm, catalog and schemas |

## Repository structure

| Path | Contents and owner boundary |
| --- | --- |
| `backend/app/` | Dulanjaya's FastAPI application, routes, configuration, SQLAlchemy models, persistence, and observation services |
| `backend/services/` | Matheesha's provider-facing NASA POWER and climate modules used by the backend |
| `backend/tests/` | Backend API, configuration, cache, persistence, and provider-boundary tests |
| `frontend/src/` | Shehani's React/TypeScript application, pages, API client, fixture API, state, catalog validation, and finance calculator |
| `src/agrosphere_rotation/` | Bhagya's crop-rotation domain package: catalog loading, candidates, constraints, scoring, and water budgets |
| `data/catalogs/` | Versioned crop and crop-water catalogs; all eight crops currently remain `draft` |
| `data/fixtures/` | Explicitly synthetic farm, climate, environment, and interface-development examples |
| `data/schemas/` | Shared JSON schemas for persisted and exchanged data |
| `docs/` | API contracts, model specifications, evidence, architecture, data sources, and teammate handoffs |
| `scripts/` | Data validation plus climate, NASA POWER, SMAP, and environment utilities |
| `tests/` | Shared climate, SMAP, environment, rotation, and water-model tests |
| `.github/workflows/` | Shared-data and backend continuous-integration checks |

Generated or local-only directories such as `.venv/`, `frontend/node_modules/`,
`frontend/dist/`, caches, SQLite databases, and `.env` files must remain uncommitted.

## Quick start

### Requirements

- Git
- Python 3.10 or newer (Python 3.12 is used in CI)
- Node.js 24 and npm 11 for the frontend

Clone the repository and enter it before running the following commands.

### 1. Start the backend

The backend loads configuration from `.env` at the repository root. On Windows
PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp .env.example .env
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If `.env` already exists, edit it instead of overwriting it. The default SQLite
database is created under `backend/` when the server is started there.

- Health check: <http://127.0.0.1:8000/api/v1/health>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI document: <http://127.0.0.1:8000/openapi.json>

Currently implemented HTTP routes cover health, farm create/read/update, NASA
POWER observation retrieval, and stored observation snapshots. Rotation,
scenario, assistant, and saved-plan HTTP routes still need to be connected.
See the [complete backend guide](backend/README.md) for configuration, request
examples, cache behavior, database paths, and tests.

### 2. Start the frontend

Open a second terminal from the repository root:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Linux/macOS uses `cp .env.example .env.local` instead of `Copy-Item`. Open
<http://localhost:5173> after Vite starts.

The frontend defaults to `VITE_USE_FIXTURES=true`, which supports the complete
demonstration journey with clearly labelled synthetic data. To exercise the
implemented backend routes, set `VITE_USE_FIXTURES=false` in
`frontend/.env.local` and restart Vite. The full journey cannot use live mode
until the remaining HTTP routes are implemented. See the
[frontend guide](frontend/README.md) for its structure and integration notes.

### 3. Run verification

Root data and domain checks:

```bash
python -m pip install -e ".[dev]"
python scripts/validate_data.py
python -m pytest tests -v
```

Frontend checks, from `frontend/`:

```bash
npm run lint
npm test
npm run build
```

Backend checks require the backend dependencies and run from `backend/`:

```bash
python -m pytest -q
```

GitHub Actions runs shared-data and backend checks on relevant pushes and pull
requests. Optional SMAP HDF5 tests install the dependencies in
`backend/requirements-smap.txt` in their separate CI job.

## Product scope

### Original modules

1. **My Farm Digital Twin:** select a farm and explore historical rainfall, temperature, regional soil moisture, and vegetation observations.
2. **Smart Crop Rotation:** compare crop sequences over three to five seasons using farm conditions, constraints, and priorities.
3. **Climate Scenarios:** explore historical climate risk indicators and test hypothetical changes such as reduced rainfall.
4. **WeedShield:** explore photo-based weed coverage analysis after selecting and validating a suitable model.
5. **SoilRevive:** compare rotation strategies for soil cover, crop diversity, and legumes.
6. **FarmRecovery:** compare recovery strategies following floods or droughts.
7. **Global Climate Twin Finder:** identify regions with similar historical climate patterns.
8. **AI Assistant:** explain actual farm analysis and rotation results in English, Sinhala, and Tamil.

### Added features

| Feature | Intended behavior | Delivery priority |
| --- | --- | --- |
| Farm History & Seasonal Calendar | Record previous crops, planting dates, irrigation, and harvests; use history when evaluating rotations. | Core |
| Farmer Goals & Constraints | Capture water limits, budget, labor, preferred crops, and household food needs. | Core |
| Rotation Comparison Workspace | Compare crop sequences, suitability, water demand, soil benefits, risks, and ranking explanations. | Core |
| Water Budget Planner | Compare estimated seasonal crop water requirements with rainfall and farmer-entered irrigation supply. | Core |
| Soil Test Integration | Accept measured soil pH, organic matter, and nutrient results with units and sampling dates. | Core |
| Cost & Income Scenarios | Compare estimated costs and potential returns using local inputs and price ranges. | Next |
| Cover Crop Planner | Include locally suitable cover crops between main growing seasons. | Next |
| Farm Alerts & Action Calendar | Turn a selected rotation into planting, monitoring, and soil-testing reminders. | Next |
| Offline Farm Notebook | Save farm details and previously generated plans for limited-connectivity use. | Next |
| Season Review & Feedback | Record actual outcomes and compare them with previous estimates. | Next |
| Agronomist Review & Shareable Report | Export farm inputs, rotation comparisons, sources, and assumptions for expert review. | Next |
| Voice Input & Read-Aloud | Support accessible input and spoken explanations in English, Sinhala, and Tamil. | Advanced |

## Delivery sequence

1. **Connected core:** farm profile, history, goals, soil inputs, NASA observation dashboard, rotation comparison, water budget, climate scenarios, and grounded assistant explanations.
2. **Planning and follow-through:** soil improvement and disaster recovery modes in the rotation planner, cover crops, financial scenarios, action calendar, reports, offline notebook, and season feedback.
3. **Advanced capabilities:** validated weed analysis, climate twins, and multilingual voice interaction.

All features are in the product scope. These phases describe implementation order, not completed functionality.

## Hackathon demonstration

Use one Sri Lankan demonstration farm and a researched local crop catalog:

**Select farm → enter history, soil results, and priorities → review NASA observations → compare three rotations → simulate reduced rainfall → compare water and soil tradeoffs → ask the assistant to explain → save or share the plan.**

Keep crop rotation central. SoilRevive and FarmRecovery are planning modes that influence the same rotation comparison rather than separate disconnected tools.

## Unified frontend

Tharuka's approved visual system and landing experience are integrated into
Shehani's functional application in `frontend/`. The former standalone sample
prototypes were removed to prevent the team from running or extending the wrong
application. Use the single frontend command in the quick start above.

The unified app retains the working farm setup, Earth-observation display,
rotation comparison, climate scenario, finance, assistant, saved-plan, offline
viewing, action-calendar, and reporting flows. Features without validated data
or backend/model support remain explicitly identified on the roadmap instead of
showing fabricated results.

## Data and model requirements

- Evaluate NASA POWER, GPM, SMAP, and HLS for their appropriate roles; verify access, licensing, resolution, and coverage before integration.
- Show observation sources, dates, units, and spatial resolution. Distinguish regional observations from field measurements.
- Label climate scenarios as hypothetical and disclose rotation scoring and soil-model assumptions.
- Use measured soil tests when available; do not infer exact field nutrient levels from satellite observations.
- Present financial estimates as ranges with input sources and dates; do not promise returns or crop success.
- Ground assistant explanations in actual module outputs and identify missing information.
- Validate photo analysis before claiming reliable weed identification or coverage measurement.
- Store shared farm inputs once so every module uses consistent location, season, crop history, and constraints.

## Current status

The frontend core journey, FastAPI health/farm/observation APIs, SQLite persistence, NASA POWER and SMAP processing, and the rotation-scoring domain package are implemented with automated tests. The frontend currently defaults to synthetic fixtures. Rotation, scenario, assistant, and saved-plan HTTP services remain to be connected before switching the frontend to the live API.

See the [six-member implementation plan](IMPLEMENTATION_PLAN.md) for responsibilities, Tharuka's UI/UX design assignment, integration contracts, milestones, and acceptance checks.
