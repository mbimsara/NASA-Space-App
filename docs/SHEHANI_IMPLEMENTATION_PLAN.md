# Shehani — personal implementation plan

Owner: Shehani Weerasekara (@shehani419). Derived from [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) (Shehani sections and the workload-sharing update). Branch: `branch-shehani`.

Scope reminder: frontend implementation, client integration, workflow QA, **plus** two supporting pieces — crop-catalog loading/validation and a small deterministic financial calculator. Not in scope: Tharuka's design work, Dulanjaya's backend, Bhagya's scientific rules, Matheesha's adapters, Akash's model.

## Status legend

- [x] done on this branch · [~] done against fixtures, needs live API / partner review · [ ] not started (deferred)

## Phase 1 — Core (first handoff: app shell + API client + validated farm form)

| # | Task | Deliverable / completion check | Partner | Status |
| --- | --- | --- | --- | --- |
| 1 | Make the scaffold build | `npm run build` and `npm test` pass; imports, zod v4 API, type-only imports fixed | — | [x] |
| 2 | App shell and routing | Header, farm-scoped navigation, language switcher, routes for farm setup → observations → rotations → scenario → assistant → saved plan; mobile-friendly layout | Tharuka (design review) | [x] |
| 3 | Shared API client and result state | Typed calls, error envelope, retry, `AbortController` + farm-scoped stale-response guard; analyses/scenarios cached by ID and tied to a farm; switching farm clears dependent results | Dulanjaya | [~] |
| 4 | Farm form validation and draft recovery | Required fields, positive area, date order, no future planting dates, explicit units, unknown irrigation/soil stays `null`; Leaflet map picker; crop exclusions; draft resume/clear | Dulanjaya, Bhagya | [~] |
| 5 | Source and assumption displays | `SourceBadge`, `SyntheticDataBanner`, `MissingDataPlaceholder`, assumptions/limitations lists on every result | Matheesha, Bhagya | [~] |
| 6 | Analysis freshness and scenario state | Outdated banner when `input_version` changes; baseline vs hypothetical scenario labelled; saving an outdated analysis is blocked | Dulanjaya | [x] |
| 7 | Rotation comparison and farmer priorities | Candidate cards, timeline, score components, water budget, constraint checks; priority weights from the farm profile, adjustable before a run | Bhagya | [~] |
| 8 | Assistant panel | Tied to selected farm/analysis/scenario/candidate; clears on analysis change; sources + limitations shown | Akash | [~] |
| 9 | Saved plan view | Save selected candidate, reopen by URL after reload, snapshot of sources/assumptions/versions, outdated warning, print view | Dulanjaya | [~] |

## Phase 2 — Supporting calculations (after a working rotation flow)

| # | Task | Deliverable / completion check | Partner | Status |
| --- | --- | --- | --- | --- |
| 10 | Crop catalog loading + validation | `validateCatalog()` mirrors `data/schemas/crop-catalog.schema.json` and `scripts/validate_data.py` cross-rules (unique IDs, approved entries need sources/seasons/family, reviewed catalog needs approved crops, URL/date formats, positive water demand). Catalog page lists issues before the engine consumes data. Unit tests. | Bhagya owns meaning | [x] |
| 11 | Financial calculator | Pure deterministic functions: area conversion (ha/acre/perch), cost categories, revenue and net **ranges**, explicit currency/period, dated sources required. Labelled *pending Bhagya's review*. Unit tests with worked examples. | Bhagya approves formulas | [~] |
| 12 | Language switching | All UI strings in `i18n/locales`; English fallback for missing keys; selection persisted; farm/analysis state preserved | Akash, fluent reviewers | [~] |

## Phase 3 — Verification

| # | Task | Status |
| --- | --- | --- |
| 13 | Automated checks: finance, catalog validation, farm form schema, stale-response guard, store invariants | [x] |
| 14 | Workflow QA checklist ([frontend/QA_CHECKLIST.md](../frontend/QA_CHECKLIST.md)) — run before each integration and at feature freeze | [~] |
| 15 | Accessibility/mobile pass with Tharuka (keyboard, focus after errors, labels, narrow screens) | [ ] needs joint session |

## Deferred (start only after the core journey passes acceptance checks)

Report/export endpoint wiring, action calendar, season feedback, offline viewing → offline editing (needs Dulanjaya's sync contract), voice controls, WeedShield upload. Order if time allows: language review → reports → offline.

## Open dependencies

- **Dulanjaya:** live `/api/v1` endpoints; until then run with `VITE_USE_FIXTURES=true`.
- **Bhagya:** approved financial formulas and range semantics; score/water model for scenario recalculation (fixture scenario math is illustrative only).
- **Matheesha:** time-series field names for observation charts.
- **Tharuka:** Figma link and component styles; approved catalog entries (catalog is currently empty, `research_pending`).
- **Akash / fluent reviewers:** Sinhala and Tamil string review.
