# Design handoff

Owner: Tharuka. Implementation: Shehani.

Tharuka's approved landing page, navigation, visual tokens, cards, responsive
layout, and workflow patterns are now integrated directly into Shehani's
functional application under `frontend/`. The standalone sample prototypes were
removed after integration so there is one maintained user interface.

To run locally:
```bash
cd frontend
npm install
npm run dev
```

Core journey: farm setup → observations → three rotation alternatives where feasible → climate scenario → grounded explanation → saved plan.

## Integrated handoff and review criteria

- Components: navigation, buttons, fields, cards, crop timeline, comparison table, source/assumption labels, status and uncertainty states.
- Screens: farm setup, farm overview, rotation workspace, scenario comparison, assistant, saved plan.
- Mobile/desktop behavior; readable chart labels and units; keyboard focus, field labels, contrast, and errors linked to inputs.
- Explicit empty/loading/error/offline/stale-analysis states. Unknown soil values remain distinguishable from zero.
- Every observation exposes source/date/resolution; every modeled result exposes assumptions. Synthetic data gets a persistent visible badge.
- Language switching preserves farm/analysis selection. Have fluent reviewers verify Sinhala/Tamil strings and layout.

Review one implemented screen at a time with Shehani. Collect usability findings as GitHub issues with reproduction steps and expected behavior. Advanced screens follow the connected core.
