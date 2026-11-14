# AgroSphere AI

A farming decision-support platform for NASA Space Apps Challenge 2026: **Field Shift: Adapting Farms with NASA Data**.

AgroSphere combines Earth observations, farmer inputs, and local agronomy to help farmers compare crop rotations. Every feature supports the same farm profile and rotation decision.

## Start here

The repository currently contains development plans, shared data contracts, and synthetic fixtures. There is no runnable frontend/backend yet.

| Resource | Purpose |
| --- | --- |
| [Implementation plan](IMPLEMENTATION_PLAN.md) | Detailed responsibilities for all six members |
| [Contributing](CONTRIBUTING.md) | Setup status, workflow, review and verification |
| [Architecture](docs/ARCHITECTURE.md) | System boundaries and open decisions |
| [API contracts](docs/API_CONTRACTS.md) | Proposed endpoints, fields, units and errors |
| [First milestone backlog](docs/BACKLOG.md) | Concrete starting tasks and acceptance checks |
| [Data sources](docs/DATA_SOURCES.md) | NASA integration research register |
| [Agronomy rules](docs/AGRONOMY_RULES.md) | Evidence and model review process |
| [Design handoff](docs/DESIGN.md) | Tharuka's UI/UX handoff to Shehani |
| [Figma UI prototype](figma-prototype/Build%20AgroSphere%20AI%20MVP/) | Tharuka's interactive UI/UX prototype & design system |
| [Demo guide](docs/DEMO.md) | Connected walkthrough and fallback rules |
| [Shared data](data/README.md) | Synthetic farm, catalog and schemas |

Validate shared inputs with `python scripts/validate_data.py` (Python 3.10+). GitHub Actions runs this check on pushes and pull requests. The crop catalog is intentionally empty pending research and approval. Application startup instructions will be added to [frontend](frontend/README.md) and [backend](backend/README.md) when scaffolding is implemented.

## Product scope

### Original modules

1. **My Farm Digital Twin:** select a farm and explore historical rainfall, temperature, regional soil moisture, and vegetation observations.
2. **Smart Crop Rotation:** compare crop sequences over three to five seasons using farm conditions, constraints, and priorities.
3. **Climate Scenarios:** explore historical climate risk indicators and test hypothetical changes such as reduced rainfall.
4. **WeedShield:** explore photo-based weed coverage analysis after selecting and validating a suitable model.
5. **SoilRevive:** compare rotation strategies for soil cover, crop diversity, and legumes.
6. **FarmRecovery:** compare recovery strategies following floods or droughts.
7. **Global Climate Twin Finder:** identify regions with similar historical climate patterns.
8. **AI Assistant:** explain actual farm analysis and rotation results in English, Sinhala, and Tamil.

### Added features

| Feature | Intended behavior | Delivery priority |
| --- | --- | --- |
| Farm History & Seasonal Calendar | Record previous crops, planting dates, irrigation, and harvests; use history when evaluating rotations. | Core |
| Farmer Goals & Constraints | Capture water limits, budget, labor, preferred crops, and household food needs. | Core |
| Rotation Comparison Workspace | Compare crop sequences, suitability, water demand, soil benefits, risks, and ranking explanations. | Core |
| Water Budget Planner | Compare estimated seasonal crop water requirements with rainfall and farmer-entered irrigation supply. | Core |
| Soil Test Integration | Accept measured soil pH, organic matter, and nutrient results with units and sampling dates. | Core |
| Cost & Income Scenarios | Compare estimated costs and potential returns using local inputs and price ranges. | Next |
| Cover Crop Planner | Include locally suitable cover crops between main growing seasons. | Next |
| Farm Alerts & Action Calendar | Turn a selected rotation into planting, monitoring, and soil-testing reminders. | Next |
| Offline Farm Notebook | Save farm details and previously generated plans for limited-connectivity use. | Next |
| Season Review & Feedback | Record actual outcomes and compare them with previous estimates. | Next |
| Agronomist Review & Shareable Report | Export farm inputs, rotation comparisons, sources, and assumptions for expert review. | Next |
| Voice Input & Read-Aloud | Support accessible input and spoken explanations in English, Sinhala, and Tamil. | Advanced |

## Delivery sequence

1. **Connected core:** farm profile, history, goals, soil inputs, NASA observation dashboard, rotation comparison, water budget, climate scenarios, and grounded assistant explanations.
2. **Planning and follow-through:** soil improvement and disaster recovery modes in the rotation planner, cover crops, financial scenarios, action calendar, reports, offline notebook, and season feedback.
3. **Advanced capabilities:** validated weed analysis, climate twins, and multilingual voice interaction.

All features are in the product scope. These phases describe implementation order, not completed functionality.

## Hackathon demonstration

Use one Sri Lankan demonstration farm and a researched local crop catalog:

**Select farm → enter history, soil results, and priorities → review NASA observations → compare three rotations → simulate reduced rainfall → compare water and soil tradeoffs → ask the assistant to explain → save or share the plan.**

Keep crop rotation central. SoilRevive and FarmRecovery are planning modes that influence the same rotation comparison rather than separate disconnected tools.

## Figma UI prototype

Tharuka's interactive Figma UI prototype for AgroSphere AI is located in [`figma-prototype/Build AgroSphere AI MVP/`](figma-prototype/Build%20AgroSphere%20AI%20MVP/). It provides an interactive preview of the farmer journey, Earth observation displays, climate scenario adjustments, and crop rotation comparison.

### Running the prototype

```bash
cd "figma-prototype/Build AgroSphere AI MVP"
pnpm install    # or npm install
pnpm dev        # or npm run dev
```

Key prototype components:
- **Farm Overview:** Demo farm location (Matale, Sri Lanka) with localized conditions and baseline soil metrics.
- **Crop Rotation Workspace:** Visual multi-season rotation paths (Rice, Mung bean, Maize, Groundnut).
- **Climate Adjustments:** Dynamic rainfall adjustment sliders for seasonal scenario simulations (e.g. Maha 2026).
- **Income Range & Confidence:** Visual display of price and yield uncertainty bounds.

## Data and model requirements

- Evaluate NASA POWER, GPM, SMAP, and HLS for their appropriate roles; verify access, licensing, resolution, and coverage before integration.
- Show observation sources, dates, units, and spatial resolution. Distinguish regional observations from field measurements.
- Label climate scenarios as hypothetical and disclose rotation scoring and soil-model assumptions.
- Use measured soil tests when available; do not infer exact field nutrient levels from satellite observations.
- Present financial estimates as ranges with input sources and dates; do not promise returns or crop success.
- Ground assistant explanations in actual module outputs and identify missing information.
- Validate photo analysis before claiming reliable weed identification or coverage measurement.
- Store shared farm inputs once so every module uses consistent location, season, crop history, and constraints.

## Current status

Product scope documented. Application implementation has not started.

See the [six-member implementation plan](IMPLEMENTATION_PLAN.md) for responsibilities, Tharuka's UI/UX design assignment, integration contracts, milestones, and acceptance checks.
