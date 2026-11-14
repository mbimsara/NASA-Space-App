# Frontend — Shehani

React 19 + TypeScript app implementing the core farmer journey: farm setup → observations → rotation comparison → rainfall scenario → assistant → saved plan, plus crop-catalog validation and a financial range calculator. Personal plan: [docs/SHEHANI_IMPLEMENTATION_PLAN.md](../docs/SHEHANI_IMPLEMENTATION_PLAN.md). QA: [QA_CHECKLIST.md](QA_CHECKLIST.md).

## Requirements and commands

Node 24 (tested with v24.13.0) and npm 11.

```bash
npm ci
npm run dev        # http://localhost:5173
npm test           # vitest unit tests
npm run typecheck  # tsc (single-threaded to limit memory use)
npm run build
npm run lint
npm run test:e2e   # real browser + isolated FastAPI/Vite test servers
```

## Configuration

Copy `.env.example` to `.env.local`. Values are public; never put provider keys here.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Dulanjaya's API |
| `VITE_USE_FIXTURES` | `false` | Live HTTP by default. Only literal `true` enables the synthetic demonstration; invalid values are rejected. |

Fixture mode shows a persistent ribbon and `synthetic` badges. Fixture data is never NASA data or approved agronomy.

Live mode uses `VITE_USE_FIXTURES=false` and
`VITE_API_BASE_URL=http://localhost:8000/api/v1`. Start FastAPI on port 8000 and
Vite on port 5173. No error path switches to fixtures. Set
`VITE_USE_FIXTURES=true` and restart Vite for the separate synthetic demonstration.

Persisted selections, drafts and offline plan caches are isolated by mode/API URL.
Legacy unscoped data is ignored, not deleted or imported into live mode. Cached
plans are shown only on connection failures, with their original provenance and
an offline-copy label; 404/409/422/503 responses remain visible errors.

See [Task 4 verification](../docs/LIVE_MODE_TASK4.md) for setup, real-browser
commands, live NASA evidence and scientific limitations.

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
| `src/finance/calculator.ts` | Deterministic cost/revenue/net ranges: financial specification v0.1 (`docs/FINANCIAL_SPECIFICATION.md`, approved by Bhagya with conditions), with per-input source provenance |
| `src/components/layout/` | App shell (sidebar, top bar, theme toggle), step tracker (`JourneyStepper`), and `FarmLayout`, which loads the farm in the URL |
| `src/pages/` | One page per journey step, plus catalog, finance and roadmap |
| `src/components/plan/ActionCalendar.tsx`, `src/utils/calendar.ts` | Farmer-entered action calendar with `.ics` export (stored on device) |
| `src/utils/offlineCache.ts`, `public/sw.js` | Read-only offline viewing of saved plans; production-only app-shell service worker |

## Integration notes

- Every result is accepted only for the selected farm (analysis) or the selected baseline (scenario), so late responses are dropped.
- `PATCH /farms/{id}` sends `expected_input_version`. A changed profile marks analyses outdated, and saving an outdated analysis is blocked in the UI.
- The observation chart consumes live `daily` records through `toChartPoints`; legacy fixture `time_series` remains supported.
- The backend should store `input_snapshot` and `analysis_snapshot` with saved plans (see `SavedPlan` in `src/types/api.ts`).

## Design

This is the repository's only runnable frontend. It combines Tharuka's approved
landing page, navigation, cards, spacing, and visual language with Shehani's
functional routing, API/fixture integration, forms, validation, accessibility,
offline viewing, calendar, and reporting work. Colours, fonts, radii and shadows
are tokens in `src/index.css`; light and dark themes follow the device setting
until the user toggles them (key `agrosphere-theme`). Accessibility adaptations
include readable minimum text sizes, WCAG-AA muted text, keyboard focus, and
explicit labels for synthetic or modeled values.
