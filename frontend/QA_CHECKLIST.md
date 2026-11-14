# Frontend workflow QA checklist

Task 4 run evidence and real-browser commands: [LIVE_MODE_TASK4.md](../docs/LIVE_MODE_TASK4.md).
Live HTTP is now the default; the synthetic demo requires explicit `VITE_USE_FIXTURES=true`.

Owner: Shehani. Run before each integration merge and at feature freeze. Record date, build/commit, mode (fixtures or live API), device, and any failures as GitHub issues with reproduction steps.

## Automated (must pass)

- [ ] `npm run typecheck`
- [ ] `npm test` — finance worked examples, catalog validation, farm form rules, stale-response guard, store invariants, fixture persistence/version conflicts
- [ ] `npm run build`
- [ ] `python scripts/validate_data.py` (repository root)

## Core journey (acceptance checks 1, 3–7)

1. [ ] Home → **Load synthetic demo farm**. Fixture ribbon and "Synthetic data" badges are visible.
2. [ ] **Observations** loads; coverage shows gaps ("x of y days"); missing days appear as gaps, not zeros; source/resolution/retrieval date are shown (or "not recorded").
3. [ ] Change the date range to start after the end, and confirm the button is disabled and an error is shown.
4. [ ] **Rotations** → Generate. Up to 3 plans show timeline, score components with weights, water budget with assumptions, constraint checks, and source/catalog/model versions.
5. [ ] Edit the farm: add `maize` to excluded crops → re-run → fewer plans with the exclusion reason shown.
6. [ ] Select a plan → **Save this plan** → saved plan page opens. Reload the browser → plan reopens with input snapshot, sources, assumptions, versions.
7. [ ] **Stale analysis:** edit the farm (any field) → Rotations shows the outdated banner and **Save** is disabled; Scenario shows the banner; the saved plan shows "inputs changed".
8. [ ] **Scenario:** −30% → table compares baseline vs scenario per plan (rank, score, effective rainfall, deficit), labelled hypothetical and referencing the same baseline ID.
9. [ ] **Assistant:** context box shows the analysis, selected plan, and scenario; numbers in the answer match the selected plan; source IDs link back to rotations/scenario. Changing the scenario or plan clears the conversation.
10. [ ] **Finance (spec v0.1):** add a source record marked *Synthetic*, link it to every input, and enter the synthetic worked example (2 ha; seed 10,000–12,000; labour 20,000–30,000; remove the other categories; yield scenario 3,000–4,000 kg/ha; price 100–120/kg) → cost 60,000–84,000; revenue 600,000–960,000; net 516,000–900,000. Removed categories are listed as "not assumed zero"; the synthetic-inputs warning shows. Unlink the price source → an error asks for a source. Clear the yield fields → revenue/net show "Unknown", not 0. The banner shows spec v0.1, the spec reference, and "input data pending".

## Farm form

- [ ] Required name, positive area, coordinate range, harvest ≥ planting, no future planting, soil tests need a unit.
- [ ] Area in acres/perches shows the stored hectares.
- [ ] Irrigation: "Unknown" saves null and Rotations shows the "water screening unavailable" notice with water values Unknown; "Rainfed" saves 0 and water values appear; "Irrigated" with no amount shows a clear error.
- [ ] Map click updates the coordinates; typing coordinates moves the marker.
- [ ] Type a farm name, leave without saving, return → draft banner; **Resume** restores; **Clear** removes it.
- [ ] On a validation error, focus moves to the error summary.

## Saved plan follow-ons

- [ ] Action calendar: enter planting dates per season, add a harvest before planting → error and download disabled; fix it → entries sorted by date; download `.ics` opens in a phone calendar.
- [ ] Reopen the plan after reload → calendar entries kept. "Season feedback" is shown as a planned feature.
- [ ] Offline: open a saved plan once, then go offline (DevTools → Network → Offline) → offline banner; the plan reopens with "Showing the copy saved on this device on …". In live mode, saving/generating buttons are disabled with an offline note.
- [ ] Production build only (`npm run build && npm run preview`): after one online visit, the app shell loads offline.
- [ ] Roadmap page lists every planned feature with "Planned feature — not yet implemented".

## Failure and isolation cases

- [ ] Live mode with the backend stopped (`VITE_USE_FIXTURES=false`) → network error with **Retry** on every screen.
- [ ] Set the farm location outside Sri Lanka (fixture) → observations show the "data not available" state.
- [ ] Open farm A, generate rotations, then open farm B → no farm A results appear on any farm B screen.
- [ ] Unknown plan URL `/plans/does-not-exist` → "not found" with a way home.
- [ ] Catalog page shows validation status; a broken `data/catalogs/crops.json` (e.g. duplicate ID) shows the problem list and a warning on Rotations.

## Accessibility and mobile (with Tharuka)

- [ ] Keyboard only: skip link, header, farm tabs, all controls reachable with visible focus; sliders work with arrow keys.
- [ ] Every input has a visible label; errors are linked with `aria-describedby`.
- [ ] 360 px wide: no horizontal page scroll; farm tabs scroll horizontally; tables scroll inside their cards.
- [ ] Chart axes show units (mm, °C); the legend is readable.
- [ ] Print the saved plan: navigation is hidden; timeline, inputs, sources, assumptions, and analysis date are printed.

## Language

- [ ] Switch to සිංහල / தமிழ் on any screen → farm, analysis, and selected plan are preserved; untranslated strings fall back to English.
- [ ] The language persists after reload; the assistant request uses the selected language.
- [ ] Fluent reviewers have signed off on Sinhala and Tamil strings (name and date): _pending_.
