<div align="center">
  <img src="frontend/public/images/agrosphere-logo-transparent.png" alt="AgroSphere AI" width="560" />
  <h1>Earth intelligence. Thoughtful farming.</h1>
  <p>Compare crop rotations, explore water trade-offs, and plan with NASA observations.</p>
  <p><strong>NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data</strong></p>
  <p>
    <a href="#quick-start">Quick start</a> ·
    <a href="#platform">Platform</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#documentation">Documentation</a> ·
    <a href="CONTRIBUTING.md">Contribute</a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/React-TypeScript-149ECA?style=flat-square" alt="React and TypeScript" />
    <img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square" alt="FastAPI and Python" />
    <img src="https://img.shields.io/badge/Data-NASA_POWER_%2B_SMAP-166534?style=flat-square" alt="NASA POWER and SMAP data" />
    <img src="https://img.shields.io/badge/Stage-Development-F0B429?style=flat-square" alt="Development stage" />
  </p>
</div>

---

AgroSphere AI connects Earth observations, farmer inputs, and crop-rotation models in one decision workspace. Start with a farm profile, compare three to five seasons, test rainfall changes, and inspect the evidence behind each result.

**Built for transparent decisions:** observations, hypothetical scenarios, synthetic demonstrations, and measured field inputs keep their own labels. The platform is under development; crop catalogs remain draft and outputs require agronomic review.

## Platform

| Capability | What you can explore |
| --- | --- |
| Farm workspace | Location, crop history, goals, constraints, irrigation, and measured soil inputs in a shared farm record. |
| Earth observations | NASA POWER climate observations with persisted snapshots and caching; SMAP preparation and regional soil-moisture processing tools. |
| Crop rotation | Candidate sequences, constraints, rankings, explanations, and seasonal water budgets. |
| Climate scenarios | Hypothetical rainfall sensitivity applied to saved analyses without changing the original observations. |
| Financial scenarios | Frontend cost and income comparisons using explicit inputs and ranges. |
| Grounded assistant | Deterministic explanations from persisted analysis context, without an external AI provider. The backend currently supports English. |
| Saved plans | Immutable plan APIs, frontend reporting, action-calendar, and cached offline viewing flows. |
| Accessible interface | Responsive layouts, light and dark themes, and English, Sinhala, and Tamil interface resources. |

WeedShield, advanced climate twins, voice interaction, and other capabilities awaiting validated models or data remain on the roadmap. Interface translation availability does not imply multilingual backend assistant support.

### A connected journey

**Create a farm → review observations → compare rotations → test rainfall changes → inspect water and financial trade-offs → ask for an explanation → save a plan.**

Use **View demo** on the welcome page to enter the demonstration experience. Synthetic data is explicitly labelled; it is not evidence about a real farm.

## Quick start

### Requirements

- **Python 3.11+** for the root domain package; CI uses Python 3.12.
- **Node.js 24 and npm 11** for the frontend.
- **Git** and two terminal windows for the full application.

Clone the repository and enter the project:

```bash
git clone https://github.com/shehani419/NASA-Space-App.git
cd NASA-Space-App
```

### 1. Run the backend

<details open>
<summary><strong>Windows PowerShell</strong></summary>

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . -r backend/requirements.txt
Copy-Item .env.example .env
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

</details>

<details>
<summary><strong>Linux / macOS</strong></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . -r backend/requirements.txt
cp .env.example .env
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

</details>

If `.env` already exists, edit it instead of copying over it. Configuration loads from the repository root. Starting the backend from `backend/` places the default SQLite database there.

| Local endpoint | Purpose |
| --- | --- |
| [Health](http://127.0.0.1:8000/api/v1/health) | Check backend availability |
| [API explorer](http://127.0.0.1:8000/docs) | Interactive request documentation |
| [OpenAPI](http://127.0.0.1:8000/openapi.json) | Machine-readable API schema |

### 2. Run the frontend

In a second terminal, from the repository root:

```powershell
Set-Location frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

On Linux/macOS, use `cd frontend` and `cp .env.example .env.local`. If the environment file already exists, edit it instead. On PowerShell systems that block `npm.ps1`, use `npm.cmd` for these commands.

Open **[localhost:5173](http://localhost:5173)** after Vite starts.

### 3. Choose your data mode

Configure `frontend/.env.local`, then restart Vite:

| Setting | Behavior |
| --- | --- |
| `VITE_USE_FIXTURES=false` | Default live mode. Calls the backend at `VITE_API_BASE_URL`. |
| `VITE_USE_FIXTURES=true` | Explicit synthetic demonstration mode for UI exploration without the backend. |
| `VITE_API_BASE_URL=http://localhost:8000/api/v1` | Local backend URL. |

Live NASA retrieval requires provider connectivity. SMAP downloads and optional HDF5 processing have separate prerequisites documented in the SMAP guides.

## Architecture

```text
React + TypeScript workspace
           |
           +-- live API --> FastAPI --> SQLite snapshots and farm records
           |                  |
           |                  +-- crop-rotation and water-budget domain engine
           |                  +-- NASA POWER observation services
           |                  +-- scenarios, grounded assistant, saved plans
           |
           +-- explicit fixture mode --> labelled synthetic examples

SMAP utilities --> discovery, quality filtering, regional environment context
```

| Location | Responsibility |
| --- | --- |
| `frontend/src/` | React pages, routing, API clients, state, translations, finance, and offline flows |
| `backend/app/` | FastAPI routes, validation, persistence, configuration, and application services |
| `backend/services/` | Provider-facing NASA POWER and climate modules |
| `src/agrosphere_rotation/` | Crop catalogs, candidates, constraints, scoring, and water budgets |
| `data/catalogs/` | Versioned crop and water catalogs; eight demo-reviewed screening crops with explicit FAO proxy limitations |
| `data/fixtures/` | Explicitly synthetic development examples |
| `data/schemas/` | Shared JSON contracts |
| `scripts/` | Data validation, POWER, SMAP, and environment utilities |
| `tests/` and `backend/tests/` | Domain, provider, API, persistence, and integration checks |
| `docs/` | Scientific assumptions, contracts, architecture, and integration handoffs |
| `.github/workflows/` | Shared-data, backend, and frontend CI |

### Backend coverage

Implemented routes cover health, farm creation and versioned updates, observation snapshots, rainfall sensitivity, immutable rotation analyses, analysis scenarios, grounded assistant messages, and saved plans. See the [backend guide](backend/README.md), [API contracts](docs/API_CONTRACTS.md), and [assistant and saved-plan handoff](docs/ASSISTANT_SAVED_PLANS_INTEGRATION.md) for exact contracts.

## Verification

From the repository root, with the Python environment active:

```bash
python -m pip install -e ".[dev]"
python scripts/validate_data.py
python -m pytest tests -v
```

From `backend/`, after installing backend dependencies:

```bash
python -m pytest -q
```

From `frontend/`, after `npm ci`:

```bash
npm run typecheck
npm test
npm run build
```

Additional checks are available through `npm run lint` and `npm run test:e2e`; browser tests require their Playwright setup. Optional SMAP HDF5 tests use `backend/requirements-smap.txt`. CI runs checks according to each workflow's path filters.

## Data and model principles

- **Traceable sources:** show dates, units, coverage, and spatial context with observations.
- **Measured inputs stay distinct:** regional soil-moisture context does not establish field nutrient levels or replace soil tests.
- **Scenarios stay hypothetical:** rainfall sensitivity is not a weather forecast; saved baselines remain unchanged.
- **Unknown values stay visible:** missing water inputs are not silently converted into known supply.
- **Estimates carry assumptions:** rotation scores and financial ranges depend on the catalog, model, local inputs, and their review status.
- **Explanations use actual context:** assistant responses resolve stored farm and analysis records.
- **Demonstrations stay labelled:** synthetic fixtures are for development and walkthroughs.

POWER and SMAP have implemented integration or processing paths. GPM and HLS remain sources to evaluate for appropriate access, coverage, licensing, and resolution.

## Roadmap

| Phase | Focus |
| --- | --- |
| Connected core | Farm records, historical observations, rotations, water budgets, rainfall scenarios, grounded explanations, and saved plans |
| Planning and follow-through | SoilRevive and FarmRecovery planning modes, cover crops, financial scenarios, reminders, reporting, and season feedback |
| Advanced capabilities | Validated weed analysis, climate twins, and reviewed multilingual voice interaction |

These phases describe product direction, not a claim that every feature is complete. See the [implementation plan](IMPLEMENTATION_PLAN.md) and [backlog](docs/BACKLOG.md) for responsibilities and acceptance criteria.

## Documentation

| Guide | Start here when you need… |
| --- | --- |
| [Frontend](frontend/README.md) / [Backend](backend/README.md) | Application setup and integration details |
| [Demo walkthrough](docs/DEMO.md) | A connected demonstration and fallback rules |
| [Contributing](CONTRIBUTING.md) | Development workflow and review expectations |
| [Architecture](docs/ARCHITECTURE.md) / [API contracts](docs/API_CONTRACTS.md) | Boundaries, fields, units, and errors |
| [Implementation plan](IMPLEMENTATION_PLAN.md) / [Backlog](docs/BACKLOG.md) | Team responsibilities and delivery work |
| [Data sources](docs/DATA_SOURCES.md) / [Attribution](docs/ATTRIBUTION.md) | Provider research and credit requirements |
| [Climate handoff](docs/CLIMATE_HANDOFF.md) | Working climate interfaces and examples |
| [Environment contract](docs/ENVIRONMENT_CONTRACT.md) | Unified POWER/SMAP responses and sensitivity examples |
| [SMAP preparation](docs/SMAP.md) / [Automation](docs/SMAP_AUTOMATION.md) | Discovery, filtering, sign-in, and resumable downloads |
| [Agronomy rules](docs/AGRONOMY_RULES.md) | Evidence and model review |
| [Design handoff](docs/DESIGN.md) | The integrated visual system |
| [Assistant and saved plans](docs/ASSISTANT_SAVED_PLANS_INTEGRATION.md) | Grounded explanations and immutable plan APIs |
| [Shared data](data/README.md) | Catalogs, fixtures, and schemas |

## Contributing

Use the single application in `frontend/` and follow [CONTRIBUTING.md](CONTRIBUTING.md). Keep changes focused, update affected contracts, and run the relevant checks before opening a pull request.

Keep `.env` files, credentials, SQLite databases, caches, `.venv/`, `node_modules/`, and generated build output out of Git. Team ownership and integration responsibilities are recorded in the [six-member implementation plan](IMPLEMENTATION_PLAN.md).

---

<div align="center">
  <strong>AgroSphere AI</strong><br />
  Earth data. Local knowledge. Thoughtful farming.
</div>
