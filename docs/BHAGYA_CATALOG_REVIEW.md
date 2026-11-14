# Bhagya review — Sri Lankan crop catalog draft v0.1

Review date: 2026-11-14

Research commits: `486b081` and `b795585` by Tharuka

Decision: **structure and land-profile separation accepted; scientific values
and numerical rules remain pending**

## Review update for commit `b795585`

The separation of the primary Anuradhapura lowland profile from the secondary
Matale upland mockup resolves the earlier conceptual mixing. Use the coordinates
in `farm.synthetic.json` only for the primary demonstration. Do not apply the
Matale upland assumptions to that farm.

The new evidence/assumption labels are also an improvement, but the crop records
cannot yet be marked approved:

- The five FAO crop-information URLs used for rice, grain legumes, maize,
  groundnut, and pepper returned HTTP 404 during review on 2026-11-14. Replace
  them with working document or archived official links and cite the applicable
  page/table.
- The working FAO 56 Chapter 6 URL is a general single-crop-coefficient chapter;
  it does not by itself establish the stated finger-millet seasonal demand.
- DOA variety pages may support names and maturity groups, but water demand,
  waterlogging tolerance, soil prohibitions, and exact time limits need their
  own directly supporting passages.
- Catalog values currently mix crop evapotranspiration with gross field water
  demand. Rice includes puddling, seepage, and percolation losses while other
  crops are described mainly with ETc. Those quantities must not be compared as
  if they were the same metric. Add a field/method contract or normalize every
  crop to a consistent demand basis before water ranking.
- The `700 mm` Yala cutoff is a model assumption derived from a nominal demand;
  `K_y` relates relative yield response to relative evapotranspiration deficit
  and does not independently prove total crop failure or a statutory 700 mm
  threshold. Keep the cutoff disabled until direct local evidence and the water
  accounting basis are supplied.
- The legume bonus and diversity threshold are correctly labeled heuristics.
  They remain disabled rather than being presented as calibrated agronomic
  effects. A continuous diversity ratio is preferable to an arbitrary pass/fail
  threshold for the first explainable model.

The primary profile is accepted as a **demo configuration proposal**, not as a
verified field classification. Adding landform/drainage behavior requires a
coordinated farm-schema change with Dulanjaya; the engine must not infer those
fields solely from coordinates.

## Replacement water model

Bhagya replaced the broken, mixed-basis numeric inputs with a separate reviewed
demo model in `data/catalogs/crop-water-requirements.json`. It uses the working
FAO Irrigation Water Management Training Manual No. 3, Chapter 3 indicative
seasonal crop-water-needs table. All ranges share the
`seasonal_crop_water_need_etc` basis:

- bean proxy: 300–500 mm;
- maize: 500–800 mm;
- peanut/groundnut: 500–700 mm;
- rice (paddy): 450–700 mm;
- sorghum/millet proxy: 450–650 mm;
- pepper proxy: 600–900 mm.

The bean range is an explicit provisional proxy for mung bean, cowpea, and black
gram; sorghum/millet is a proxy for finger millet; pepper is a proxy for chilli.
These are indicative scenario ranges rather than Sri Lankan cultivar
measurements. The midpoint is derived only as a display/reference value and is
not substituted for the range in water-budget calculations.

Paddy land preparation, puddling, seepage, percolation, conveyance loss, and
irrigation efficiency are excluded from ETc and remain unknown. Therefore, the
range calculator is a transparent screening comparison, not an irrigation
prescription. The original catalog remains research-pending and its single
nominal values do not drive the reviewed range calculation.

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
