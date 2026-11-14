# Demo and acceptance walkthrough

Owners: Tharuka (story/visuals), Shehani (UI walkthrough), everyone (module correctness).

## Development fixture

Use `data/fixtures/farm.synthetic.json`. Its point is an illustrative Sri Lankan coordinate, not a real farmer's field. Soil values and crop history are unknown. The fixture intentionally lacks enough agronomic information to justify a recommendation until reviewed inputs/catalog are supplied.

## Connected demonstration

1. Create/reload the demonstration farm; explain history, unknown soil values, and farmer priorities.
2. Show a real retrieved NASA observation with source, dates, resolution, and missing-data context. If using cached observations, show their original dates. If unavailable, state that and use a clearly labeled synthetic UI demonstration.
3. Generate rotation alternatives from the approved catalog. Show eligibility checks, ranking reasons, and water-budget assumptions; explain if fewer than three plans are feasible.
4. Apply a hypothetical 30% rainfall reduction. Compare the recomputed water budget and ranking against the same baseline.
5. Ask the assistant why the selected plan fits the stated priorities. Verify every cited number matches the selected analysis.
6. Save/reopen the plan with its input version and evidence. Show stale-analysis behavior after a farm edit.

## Rehearsal checks

- Run on the deployed environment and a phone-sized layout; verify keyboard navigation.
- Test provider failure, missing observations, empty feasible results, and refresh/reload.
- Keep a dated real-data cache if permitted; maintain an explicitly labeled synthetic fallback recording.
- Confirm language samples with fluent reviewers and prepare an English fallback.
- Capture only working features as implemented; show unfinished capabilities as roadmap items.
- Maintain a source list, limitation slide, and a short recording under the submission's verified requirements. Add event-specific duration/format when confirmed.
