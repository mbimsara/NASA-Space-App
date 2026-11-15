# Architecture — proposed v0.1

Status: FastAPI farm/observation persistence, rotation analyses, climate scenarios, the deterministic assistant and saved plans are implemented on canonical SQLite snapshot tables. Provider/scientific modules remain owned by their leads. See [backend setup](../backend/README.md) and [canonical integration details](ASSISTANT_SAVED_PLANS_INTEGRATION.md).

```mermaid
flowchart TD
    UI[React frontend — Shehani / design by Tharuka] --> API[FastAPI — Dulanjaya]
    API --> DB[(Farm inputs, analysis snapshots, saved plans)]
    API --> EO[NASA adapters and climate summaries — Matheesha]
    EO --> NASA[Verified NASA data sources]
    API --> ROT[Rotation and water engine — Bhagya]
    EO --> ROT
    CAT[Reviewed regional crop catalog — Tharuka + Bhagya] --> ROT
    API --> FIN[Financial calculator — Shehani / reviewed by Bhagya]
    API --> AI[Grounded assistant — Akash]
    DB --> AI
```

## Core flow

1. Save a farm and increment its input version on changes.
2. Retrieve observations, preserving source dates, resolution, units, and missing values.
3. Analyze an explicit farm snapshot against an approved crop catalog and model version.
4. Run a hypothetical scenario from an immutable baseline analysis. A scenario changes specified inputs, not historical observations.
5. Save a selected candidate with its analysis and source references.
6. Resolve assistant context on the server using the selected IDs. Explain only the available structured results.

## Boundaries

- API prefix: `/api/v1`. Domain functions do not depend on frontend state.
- Provider credentials stay server-side. Farm updates use input versions to prevent overwriting newer edits.
- Historical observations, synthetic fixtures, modeled estimates, and hypothetical scenarios remain distinguishable in storage and UI.
- Cache provider responses with retrieval time and coverage. A provider failure produces a clear unavailable response or dated cache result.
- Financial ranges depend on sourced user/local inputs. Climate similarity does not establish agronomic equivalence.
- Weed, voice, notifications, offline writes, and climate twins are follow-on integrations. Final service/library choices need verification during implementation.

## Decisions still needed

Record decisions and reasons here as they are made: production database/deployment target (SQLite is the current local default); production runtime versions; production observation retention and background refresh policy (POWER snapshots currently use a configurable 24-hour fresh-cache lifetime); map tiles and license; crop region/season definitions; reviewed scoring rules; AI provider/model; authentication before accepting real farmer data; offline conflict policy; team-approved license.

## Implemented observation boundary

`GET /api/v1/farms/{farm_id}/observations` reads farm coordinates and input version from
SQLite, validates historical dates, and calls the dependency-injected `ObservationAdapter`.
The default adapter reuses Matheesha's `backend/services/nasa_power.py`. POWER
observations are the persisted rotation baseline. SMAP, GPM IMERG, and HLS are
exposed through separate farm-scoped context APIs with explicit availability
and distance policies; they are never silently substituted into that baseline.
The HTTP layer preserves normalized results and adds farm/observation IDs, version,
units, coverage disclosure and contract aliases. Missing or unusable services produce 503.
POWER results remain modeled estimates, with missing values preserved.

`observation_snapshots` stores immutable response JSON, the complete original farm profile,
its input version, cache-key generations and separate cache creation/expiry timestamps.
Startup adds this table without modifying the existing farm table. The cache key covers farm,
version, coordinates, period and versioned provider settings. Fresh requests reuse stable IDs;
expiry or version changes append snapshots. Unique key/generation constraints resolve concurrent
writers to one committed ID. Network calls run outside the database read transaction.
Old snapshots remain readable at `/api/v1/observations/{observation_id}`. Failed refreshes return
503 rather than silently using expired or synthetic values. Cache expiry and farm-version
staleness are separate: the future-analysis reference helper permits historical IDs for matching
current inputs but rejects ownership/version conflicts. Future analysis saves must recheck
input versions when committing. No crop calculations are added in the observation boundary. See [backend details](../backend/README.md#climate-observations).

## Canonical analysis and selection boundaries

`rotation_analysis_snapshots`, `rotation_scenario_snapshots` and
`saved_plan_snapshots` remain the sole analytical/plan tables. Rotation insertion
and plan saving atomically guard the farm version through a conditional no-op
UPDATE and commit. Calculation code, scenario comparison fields and producer
snapshots are retained unchanged; no legacy tables or duplicate engine package
are introduced.

The assistant/plan resolver checks canonical snapshot identities and relationships.
Plan reads validate only their embedded historical snapshots. The original full
analysis request/catalog bundle was not persisted by main and is not fabricated
from current inputs. The assistant HTTP bridge adds selected-context warnings
without altering explanation or evidence-selection functions. See
[selective old-branch review and compatibility evidence](DULANJAYA_BACKEND_REVIEW.md).
