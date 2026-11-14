# Design handoff

Owner: Tharuka. Implementation: Shehani.
Interactive Prototype: [`figma-prototype/Build AgroSphere AI MVP/`](../figma-prototype/Build%20AgroSphere%20AI%20MVP/)

The interactive Figma prototype has been exported and structured under [`figma-prototype/Build AgroSphere AI MVP/`](../figma-prototype/Build%20AgroSphere%20AI%20MVP/). It runs as a Vite/React application showcasing the end-to-end user experience for the Sri Lankan demonstration farm (Matale).

To run locally:
```bash
cd "figma-prototype/Build AgroSphere AI MVP"
pnpm install
pnpm dev
```

Core journey: farm setup → observations → three rotation alternatives where feasible → climate scenario → grounded explanation → saved plan.

## Required handoff

- Components: navigation, buttons, fields, cards, crop timeline, comparison table, source/assumption labels, status and uncertainty states.
- Screens: farm setup, farm overview, rotation workspace, scenario comparison, assistant, saved plan.
- Mobile/desktop behavior; readable chart labels and units; keyboard focus, field labels, contrast, and errors linked to inputs.
- Explicit empty/loading/error/offline/stale-analysis states. Unknown soil values remain distinguishable from zero.
- Every observation exposes source/date/resolution; every modeled result exposes assumptions. Synthetic data gets a persistent visible badge.
- Language switching preserves farm/analysis selection. Have fluent reviewers verify Sinhala/Tamil strings and layout.

Review one implemented screen at a time with Shehani. Collect usability findings as GitHub issues with reproduction steps and expected behavior. Advanced screens follow the connected core.
