# Frontend — Shehani

React 19 + TypeScript app implementing the core farmer journey: farm setup → observations → rotation comparison → rainfall scenario → assistant → saved plan, plus crop-catalog validation and a financial range calculator. Personal plan: [docs/SHEHANI_IMPLEMENTATION_PLAN.md](../docs/SHEHANI_IMPLEMENTATION_PLAN.md). QA: [QA_CHECKLIST.md](QA_CHECKLIST.md).

## Requirements and commands

Node 24 (tested with v24.13.0) and npm 11.

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # vitest unit tests
npm run typecheck  # tsc (single-threaded to limit memory use)
npm run build
```

## Configuration

Copy `.env.example` to `.env.local`. Values are public; never put provider keys here.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Dulanjaya's API |
| `VITE_USE_FIXTURES` | `true` (anything except `false`) | Use synthetic fixtures stored in browser `localStorage`. Set `false` to call the API. |

Fixture mode shows a persistent ribbon and `synthetic` badges. Fixture data is never NASA data or approved agronomy.

## Libraries

React Router 6 (routing), Zustand (selected farm/analysis state, persisted), Zod 4 (form validation), Axios (live client), Leaflet + react-leaflet with OpenStreetMap tiles (map picker), Recharts (observation chart), i18next (en/si/ta with English fallback), and Vitest + jsdom (tests).

## Structure

| Path | Purpose |
| --- | --- |
| `src/api/client.ts` | Typed live API client; error envelope → `ApiClientError` |
| `src/api/fixtures.ts` | Contract-shaped synthetic backend (persistence, 409 conflicts, exclusions, scenario recalculation) |
| `src/api/requestGuard.ts` | Stale-response guard (abort + "is this still the latest request") |
| `src/hooks/useAppStore.ts` | Selected farm/analysis/scenario/candidate; results are cached per farm and cleared on farm switch |
| `src/catalog/` | Validated loading path for `data/catalogs/crops.json` |
| `src/finance/calculator.ts` | Deterministic cost/revenue/net ranges (spec v0.1-draft, pending Bhagya's review) |
| `src/components/layout/` | App shell; `FarmLayout` loads the farm in the URL |
| `src/pages/` | One page per journey step, plus catalog and finance |

## Integration notes

- Every result is accepted only for the selected farm (analysis) or the selected baseline (scenario), so late responses are dropped.
- `PATCH /farms/{id}` sends `expected_input_version`. A changed profile marks analyses outdated, and saving an outdated analysis is blocked in the UI.
- The live client maps the backend's `daily[]` values into chart `time_series[]`, preserving nulls, zeros, and per-variable coverage. Historical queries end before the current UTC date.
- Farm and observation HTTP routes are implemented. Rotation, scenario, assistant, and saved-plan routes remain integration work; keep fixture mode enabled for the full demonstration journey.
- The backend should store `input_snapshot` and `analysis_snapshot` with saved plans (see `SavedPlan` in `src/types/api.ts`).
