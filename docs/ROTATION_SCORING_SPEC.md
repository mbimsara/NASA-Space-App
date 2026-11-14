# Rotation scoring specification v0.1

Owner: Bhagya

Model version: `rotation-score-0.1`

Status: approved for transparent prototype ranking; not agronomic validation,
yield prediction, or a crop-success guarantee.

## Eligibility before scoring

The engine scores only feasible sequences. These hard checks are active:

| Rule | Default | Behavior |
| --- | --- | --- |
| `catalog_review` | Enabled | Every crop and the catalog must be reviewed/approved |
| `season_eligibility` | Enabled | Crop must list the requested season |
| `farmer_exclusion` | Enabled | Farmer-excluded crop IDs are rejected |
| `consecutive_crop` | Disabled | Configurable draft pending approved exceptions |
| `consecutive_family` | Disabled | Not approved as a global rule; family-specific redesign needed |

Each returned candidate exposes checks as `{rule, passed, note}`. Rejected
enumerated sequences expose their failed check. If a season has no eligible
crop, the result returns `candidates: []` and top-level `reasons`; this is not a
server failure.

## Components

Every component uses a 0–100 scale and `higher_is_better` direction.

| Component | Requested priority | Calculation | Null behavior |
| --- | --- | --- | --- |
| `water_sufficiency` | `water` | Mean across seasons of `min(100, baseline available water / high ETc demand × 100)` | `null` if any season lacks a reviewed demand range or complete rainfall input |
| `crop_diversity` | `soil` | Unique crop IDs / sequence length × 100 | Never null for a valid sequence; this is a diversity proxy, not measured soil improvement |
| `scenario_resilience` | `climate` | Mean across seasons of `min(100, scenario available water / high ETc demand × 100)` | `null` when no rainfall-change scenario exists or any season input is missing |

Coverage above 100% is capped for scoring but remains uncapped in the displayed
water-budget range. This prevents excess modeled water from increasing rank
without limit. No score uses SMAP as field soil moisture, inferred nutrients,
yield, prices, or the unapproved legume bonus.

## Weights and total

Requested weights are the farm's nonnegative `water`, `soil`, and `climate`
priorities. Their sum must be positive. Components with `null` values receive
effective weight zero. Remaining requested weights are normalized to sum to one:

```text
effective_weight_i = requested_weight_i / sum(requested weights for available components)
total_score = sum(component_score_i × effective_weight_i)
```

Return requested and effective weights so the interface can explain any
renormalization. A candidate cannot be scored if every positively weighted
component is unavailable.

## Ordering and ties

Rank by:

1. total score descending;
2. conservative baseline water coverage descending;
3. crop-diversity ratio descending;
4. crop-ID sequence lexicographically ascending for deterministic output.

The API must not imply that small score differences are statistically
significant.

## Water output scope

`water_budget_range` is **per season/crop**. The UI should show a per-season
table or timeline containing crop ID, demand low/high, baseline/scenario
rainfall, irrigation, coverage range, balance range, demand basis, model
version, assumptions, and limitations.

A whole-rotation total may be added only when seasons are non-overlapping and
every demand/rainfall/irrigation value covers its matching period. It must not
replace the per-season records.

## Effective rainfall contract

No effective-rainfall method is approved yet. Dulanjaya should send and store:

- historical `rainfall_total_mm` from Matheesha's complete season input;
- `effective_rainfall_mm: null`;
- farmer-entered `irrigation_supply_mm_per_season` when known;
- the provisional assumption that total rainfall is used for screening.

The engine's screening coverage therefore is not an irrigation prescription.
When an effective-rainfall method is reviewed, it requires a new water-model
version and baseline/scenario regression tests.

## UI wording

Use:

- “Heuristic comparison score — not a yield prediction.”
- “Water sufficiency is a screening estimate using total modeled rainfall;
  effective rainfall and field losses are not yet modeled.”
- “Crop diversity is a rotation-structure proxy, not a measured soil-health
  change.”
- “Scenario resilience describes a hypothetical rainfall adjustment, not a
  weather forecast.”

Do not use “best crop,” “expected yield,” “success probability,” or “recommended
profit” for these results.
