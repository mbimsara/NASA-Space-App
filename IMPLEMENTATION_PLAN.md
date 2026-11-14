# AgroSphere AI — Six-member implementation plan

This is a proposed allocation based on the six verified GitHub members, not an assessment of individual skills. Tharuka owns UI/UX design as requested. The timeline assumes a 48-hour hackathon; follow the milestone order if the event duration differs.

## Ownership and deliverables

### Workload sharing update

The assignments below refine the original ownership table: module leads retain their core engines, while Tharuka and Shehani own the supporting deliverables listed here. These assignments take precedence where later tables mention only the lead.

| Workstream | Lead retains | Tharuka owns | Shehani owns |
| --- | --- | --- | --- |
| Crop rotation and agronomy | Bhagya: candidate generation, constraints, scoring, water-budget math, and final rule review | Research and maintain the initial regional crop catalog with references, units, seasonal suitability, and unresolved questions; prepare sourced soil/recovery/cover-crop rule drafts for Bhagya to approve | Crop catalog loading and schema validation utilities; rotation comparison, farmer-priority controls, and soil/recovery mode interfaces |
| Financial scenarios | Bhagya: approve assumptions and calculation specification | Research a small set of dated local cost/price inputs and define understandable uncertainty labels | Implement the specified deterministic cost/revenue range calculator with focused calculation checks; display assumptions and ranges. Bhagya reviews results before integration |
| NASA observations and climate | Matheesha: access adapters, geospatial/time processing, climate indicators, and twin matching | Maintain dataset/source inventory and source-explanation text from Matheesha's verified metadata; check demo charts for clear units, dates, and resolution | Reusable observation charts, missing-data displays, and baseline/scenario comparison UI using Matheesha's output contracts |
| Assistant and evaluation | Akash: model integration, grounding, image-model validation, and voice service | Prepare realistic farmer questions and expected facts from approved fixture results; coordinate fluent Sinhala/Tamil review rather than assuming translation accuracy | Language-switching infrastructure, assistant context selection, and citation/result navigation |
| Demo and quality | Dulanjaya: integration/deployment; each lead: scientific or technical correctness | Own usability sessions, issue triage, source/assumption documentation, demo script, and presentation assets | Own core frontend regression checks and resolve client-side issues with the relevant lead |

Tharuka keeps UI/UX design ownership. Complete the core Figma journey first, then the crop catalog and validation material; advanced-screen design is deferred. Research drafts require the relevant module lead's approval before they influence recommendations.

Shehani already has substantial frontend work. Her new implementation ownership is limited to catalog validation and a small specified financial calculator; charts and language controls remain part of her existing frontend scope. Defer offline editing/synchronization, voice controls, and advanced upload screens until the core journey passes. Offline viewing of saved results can precede offline editing.

For the first milestone, Tharuka hands Bhagya a referenced crop-catalog draft, Shehani provides its validated loading path, and Bhagya concentrates on the rotation engine. Matheesha supplies one verified observation response while Tharuka documents its meaning and Shehani renders it. No one independently changes scientific rules without the lead's review.

| Member | Primary responsibility | Core deliverables | Follow-on features |
| --- | --- | --- | --- |
| **Dulanjaya Herath — @DulanjayaHerath** | Backend, shared data, integration, and deployment | API contracts; farm/history/soil/priority persistence; input validation; integrate services; deploy and maintain the working demo | Season feedback persistence, report export, calendar/reminder backend |
| **Tharuka — @tharuka058** | **UI/UX design and design QA** | Figma flow, wireframes, component styles, desktop/mobile screens, clickable prototype, handoff notes, accessibility and final visual review | Designs for all advanced modules, offline and voice states, presentation visuals |
| **Shehani Weerasekara — @shehani419** | Frontend implementation, client integration, and workflow QA | Build Tharuka's designs; farm onboarding and map; dashboard; rotation comparison; scenario controls; assistant interface; shared API client; form validation; accessibility and workflow checks | Offline notebook, action calendar, review forms, report UI, language switching, voice controls |
| **Matheesha Bimsara — @mbimsara** | NASA data and climate analysis | First verified NASA observation integration; cache; units and provenance; historical indicators; reduced-rainfall scenario inputs | GPM/SMAP/HLS adapters where feasible; historical climate twin comparison |
| **Bhagya Karunanayake — @zerokali20** | Crop rotation and agronomy engine | Researched regional crop catalog; candidate sequences; constraint checks; explainable ranking; water-budget estimates | SoilRevive, FarmRecovery, cover crops, financial scenario ranges |
| **Akash Neelawathura — @iamneelz11** | AI assistant, evaluation, and image analysis | Assistant grounded in computed results; missing-data handling; English/Sinhala/Tamil checks; evaluation questions and demo explanations | WeedShield model feasibility/validation, then voice-service integration |

Each person implements and verifies their own work. Dulanjaya coordinates integration; testing and presentation are shared responsibilities. Advanced work starts only after the connected core passes its acceptance checks.

## Detailed tasks for each member

These sections are the consolidated assignments, including the workload-sharing update. A lead owns the correctness of their module; supporting contributors deliver the specific pieces listed below.

### Matheesha — NASA data and climate intelligence

**Goal:** provide traceable environmental information that the rotation engine can actually use.

1. **Verify data access:** evaluate the proposed NASA products for the demo location, variables, dates, resolution, and access requirements. Select one useful source for the first working integration; record why it fits and what it cannot measure.
2. **Build the observation adapter:** retrieve observations using farm coordinates and a requested date range. Normalize dates and units, preserve missing values, and return the shared observation schema rather than raw provider responses.
3. **Prepare historical summaries:** calculate documented seasonal rainfall and temperature summaries and, where the data supports them, historical dry/heat/excess-rain indicators. Distinguish historical indicators from forecasts.
4. **Support climate scenarios:** supply baseline climate inputs and explicit rainfall-change parameters. Work with Bhagya so a hypothetical rainfall reduction changes the same water-budget calculation used by the rotation engine.
5. **Handle reliability:** cache responses with retrieval/observation dates; handle unavailable locations, partial coverage, and provider failures without silently fabricating values.
6. **Build climate twins later:** define comparable historical climate features, candidate regions, and a similarity method. Explain that climate similarity alone does not establish crop or soil suitability.

**Deliverables:** observation adapter, normalized example response, baseline summaries, scenario input specification, source metadata, and later a climate-twin result with its method documented.

**Handoffs:** Dulanjaya exposes the adapter through the API; Bhagya consumes its climate inputs; Shehani renders charts; Tharuka turns verified metadata into readable source explanations.

**Done when:** the demonstration farm retrieves a real, dated observation result; its units and source are visible; missing-data behavior works; and Bhagya can consume the response without manual conversion.

### Bhagya — crop rotation and agronomy engine

**Goal:** generate useful crop sequences and explain their tradeoffs through transparent rules.

1. **Approve the regional crop catalog:** review Tharuka's sourced research for season suitability, crop families, water requirements, soil constraints, and limitations. Keep unknown values explicit and restrict the demo to crops with adequate supporting information.
2. **Generate candidate rotations:** construct three-to-five-season sequences from the approved catalog. Apply farmer exclusions, season constraints, crop history, and documented repeat-crop rules before ranking candidates.
3. **Implement explainable ranking:** define score components and priority weights. Return reasons, tradeoffs, rejected constraints, and assumptions alongside scores; avoid presenting heuristic scores as validated yield predictions.
4. **Calculate the water budget:** agree with Matheesha on units, period, rainfall assumptions, irrigation supply, and crop demand. Recompute affected metrics under scenario inputs and check representative calculations.
5. **Add soil and recovery modes:** review Tharuka's proposed rules for legumes, cover, diversity, and recovery after drought/flood. Implement supported rules as inputs to the existing rotation comparison, with missing soil/drainage information disclosed.
6. **Specify financial scenarios:** define cost categories, area conversions, price/yield range inputs, and calculation assumptions. Shehani implements the agreed calculator; Bhagya reviews its outputs and uncertainty wording before use.

**Deliverables:** approved crop catalog, candidate generator, scoring specification and engine, water-budget functions, scenario recalculation, soil/recovery rules, and reviewed financial calculation examples.

**Handoffs:** Tharuka supplies research drafts; Matheesha supplies observations; Shehani supplies catalog validation and financial calculation code; Dulanjaya stores/serves analyses; Akash explains the returned results.

**Done when:** feasible sequences respect documented constraints, rankings expose their reasons, water calculations use consistent units, and scenario changes produce reproducible differences. If fewer than three plans are feasible, return the actual count and explain why.

### Tharuka — UI/UX, research support, and usability

**Goal:** make the farmer journey understandable while taking research and communication work off the module leads.

1. **Design the core journey:** create the Figma flow and reusable components for farm setup, observations, rotation comparison, climate scenarios, assistant, and saved plan. Include mobile layouts and loading, error, empty, and unknown-value states.
2. **Hand designs to Shehani incrementally:** specify labels, units, interaction states, responsive behavior, and keyboard focus. Review implemented screens together; deliver the first components early so coding can start.
3. **Research the initial crop catalog:** compile a small regional catalog with source links, geographic applicability, units, seasonal information, and unresolved questions. Submit it to Bhagya for approval; do not turn unreviewed claims into production rules.
4. **Prepare supporting agronomy and price research:** draft referenced soil/recovery/cover-crop guidance and a limited set of dated local financial inputs. Clearly separate evidence, assumptions, and missing information for Bhagya's review.
5. **Maintain source explanations:** use Matheesha's verified metadata to explain dataset dates, resolution, coverage, and limitations in plain language. Maintain the source/assumption documentation used in the report and pitch.
6. **Own usability and demo preparation:** run short task-based reviews, record confusing steps, prioritize findings, prepare farmer evaluation questions from approved results, and coordinate language review with fluent speakers. Produce the demo script and presentation visuals.

**Deliverables:** core Figma prototype and component handoff, reviewed research tables, source explanations, usability issue list, evaluation questions with expected facts, and demo/presentation assets.

**Handoffs:** Shehani implements the designs; Bhagya approves crop/agronomy/price research; Matheesha approves NASA explanations; Akash uses evaluation questions to check grounded answers.

**Done when:** the core design supports the complete farmer journey, every research entry is traceable or marked unresolved, module leads have reviewed content used by calculations, and major usability issues are resolved or recorded.

**Order:** core design first, crop-catalog research second, validation and demo material next. Advanced-screen design waits until the core is usable.

### Shehani — frontend, client integration, and supporting calculations

**Goal:** turn the designs and module outputs into one reliable farmer-facing application.

1. **Implement the core interface:** build the app shell, farm map/forms, observation dashboard, rotation timeline/comparison, scenario controls, assistant panel, and saved-plan view from Tharuka's designs.
2. **Connect the shared APIs:** implement typed client calls, loading/error/retry states, and farm/analysis selection. Guard against old requests replacing newer results after a farm or scenario change.
3. **Validate and preserve inputs:** validate dates, required fields, positive area, and explicit units while allowing unknown soil values. Add recoverable local drafts and a clear-draft control; coordinate server validation with Dulanjaya.
4. **Validate crop catalog loading:** implement schema checks for the approved catalog so missing identifiers, invalid units, or malformed records are surfaced before the engine consumes them. Bhagya owns the scientific meaning of catalog entries.
5. **Implement the financial calculator:** follow Bhagya's approved formulas and range assumptions, accept explicit local inputs, and add focused checks for conversions and calculation examples. Show dated sources and assumptions with the results.
6. **Make results understandable:** render source metadata, missing observations, uncertainty, baseline/scenario differences, and outdated-analysis indicators. Keep the assistant tied to the currently selected analysis.
7. **Verify the complete journey:** check phone layouts, keyboard access, farm save/reload, scenario updates, request failures, and plan reopening. Implement language switching without losing farm state; ask fluent reviewers to validate translations.
8. **Add follow-on interfaces after core completion:** report/print view, action calendar, season feedback, offline viewing, then offline editing under an agreed sync policy. Voice and weed-upload controls come after their services are ready.

**Deliverables:** connected responsive frontend, shared API client, validated forms/drafts, catalog validation utility, reviewed financial calculator, source/result components, and a repeatable workflow QA checklist.

**Handoffs:** Tharuka supplies designs and reviewed content; Dulanjaya supplies APIs and sync contracts; Matheesha supplies observations; Bhagya approves calculator behavior; Akash supplies assistant/voice/image services.

**Done when:** a farmer can complete the core journey without manual intervention, failed requests have useful recovery states, farm changes cannot display another farm's results, and saved plans reopen correctly.

**Order:** core screens and integration first. Financial calculations and language switching follow a working rotation flow. Offline editing, voice controls, and advanced upload screens remain deferred to protect workload.

### Dulanjaya — backend, persistence, and integration

**Goal:** provide the shared application foundation and keep all modules operating on consistent data.

1. **Define contracts and fixtures:** publish typed request/response schemas, error formats, units, and example responses. Coordinate schema changes before other modules adopt them.
2. **Implement farm persistence:** store location, area, crop history, soil tests, priorities, and constraints; validate inputs and support create/read/update operations.
3. **Wire analytical services:** expose Matheesha's observations and Bhagya's rotation/scenario functions through stable endpoints. Pass structured context to Akash's assistant and keep provider credentials server-side.
4. **Version saved results:** persist input snapshots, analysis/model/catalog versions, sources, selected plans, and scenario parameters. Detect outdated analyses when farm inputs change.
5. **Implement supporting persistence:** add season outcome records, report/export endpoints, and action-calendar records once core plans work. Define reminder delivery before building external notifications.
6. **Prepare deployment and reliability:** configure environment variables, database setup, health checks, useful error logging, and reproducible startup instructions. Verify the deployed frontend can reach the backend and demonstrate provider failure behavior.
7. **Define offline synchronization later:** agree with Shehani on cached data, pending edits, server versions, and conflict resolution before allowing offline writes.

**Deliverables:** API schemas and fixtures, database models, working endpoints, analysis/plan versioning, integrated deployment, configuration documentation, and later report/calendar/feedback support.

**Handoffs:** all members develop against the published contracts; Shehani integrates endpoints; analytical leads approve the meaning of data passed through the backend.

**Done when:** farm and plan data survive reload/restart, services share the correct IDs and input versions, invalid requests return clear errors, credentials stay out of the client/repository, and the deployed core flow works.

### Akash — grounded assistant, evaluation, and advanced AI

**Goal:** explain actual application results accurately and add advanced AI capabilities only when they can be evaluated.

1. **Build the assistant integration:** consume the selected farm, analysis, plan, scenario, and source references. Use the computed results as the basis of explanations rather than generating independent rotation scores or environmental measurements.
2. **Handle uncertainty and missing inputs:** distinguish observations from modeled estimates and hypothetical scenarios. Explain when the supplied context cannot answer a question or when an agronomy input is missing.
3. **Support multilingual explanations:** implement English/Sinhala/Tamil response selection; coordinate with Shehani's interface and fluent reviewers. Preserve numbers, units, crop names, and source meaning across languages.
4. **Evaluate grounded answers:** use Tharuka's farmer questions and approved fixture results to check numeric consistency, references, missing-data behavior, and baseline/scenario distinctions. Record failures and fix prompts/context handling.
5. **Investigate WeedShield after core:** assess available models and suitable test data, clarify whether the model identifies species or estimates coverage, and evaluate its performance and unsupported conditions. If validation is insufficient, present it as a prototype or roadmap feature.
6. **Add voice after text works:** integrate supported speech input/read-aloud with Shehani, verify languages and browser behavior, and provide a text fallback.

**Deliverables:** server-side assistant service, structured context format, multilingual answer examples, evaluation cases/results, and later an honestly evaluated weed prototype and voice integration.

**Handoffs:** Dulanjaya integrates the service; Shehani builds the interface; Tharuka supplies test questions and coordinates usability/language review; Matheesha and Bhagya resolve domain-specific answer issues.

**Done when:** assistant numbers match the selected analysis, unsupported questions do not produce invented results, source references are usable, and reviewed language outputs preserve the meaning of the underlying data.

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

## Shehani's expanded implementation tasks

Complete the core screens first. The following tasks extend frontend ownership; they do not require Shehani to take over Tharuka's design work or the backend and scientific models.

| Task | Deliverable and completion check | Partner | Order |
| --- | --- | --- | --- |
| Shared API client and result state | Typed requests, consistent error handling, retry controls, and request cancellation or stale-response guards. Switching farms must never show another farm's results. | Dulanjaya | Core |
| Farm form validation and draft recovery | Validate required fields, date order, positive area, and explicit units; preserve unknown soil values. Recover an unfinished draft on the same browser and allow clearing it. | Dulanjaya and Bhagya | Core |
| Source and assumption displays | Reusable components for dataset dates, resolution, units, missing observations, modeled estimates, and hypothetical scenarios. | Matheesha and Bhagya | Core |
| Analysis freshness and scenario state | Mark old analyses as outdated after input edits; keep baseline and scenario clearly identified; prevent saving an older result as the current selection accidentally. | Dulanjaya | Core |
| Accessibility and mobile QA | Verify keyboard navigation, focus after dialogs/errors, field labels, readable charts, and layouts on narrow screens. Record and fix issues with Tharuka. | Tharuka | Core |
| Complete workflow verification | Check farm save/reload, comparison, scenario recalculation, assistant context, and plan reopening. Include unavailable-data and failed-request cases; add focused automated checks for stale responses and persistence regressions where practical. | All module owners | Core |
| Language switching infrastructure | Externalize interface text; implement English/Sinhala/Tamil switching and English fallback for missing translations. Preserve the selected farm and analysis when switching. | Akash; fluent reviewers verify translations | Next |
| Print and report presentation | Build a print-friendly plan view with crop timeline, inputs, sources, assumptions, and analysis date; connect it to the report/export endpoint when ready. | Tharuka and Dulanjaya | Next |
| Offline and synchronization status | Show cached-data dates, offline availability, pending edits, and sync failures. Implement the agreed conflict policy before allowing offline edits to overwrite server records. | Dulanjaya | Next |
| Demo readiness | Maintain a repeatable frontend demo checklist and capture the completed journey for the submission. Clearly label fixtures and roadmap screens. | Tharuka and the team | Feature freeze |

Shehani's first handoff is the app shell plus the shared API client and validated farm form. After the core journey works, prioritize language switching, reports, and offline behavior in that order. If time is tight, defer follow-on tasks rather than weakening the core workflow.

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
