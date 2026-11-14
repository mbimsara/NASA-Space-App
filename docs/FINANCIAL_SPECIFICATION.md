# Financial scenario specification v0.1

Owner/reviewer: Bhagya

Implementation: Shehani (`origin/branch-shehani`, commit `03a46b7`)

Review date: 2026-11-14

Formula status: **approved with implementation conditions**

Input-data status: **pending sourced local values**

## Purpose and interpretation

The calculator compares user-supplied cost, yield, and price scenario ranges for
one crop cycle. Results are deterministic arithmetic scenarios, not forecasts,
profit promises, crop recommendations, or guarantees. Range endpoints are
illustrative bounds from explicit inputs; they are not confidence intervals.

Use hectares internally, kilograms for production, an explicit three-letter
currency code, and one crop cycle as the time basis. All inputs used together
must refer to compatible locations, crop varieties/grades, and dates or clearly
disclose differences.

## Approved formulas

For area `A` in hectares, cost-category ranges `[C_i_low, C_i_high]` in currency
per hectare per crop cycle, yield range `[Y_low, Y_high]` in kg/ha per crop
cycle, and farm-gate price range `[P_low, P_high]` in currency/kg:

```text
cost_low    = A × sum(C_i_low)
cost_high   = A × sum(C_i_high)

revenue_low  = A × Y_low  × P_low
revenue_high = A × Y_high × P_high

net_low  = revenue_low  - cost_high
net_high = revenue_high - cost_low

break_even_price_low  = cost_low  / (A × Y_high)
break_even_price_high = cost_high / (A × Y_low)
```

The net interval intentionally pairs the lowest revenue with the highest cost
and the highest revenue with the lowest cost. This is conservative interval
arithmetic, not a claim that those endpoints are equally likely. Break-even
price is unknown when minimum yield is zero.

Approved area conversions:

```text
1 acre = 0.40468564224 hectares
1 perch = 1/160 acre = 0.002529285264 hectares
```

Do not round during calculations. Round only for display while retaining the
unrounded result in application state and stored analyses.

## Missing data and validation

- Area must be finite and greater than zero.
- All known range values must be finite and nonnegative; low must not exceed
  high.
- A range is either complete or unknown. A half-entered range is invalid.
- If any cost category is unknown, total cost and net are unknown.
- If yield or price is unknown, revenue and net are unknown.
- Missing values remain `null`; they never become zero.
- Zero is a valid entered endpoint, except that zero minimum yield makes the
  break-even price range undefined.
- Negative net values must be displayed rather than clamped to zero.

## Required cost categories and provenance

The calculator may accept flexible categories, but the interface should prompt
for relevant items such as seed/planting material, land preparation, fertilizer
and soil amendments, crop protection, irrigation/energy, hired labour,
machinery, harvest/post-harvest, transport, and other costs. An omitted category
must be visibly disclosed; it must not silently imply zero cost.

Every cost, price, and yield range needs traceable provenance:

- source label and URL or document reference;
- quoted/observed date and access date;
- geographic market or production area;
- crop/variety and grade where relevant;
- unit and period;
- whether the value is farmer-entered, observed, researched, or synthetic.

One generic source attached to the whole calculation is insufficient when
different inputs come from different sources. Each input or category must link
to its applicable source reference. Synthetic worked examples must remain
clearly labeled synthetic.

## Required changes to Shehani's draft

The arithmetic in `frontend/src/finance/calculator.ts` is approved. Before the
pending-approval banner is removed:

1. Change the specification version from `0.1-draft` to `0.1` and reference
   this document.
2. Replace “expected yield” wording with “yield scenario range.”
3. Extend source records beyond label/date to include a URL or document
   reference and map sources to the inputs they support.
4. Display omitted/unknown cost categories and data limitations beside results.
5. Preserve the disclaimer that outputs are illustrative ranges, not forecasts
   or guarantees.

The worked values in tests (for example LKR 100–120/kg and 3,000–4,000 kg/ha)
remain synthetic arithmetic fixtures. Formula approval does not approve those
numbers as Sri Lankan market or yield evidence.
