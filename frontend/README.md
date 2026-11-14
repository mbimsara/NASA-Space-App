# AgroSphere official frontend

React 19 + TypeScript application for the core farmer journey: farm setup → observations → rotation comparison → rainfall scenario → assistant → saved plan, plus crop-catalog validation and a financial range calculator.

This directory is the single official frontend. It combines Tharuka's forest/emerald visual direction and approved imagery with Shehani's routing, state, API client, fixtures, validation, finance logic, and tests. See the [implementation plan](../docs/SHEHANI_IMPLEMENTATION_PLAN.md) and [QA checklist](QA_CHECKLIST.md).

`design-prototype/` remains a visual reference. Do not connect APIs or add authoritative values there; migrate approved patterns into `src/`.

## Requirements and commands

Node 24 (tested with v24.13.0) and npm 11.

```bash
npm ci
npm run dev        # http://localhost:5173
npm run lint
npm test           # Vitest unit tests
npm run typecheck  # TypeScript, single-threaded to limit memory use
npm run build
```

Stop the Vite process with `Ctrl+C` before running `npm ci` again on Windows. Otherwise the native Rolldown file can remain locked and cause an `EPERM unlink` error.

## Configuration

Copy `.env.example` to `.env.local`. These values are public; never place provider keys in a Vite environment file.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Dulanjaya's API |
| `VITE_USE_FIXTURES` | `true` (anything except `false`) | Use the contract-shaped synthetic fixture service stored in browser `localStorage` |

Fixture mode supports the complete demonstration journey and shows a persistent warning ribbon and `synthetic` badges. Set `VITE_USE_FIXTURES=false` only when testing implemented live routes. The backend currently exposes health, farm, and observation routes; rotation, scenario, assistant, and saved-plan routes remain to be connected.

## Structure

| Path | Purpose |
| --- | --- |
| `src/api/client.ts` | Typed live API client and error-envelope handling |
| `src/api/fixtures.ts` | Contract-shaped synthetic service, persistence, conflicts, exclusions, and scenario recalculation |
| `src/api/requestGuard.ts` | Abort and stale-response protection |
| `src/hooks/useAppStore.ts` | Selected farm, analysis, scenario, candidate, and browser persistence |
| `src/catalog/` | Validated loading path for `data/catalogs/crops.json` |
| `src/finance/calculator.ts` | Deterministic, provenance-aware financial ranges |
| `src/components/` | Official shared layout, rotation, observation, scenario, and UI components |
| `src/pages/` | Routed pages for the complete journey, catalog, and finance |
| `src/index.css` | Official Tharuka-derived visual tokens and responsive component styling |
| `public/images/` | Approved visual assets migrated from the design prototype |

## Integration rules

- Accept results only for the currently selected farm or baseline; late responses are discarded.
- `PATCH /farms/{id}` sends `expected_input_version`. Farm changes mark existing analyses outdated.
- The observation chart accepts Matheesha's normalized `daily[]` values and preserves separate rainfall/temperature coverage and missing dates.
- Unknown measurements remain `null` and display as “Unknown,” never as zero.
- Unknown irrigation makes water availability, balance, coverage, and water-based scoring unavailable.
- Saved plans need `input_snapshot` and `analysis_snapshot`; see `SavedPlan` in `src/types/api.ts`.
- Prototype sample values are never copied into authoritative fixtures, API responses, or recommendations.
