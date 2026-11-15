# Shehani — personal implementation plan

> Historical ownership plan retained for attribution, not current capability
> status. See `COMPLETION_AUDIT.md` and the in-app Capability Status page.

Owner: Shehani Weerasekara (@shehani419). Derived from [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) (Shehani sections, the workload-sharing update, and follow-on dependencies). Branch: `branch-shehani`. Last audited: 2026-11-14.

Scope: frontend implementation, client integration, workflow QA, plus crop-catalog loading/validation and the deterministic financial calculator. Not in scope: Tharuka's design work, Dulanjaya's backend, Bhagya's scientific rules, Matheesha's adapters, Akash's model.

Legend: ✅ done · 🟡 done in the frontend, waiting on a teammate's service or review · 🔒 blocked by a dependency (shown as a planned feature in the app)

## Core

| # | Task (plan) | Status | Notes |
| --- | --- | --- | --- |
| 1 | Core interface: app shell, farm map/forms, observation dashboard, rotation timeline/comparison, scenario controls, assistant panel, saved-plan view | ✅ | Tharuka's design adopted: sidebar, top bar, step tracker, light/dark themes (AA contrast verified on 6 pages in both themes) |
| 2 | Shared API client and result state: typed calls, loading/error/retry, farm/analysis selection, stale-response guards | ✅ | Farms and observations verified against the live backend; rotations/scenarios/assistant/plans wait for endpoints |
| 3 | Validate and preserve inputs; recoverable drafts with clear control | ✅ | Irrigation has three explicit choices: amount, rainfed (0), unknown (null) |
| 4 | Crop catalog loading + validation | ✅ | Eight project-owner demo-reviewed screening crops; FAO proxy limitations remain explicit |
| 5 | Financial calculator | ✅ | Spec v0.1 approved (Bhagya); real local inputs pending (Tharuka) |
| 6 | Make results understandable: sources, missing data, uncertainty, baseline vs scenario, outdated indicators; assistant tied to the analysis | ✅ | rotation-score-0.1 components and weights, per-season water (baseline → scenario), unknown-irrigation notice, assistant status/assumptions/source links |
| 7 | Verify the complete journey: phone layouts, keyboard, save/reload, scenario updates, failures, plan reopening; language switching | ✅ | 11 pages pass at 375 px with labelled inputs; focus moves to content on navigation; Sinhala/Tamil strings need fluent review |
| — | Source and assumption displays · analysis freshness · accessibility/mobile QA · workflow verification (expanded table) | ✅ | Joint visual review with Tharuka still recommended |

## Follow-on (plan step 8 and "Next" rows)

| Task | Status | Notes |
| --- | --- | --- |
| Language switching infrastructure | 🟡 | All UI text in locale files with English fallback; translations need fluent reviewers |
| Print/report presentation | 🟡 | Print view done; connect to the report/export endpoint when Dulanjaya publishes it |
| Action calendar | 🟡 | Farmer-entered dates per season, validation, chronological view, `.ics` download; stored on device until calendar records exist; reminder delivery not chosen |
| Offline viewing and status | ✅ | Offline banner; saved plans cached on device and reopened with their copy date; production service worker for the app shell; server writes blocked offline in live mode |
| Offline editing / sync | 🔒 | Needs Dulanjaya's sync and conflict policy |
| Season feedback / review forms | 🔒 | Needs outcome fields and storage (backend) |
| Voice controls | 🔒 | Needs Akash's voice service and a working multilingual text flow |
| WeedShield upload | 🔒 | Needs a validated model |
| Demo readiness | ✅ | `frontend/QA_CHECKLIST.md`; fixtures labelled; planned features listed on the Roadmap page |

## Verification

- Frontend: `npm run typecheck`, `npm run lint`, `npm test` (91 tests), `npm run build`.
- Repository: `python scripts/validate_data.py`, shared `pytest tests`, backend tests (on Windows use `--allow-hosts=127.0.0.1` instead of CI's socket flags).
- Not yet verified: loading the production build fully offline through the service worker, and a joint accessibility review with Tharuka.

## Open dependencies

- **Dulanjaya:** rotation, scenario, assistant and plan endpoints; report/export and calendar records; sync policy; server-side `irrigation_basis: "field_applied_depth"` when irrigation is known.
- **Bhagya:** crop approvals; soil/recovery rules.
- **Akash:** HTTP route (with Dulanjaya); Sinhala/Tamil answers; voice.
- **Tharuka:** review the adopted design in `frontend/src`; sourced finance inputs; fluent reviewers; usability session.
