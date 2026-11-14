# AgroSphere AI — Six-member implementation plan

This is a proposed allocation based on the six verified GitHub members, not an assessment of individual skills. Tharuka owns UI/UX design as requested. The timeline assumes a 48-hour hackathon; follow the milestone order if the event duration differs.

## Ownership and deliverables

| Member | Primary responsibility | Core deliverables | Follow-on features |
| --- | --- | --- | --- |
| **Dulanjaya Herath — @DulanjayaHerath** | Backend, shared data, integration, and deployment | API contracts; farm/history/soil/priority persistence; input validation; integrate services; deploy and maintain the working demo | Season feedback persistence, report export, calendar/reminder backend |
| **Tharuka — @tharuka058** | **UI/UX design and design QA** | Figma flow, wireframes, component styles, desktop/mobile screens, clickable prototype, handoff notes, accessibility and final visual review | Designs for all advanced modules, offline and voice states, presentation visuals |
| **Shehani Weerasekara — @shehani419** | Frontend implementation | Build Tharuka's designs; farm onboarding and map; dashboard; rotation comparison; scenario controls; assistant interface | Offline notebook, action calendar, review forms, report UI, voice controls |
| **Matheesha Bimsara — @mbimsara** | NASA data and climate analysis | First verified NASA observation integration; cache; units and provenance; historical indicators; reduced-rainfall scenario inputs | GPM/SMAP/HLS adapters where feasible; historical climate twin comparison |
| **Bhagya Karunanayake — @zerokali20** | Crop rotation and agronomy engine | Researched regional crop catalog; candidate sequences; constraint checks; explainable ranking; water-budget estimates | SoilRevive, FarmRecovery, cover crops, financial scenario ranges |
| **Akash Neelawathura — @iamneelz11** | AI assistant, evaluation, and image analysis | Assistant grounded in computed results; missing-data handling; English/Sinhala/Tamil checks; evaluation questions and demo explanations | WeedShield model feasibility/validation, then voice-service integration |

Each person implements and verifies their own work. Dulanjaya coordinates integration; testing and presentation are shared responsibilities. Advanced work starts only after the connected core passes its acceptance checks.

## Tharuka's UI design assignment

Deliver a Figma file with reusable typography, colors, spacing, buttons, form fields, cards, chart styles, status badges, and navigation. Provide desktop and mobile layouts plus a clickable core journey.

Design these screens in order:

1. **Farm setup:** map location, area and units, current and previous crops, irrigation, soil test entries, priorities, and constraints. Allow unknown soil values.
2. **Farm overview:** observation charts, date range, source/resolution labels, missing-data states, and a clear next step to compare rotations.
3. **Rotation workspace:** three candidate plans, seasonal crop timeline, water demand, soil indicators, risk, ranking explanation, and selection control.
4. **Scenario comparison:** rainfall adjustment, baseline versus scenario results, changed assumptions, and hypothetical-scenario labels.
5. **Assistant:** farm/plan context, suggested questions, explanations with source references, loading/error states, and language selection.
6. **Saved plan:** chosen rotation, action calendar, share/export preview, and later season feedback.

Then design WeedShield upload/results, climate twins, financial scenarios, offline status, and voice interaction. Keep these visibly identified as planned capabilities until implemented.

Handoff checklist: component states, responsive behavior, labels and units, empty/loading/error states, keyboard focus, readable contrast, and source/assumption placement. Tharuka and Shehani review each core screen together before implementation; Shehani can start the app shell from the initial component set without waiting for all screens.

## Suggested technical boundaries

- Frontend: React with TypeScript; map and chart libraries selected during setup.
- Backend: FastAPI with typed request/response models and a database for farm records and saved analyses.
- Computation: explicit Python functions for rotation scoring, water budgets, and scenarios; version their assumptions.
- Assistant: server-side model access using structured analysis context. Keep provider credentials on the server.
- Data: implement one NASA source end to end first; add other products after checking access, spatial resolution, temporal coverage, and usefulness.

These are proposed implementation choices, not installed dependencies or verified service integrations.

## Shared contracts — agree before module development

Dulanjaya publishes the schemas and one example response per endpoint. Everyone develops against the same fixtures until live integrations are available.

| Object | Required information |
| --- | --- |
| Farm profile | ID, location, area/unit, irrigation supply/unit, crop history with dates, soil tests with units/dates, priorities, constraints |
| Observation summary | Farm ID, time range, variables/units, source, observation dates, spatial resolution, coverage/missing values, retrieval date |
| Rotation analysis | Analysis ID, farm input version, crop catalog/model version, candidate crop sequences, score breakdown, water estimates, reasons, assumptions, sources |
| Scenario result | Baseline analysis ID, changed inputs, scenario parameters, recalculated metrics, differences, limitations |
| Assistant context | Farm and analysis IDs, selected plan, relevant structured results, source references, user question/language |

Proposed API surface:

- `POST /farms`, `GET /farms/{id}`, `PATCH /farms/{id}`
- `GET /farms/{id}/observations?start=...&end=...`
- `POST /farms/{id}/rotations`
- `POST /analyses/{id}/scenarios`
- `POST /assistant/messages`
- `POST /farms/{id}/plans`, `GET /plans/{id}`

Changing farm inputs marks older analyses as outdated. Saving a plan stores its input snapshot, sources, and model version. All modules use the same farm ID and analysis ID; the assistant consumes computed results rather than independently inventing scores.

## Milestones for a 48-hour build

| Time | Team objective | Required handoff |
| --- | --- | --- |
| Hours 0–4 | Freeze core journey, crop region/catalog scope, schemas, sample farm, and demo criteria | Tharuka: flow/components; Dulanjaya: API examples; Matheesha: data-access feasibility; Bhagya: crop rules; Akash: answer format; Shehani: app shell |
| Hours 4–12 | Build independently against shared fixtures | Farm save/read, first observation adapter, first rotation result, clickable core design, frontend screens, assistant over fixture results |
| Hours 12–24 | Integrate the first complete journey | Saved farm → real observations → rotation comparison → assistant explanation; resolve contract mismatches immediately |
| Hours 24–34 | Add scenario comparison and water budget; persist selected plan | Changing rainfall produces a recalculated comparison and the assistant explains that exact result |
| Hours 34–42 | Add only ready follow-on features; verify mobile and failure behavior | Prefer soil/recovery modes, report, and calendar before opening advanced model work |
| Hours 42–48 | Freeze features, fix defects, rehearse, and submit | Deployed demo, labeled fallback data, source list, limitations, screenshots/video, and final pitch |

## Acceptance checks

1. A farmer can save and reload a farm without losing history, units, soil inputs, or priorities.
2. At least one NASA dataset is actually retrieved for the demonstration location and displayed with provenance and coverage. Unavailable observations produce an honest missing-data state.
3. Three feasible, distinct rotation candidates are returned when the catalog and constraints permit. If fewer are feasible, explain why instead of manufacturing alternatives.
4. Crop exclusions, repeat-crop rules, seasonal suitability, and water constraints affect candidate eligibility or ranking through documented rules. Scores expose their components.
5. A reduced-rainfall scenario recomputes the water budget and affected rankings from the same baseline. Its assumptions and differences are visible.
6. The assistant's numbers match the selected analysis, identifies missing data, and provides understandable explanations in each supported language after review.
7. The selected plan can be saved and reopened. Core screens work on a phone and have usable loading, error, and empty states.
8. Cached real observations retain their original timestamps. Synthetic fixtures and unimplemented features are explicitly labeled in demos.

Bhagya and Matheesha cross-check units and scenario math. Akash checks explanations against API results. Tharuka and Shehani check the complete UI journey. Dulanjaya verifies persistence, deployment, and integration failures.

## Follow-on feature dependencies

| Feature | Owners | Start condition |
| --- | --- | --- |
| SoilRevive / FarmRecovery / cover crops | Bhagya; Tharuka and Shehani for UI | Rotation engine and regional agronomy rules working |
| Cost and income scenarios | Bhagya; Dulanjaya for storage | Sourced local inputs, units, dates, and uncertainty ranges available |
| Action calendar and reminders | Shehani and Dulanjaya | Selected plan and planting dates saved; choose reminder delivery separately |
| Offline notebook | Shehani; Dulanjaya for sync contract | Persistence works; define cached data, stale indicators, and edit-conflict behavior |
| Season review | Dulanjaya and Shehani | Saved plan versions and actual outcome fields defined |
| Shareable report | Dulanjaya and Shehani; Tharuka designs | Stable analysis with sources and assumptions |
| Global climate twins | Matheesha; Bhagya reviews interpretation | Comparable historical climate features and candidate regions available |
| WeedShield | Akash; Shehani builds upload UI | Suitable model/data identified and tested; uncertainty and unsupported inputs handled |
| Voice input and read-aloud | Akash and Shehani; Tharuka designs | Language text flow works; browser/service support and fallback verified |

## Collaboration and delivery

- Use small branches such as `codex/farm-api`, `codex/ui-shell`, or `codex/rotation-engine`, with pull requests linked to a feature and acceptance check.
- Agree on schemas first; communicate contract changes before merging them. Integrate at least every four hours after the first build period.
- Each PR includes what changed, how it was checked, assumptions, and a screenshot for visible UI changes.
- Keep a working demo on the shared branch. Avoid committing credentials or private farm data; use a consented or synthetic demonstration farm profile.
- At feature freeze, defer incomplete advanced modules and present them as roadmap items. All 20 capabilities remain in the product scope.

## Pitch ownership

- Dulanjaya: problem, architecture, and live flow coordination.
- Tharuka: farmer journey, interface, and visual storytelling.
- Shehani: live farm-to-plan walkthrough.
- Matheesha: NASA sources and their practical limits.
- Bhagya: rotation logic and agronomic tradeoffs.
- Akash: assistant explanation, evaluation, and next steps.

Adjust speaking time to the actual submission format. Everyone rehearses the same story: one farm, one decision, traceable evidence.
