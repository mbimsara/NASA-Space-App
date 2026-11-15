# AgroSphere non-deployment completion audit

Audit date: 2026-11-15. Verified feature commit: `ee4e89a` on `origin/main`.

| Requirement | Authoritative implementation evidence | Verification |
| --- | --- | --- |
| NASA POWER | Provider adapter, persisted observation snapshots, observations and season-input APIs/UI | Normalization, cache, missing-data, season-input, HTTP and browser tests pass |
| SMAP | SPL3SMP_E V006 authenticated subset pipeline, quality filtering, distance gate, `/soil-moisture`, observations/soil UI | Complete 31-file January 2025 local job recorded; unit and integration tests pass |
| GPM IMERG | GPM_3IMERGDF V07 workflow, normalizer, distance gate, `/gpm-precipitation`, observations UI | Provenance, missing-value, route and location-gate tests pass |
| HLS | HLSL30/HLSS30 V2.0 workflow, cloud/quality filtering, NDVI, distance gate, `/hls-vegetation`, observations/soil/WeedShield UI | Normalizer, rejection, route and location-gate tests pass |
| Farm and observations | Versioned farm CRUD, immutable observation snapshots, coverage/source/limitation display | FastAPI integration and browser tests pass |
| Rotation and recovery | Crop rotation, season water ranges, SoilRevive, drought recovery, flood recovery, sourced planning evidence | Engine, API, mode-ordering, scenario and UI tests pass |
| Climate scenarios and twins | Immutable hypothetical rainfall scenarios; same-period registered-farm POWER comparison | Recalculation, baseline-preservation, sensitivity, API and UI tests pass |
| Assistant | `POST /assistant/messages`, context ownership, sources/assumptions/limitations, optional non-persistent LLM wording, deterministic fallback | Contract, grounding, stale-context and browser tests pass; unsupported Sinhala/Tamil safely return 422 |
| Saved plans/reports/calendar/offline | Immutable snapshots, list/get APIs, JSON/print export, ICS, reminders, offline viewing and version-safe queued edits | Plan, cache, conflict, calendar, reminder and browser tests pass |
| WeedShield | On-device disclosed green-pixel vegetation triage, separate HLS context, farmer confirmation | Pixel tests, production build and live page assertions pass |
| Financial scenarios and feedback | Deterministic sourced range calculator; append-only season feedback | Calculator, validation and feedback API tests pass |
| Honest data boundaries | Synthetic labels, null missing values, source/date/unit/coverage, no silent fallback or unsupported field inference | Provider-failure tests, source-policy scans and UI copy reviewed |
| Source restriction | NASA/FAO/Sri Lanka DOA sources only for implemented paths; no China-related dataset, location or example | Repository scan and planning-evidence test pass |

## Verification gates

- Complete root and backend Python suite: passed.
- Frontend Vitest: 19 files, 120 tests passed.
- Frontend TypeScript production build and lint: passed.
- Live FastAPI + React Playwright suite: 4 applicable tests passed; 3
  environment-specific variants skipped by explicit flags.
- Git diff check: passed; remote `origin/main` resolved to `ee4e89a` after push.

## Scientific boundary

WeedShield reports vegetation-like pixels, not weed coverage or species. The
competition resources do not include a validated Sri Lankan field-photo weed
dataset, so AgroSphere does not fabricate a classifier or herbicide advice.
Likewise, SMAP and HLS remain contextual satellite layers rather than field
nutrient, root-zone-water, or soil-health measurements.
