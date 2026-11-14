# Bhagya review — Sri Lankan crop catalog draft v0.1

Review date: 2026-11-14  
Research commit: `486b081` by Tharuka  
Decision: **structure accepted; scientific values and rules remain pending**

## Catalog decision

The eight-crop draft is useful and follows the shared schema. Crop IDs,
families, `maha`/`yala` labels, explicit units, source fields, limitations, and
draft statuses are suitable for continued development.

No crop is approved for recommendation yet. The cited DOA links are institute
landing pages, while the notes make precise claims about crop duration, water
demand, drought tolerance, nitrogen effects, and soil applicability. Before
approval, each numerical or constraint-producing claim needs a direct document,
page/table, or crop recommendation page that supports it. Record whether a
water value is crop evapotranspiration, irrigation requirement, total water
input, or a planning estimate and ensure its period matches the crop cycle.

Do not replace the midpoint values with zero. Keep them as draft research
values until verified. The catalog-level status remains `research_pending`, and
all crop records remain `draft`.

## Rule decisions

| Rule | Decision | Required follow-up |
| --- | --- | --- |
| `RULE-ROT-001-v0.1` same-crop repeat | Keep as a configurable draft; do not enable globally | Link direct crop/rotation guidance and decide documented exceptions, especially rice-rice under irrigation |
| `RULE-ROT-002-v0.1` family repeat | Reject as a global hard rule; retain for redesign | Define family-specific rules. A global switch can remove common rice-maize and pulse sequences without enough evidence |
| `RULE-SOIL-001-v0.1` legume bonus | Evidence concept accepted; numeric 15–25% bonus not approved | Link the source for residual-N ranges and specify a transparent, non-yield soil score |
| `RULE-SOIL-002-v0.1` diversity ratio | Formula may be displayed descriptively; `D >= 0.6` preference not approved | Provide a source for the threshold or use the continuous ratio without an evidence claim |
| `RULE-EXCL-001-v0.1` Yala water cutoff | Not approved | Verify the 700 mm cutoff and define total/effective rainfall plus irrigation math for the same crop period |
| `RULE-EXCL-002-v0.1` drainage | Concept retained; not implementable yet | Add an agreed drainage field to the farm contract and link crop-specific standing-water tolerances |

## Inputs required before approval

1. Direct evidence for every water-demand value and whether it represents a
   range, midpoint, crop evapotranspiration, or irrigation requirement.
2. One precise demonstration location/land type. Anuradhapura lowland paddy and
   Matale upland conditions must not be treated as interchangeable.
3. Crop-cycle dates or durations aligned with the NASA POWER rainfall period.
4. A decision for unknown irrigation and drainage inputs that reports an
   unresolved risk without assuming safe conditions.
5. Versioned exceptions for crop/family repetition rules.

Until these checks are complete, the engine may load the catalog and demonstrate
validation, but it must return no production recommendations.
