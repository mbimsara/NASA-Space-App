# Frontend integration notes — for the merge

Owner: Shehani (`branch-shehani`). Checked against every team branch on origin on 2026-11-14. Please reply in the team chat or edit this file if something here is wrong.

## What `branch-shehani` adds

- `frontend/` — complete React app for the core journey (farm setup → observations → rotations → scenario → assistant → saved plan), plus the crop-catalog validation page and the financial calculator (spec v0.1).
- `docs/SHEHANI_IMPLEMENTATION_PLAN.md`, this file.
- No files outside `frontend/` and `docs/` are changed, so merging should not create text conflicts with other branches.
- Until the backend is merged and running, the app uses synthetic fixtures (`VITE_USE_FIXTURES=true`, the default). Set it to `false` to call `VITE_API_BASE_URL` (default `http://localhost:8000/api/v1`).

Run: `cd frontend && npm install && npm run dev` (tests: `npm test`).

## Status per teammate

| Teammate / branch | Status against the frontend | What I need |
| --- | --- | --- |
| **Dulanjaya** — `dulanjaya/backend` | ✅ Farm API matches: `/api/v1` prefix, `{id, input_version, profile}` envelope, PATCH `{expected_input_version, profile}`, 404/409 error envelope, CORS for `localhost:5173`. | (1) Keep validation errors (422) in the `{"error": {code, message, fields}}` envelope, with `fields` keyed by profile path such as `area_ha` or `location.latitude`, so the form can show them beside inputs. (2) Next endpoints the UI already calls: `GET /farms/{id}/observations`, `POST /farms/{id}/rotations`, `POST /analyses/{id}/scenarios`, `POST /assistant/messages`, `POST /farms/{id}/plans`, `GET /plans/{id}`. (3) Saved plans should return `candidate_snapshot`, `input_snapshot` and `analysis_snapshot` (see `frontend/src/types/api.ts` → `SavedPlan`). |
| **Bhagya** — `zerokali20` | ✅ The new `data/catalogs/crops.json` (`0.1-draft-referenced`, 8 crops) passes the frontend catalog validator with no errors; all 8 are `draft`, so none are used for recommendations yet. ✅ Financial calculator updated to spec v0.1 per `docs/FINANCIAL_SPECIFICATION.md` (version/banner, "yield scenario range", per-input URL/document provenance, omitted categories disclosed). | Tell me when crops move to `approved`, and whether rotation results will use the new crop IDs (e.g. `mung-bean`). The UI shows `crop_name` when provided, so please include it in rotation sequences. Rotation UI (per your review): each candidate may carry `water_budget_range` mirroring your `WaterBudgetRange` (demand low/nominal/high, baseline and scenario rainfall, irrigation, available water, balance low/high, coverage low/high %, `demand_basis`, `model_version`, `source_url`, `assumptions`). The analysis may carry top-level `reasons[]` for infeasible or fewer plans. `score` and component `value` may be `null`, and any unknown field shows "Unknown", never 0. Dulanjaya: please pass these through the rotations endpoint unchanged. |
| **Matheesha** — `matheesha/nasa-power-integration` | ⚠️ **Shape mismatch.** Your `environment.synthetic.json` nests the observation under `climate.result.observation`, uses `daily[]` with `precipitation_mm_per_day` / `temperature_c`, `summary.rainfall_total_mm`, and per-variable coverage (`precipitation_valid_days`, `temperature_valid_days`). The UI currently reads the API_CONTRACTS shape: `time_series[]` with `rainfall_mm` / `mean_temperature_c`, `summary.rainfall_mm`, `coverage.available_days`. | Let's agree with Dulanjaya what `GET /farms/{id}/observations` returns. Your shape is richer (per-variable coverage, `provider`, `source_url`, `time_standard`), so I'm happy to adopt it in the frontend; just confirm it's final before I switch. |
| **Akash** — `akash-dev` | ℹ️ `explain(context, question, language="en")` is a service function; there is no HTTP route yet. Only `en` is supported, and other languages raise an error. | The UI sends `{farm_id, analysis_id, scenario_id?, candidate_id?, language, message}` and expects `{role, content, source_ids[], limitations[]}`. For `si`/`ta`, please return a clear error code (e.g. `UNSUPPORTED_LANGUAGE`) rather than a 500 so the UI can explain it and fall back to English. Route to be added by Dulanjaya. |
| **Tharuka** — `tharuk` | ℹ️ `figma-prototype/` is a separate app and doesn't conflict. Styling in `frontend/` is placeholder: colours and spacing are tokens in `frontend/src/index.css`. | Which prototype styles/tokens to adopt in the real frontend. Sri Lankan market/yield values with sources for the finance page (each needs URL/document, dates, area, crop/grade, unit/period). A keyboard/phone review session. Sinhala/Tamil reviewers for `frontend/src/i18n/locales/si.json` and `ta.json`. |

## Shared files to watch during merge

- `data/catalogs/crops.json`: changed on `zerokali20` (and `tharuk`). The frontend imports it directly, so a broken catalog shows on the Catalog page and as a warning on the Rotations page.
- `pyproject.toml` and `src/agrosphere_rotation/`: added on both `tharuk` and `zerokali20`; check these merge cleanly between those two branches.
- `docs/API_CONTRACTS.md`: if any response shape changes (e.g. observations), update it in the same PR so the frontend types follow.

## Suggested merge order

1. `zerokali20` (catalog, agronomy docs, financial spec) and `dulanjaya/backend` (API foundation).
2. `matheesha/nasa-power-integration` and `akash-dev`, after the observation/assistant endpoint shapes are agreed.
3. `branch-shehani` (frontend). Then switch `VITE_USE_FIXTURES=false` and run `frontend/QA_CHECKLIST.md` against the real backend.
4. `tharuk` prototype assets, as reference only.

## Update — replies received 2026-11-14

- **Matheesha / Dulanjaya (observations): resolved in the frontend.** Reads `daily[].precipitation_mm_per_day` / `temperature_c`, shows separate rainfall and temperature coverage plus missing dates, renders `spatial_resolution` as an object, defaults the end date to yesterday (UTC, from 1981-01-01), shows provider/source/documentation links, and sends the loaded `observation_id` with rotation requests. SMAP AM/PM will be charted separately when the API exposes it.
- **Bhagya (rotation-score-0.1): implemented in the UI and fixtures.** Components `water_sufficiency` / `crop_diversity` / nullable `scenario_resilience` on 0–100, requested and effective weights with renormalization shown, spec tie-break order, per-season `water_budget_range` table (plan aggregate is optional and collapsed), checks `catalog_review` / `season_eligibility` / `farmer_exclusion` as `{rule, passed, note}`, `effective_rainfall_mm: null` shown as "Not modeled", 80% placeholder removed, approved wording used, banned phrases absent. Soil/recovery controls are still pending. Unknown irrigation now makes water availability, balances, coverage, and water-based score components null; rainfall-only screening occurs only when irrigation is explicitly confirmed as zero with the agreed field-applied-depth basis.
- **Akash (assistant): aligned.** The UI relies only on `{role, content, source_ids, limitations}` (optional `status` accepted). On `422 UNSUPPORTED_LANGUAGE` it explains the error and offers "Ask in English instead".
