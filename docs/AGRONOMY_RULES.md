# Agronomy and financial model register

Owner/reviewer: Bhagya. Research: Tharuka. Financial implementation and catalog validation: Shehani.

No scientific rule or crop value is approved yet. Start with a small Sri Lankan crop catalog and document geographic/seasonal applicability. Use [the catalog schema](../data/schemas/crop-catalog.schema.json); its empty catalog is intentionally not sufficient to generate recommendations.

## Record every rule

| Field | Required meaning |
| --- | --- |
| Rule ID and version | Stable reference stored with analyses |
| Input and units | Values needed; handling of unknown inputs |
| Applicability | Region, season, crop family, soil or irrigation assumptions |
| Calculation/constraint | Explicit reproducible rule; hard exclusion versus ranking preference |
| Evidence | Source URL/title, relevant detail, access date and limitations |
| Review | Researcher, Bhagya's decision/date, unresolved questions |
| Example | Inputs and expected outcome, including an edge case |

## Initial specifications to approve

- Crop repeat/family rules, seasonal eligibility, farmer exclusions, and feasibility when inputs are missing.
- Score components and farmer weights, normalization, tie-breaking, and reasons for rank changes.
- Water demand period and method, effective rainfall assumption, irrigation units, deficit definition, and area conversion. Rainfall totals must align with crop-demand dates.
- Rainfall scenarios: recompute the budget from a baseline; label as hypothetical rather than a forecast.
- Soil/recovery modes: documented benefits/proxies; do not claim measured nutrient recovery or guaranteed post-flood planting safety.
- Finance: currency, area basis, time period, dated input ranges, cost categories, revenue assumptions, and treatment of uncertain yield. Document whether range endpoints are conservative bounds or scenario examples.

Tharuka supplies evidence drafts. Bhagya approves scientific assumptions; Shehani implements the agreed financial specification and checks examples. All numeric model examples remain pending until this review occurs.
