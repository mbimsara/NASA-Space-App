# Crop catalog source check — 2026-11-14

> Historical audit, superseded on 2026-11-15 by project-owner deadline review
> `0.2-demo-reviewed-proxies`. Broken links were replaced with working official
> FAO and Sri Lanka DOA sources; nominal values now match the midpoint of the
> separately reviewed FAO ranges. Approval is for transparent hackathon
> screening only, not cultivar-specific agronomic prescription.

Scope: `data/catalogs/crops.json` (`0.1-draft-referenced`, 8 crops), checked
against the approval criteria in [Bhagya's catalog review](BHAGYA_CATALOG_REVIEW.md).
This is a source-availability and evidence check prepared for Bhagya. It is
**not** an agronomic approval; only the reviewer can approve records.

## Result

**No crop record passes, so nothing is approved.** The catalog stays
`research_pending` and all eight records stay `draft`. `crops.json` was not
modified. The rotation API therefore keeps returning a successful analysis with
`candidates: []` and explicit reasons. This is the intended behaviour.

## Source availability (fetched 2026-11-14)

| Cited URL | Used by | Result |
| --- | --- | --- |
| `fao.org/land-water/.../crop-information/rice/en/` | rice | HTTP 404 |
| `fao.org/land-water/.../crop-information/grain-legumes/en/` | mung bean, cowpea, black gram | HTTP 404 |
| `fao.org/land-water/.../crop-information/maize/en/` | maize | HTTP 404 |
| `fao.org/land-water/.../crop-information/groundnut/en/` | groundnut | HTTP 404 |
| `fao.org/land-water/.../crop-information/pepper/en/` | chilli | HTTP 404 |
| `fao.org/3/x0490e/x0490e0b.htm` | finger millet | Redirects to FAO-56 Chapter 6, a general crop-coefficient chapter with no finger-millet seasonal demand |
| `doa.gov.lk/rrdi-varieties/` | rice | HTTP 404 |
| `doa.gov.lk/fcrdi-crop-varieties/` | all seven field crops | HTTP 404 |
| `fao.org/4/s2022e/s2022e07.htm` (water model, not the catalog) | `crop-water-requirements.json` | Works. Table 14 confirms every reviewed range (rice 450–700, bean 300–500, maize 500–800, peanut 500–700, sorghum/millet 450–650, pepper 600–900 mm) |

## Per-crop status

| Crop | Blocking issue | Needed for approval |
| --- | --- | --- |
| rice | Both sources 404. The catalog value (1050 mm) mixes gross paddy demand with ETc | A working DOA/RRDI document for variety duration, plus a decision to use the ETc range from the water model |
| mung-bean | Both sources 404; only a generic bean proxy is available | Direct FCRDI/DOA crop recommendation page; cultivar-specific evidence or an accepted proxy decision |
| maize | Both sources 404 | Direct source for duration and drainage constraint |
| groundnut | Both sources 404 | Direct source for duration and soil applicability |
| cowpea | Both sources 404; bean proxy | As for mung bean |
| finger-millet | FAO source does not state the claim; DOA 404 | A finger-millet-specific source, or acceptance of the sorghum/millet proxy |
| black-gram | Both sources 404; bean proxy | As for mung bean |
| chilli | Both sources 404; pepper proxy | Direct source for duration and the Solanaceae rotation rule |

## What already works

The seasonal water screening does not depend on the catalog's single nominal
values. It uses the separately reviewed `crop-water-requirements.json`
(`status: reviewed_for_demo`), whose source was re-verified above. Once Bhagya
approves records (set catalog `status` to `reviewed` and the records to
`approved`), analyses will show candidates with season-specific water budgets
without any code change.
