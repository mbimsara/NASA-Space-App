# Bhagya: rotation-engine starting point

## Immediate scope

Bhagya owns candidate generation, documented constraint rules, explainable
ranking, water-budget mathematics, and agronomic review. The first milestone is
not blocked on live satellite access: develop against a normalized climate
fixture, then replace that fixture with Matheesha's response using the same
units and period.

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
# Standard Windows Python uses .venv\Scripts\python.exe. The MSYS2 Python
# currently used in this repository creates .venv\bin\python.exe instead.
.venv\bin\python.exe -m pip install -e ".[dev]"
.venv\bin\python.exe -m pytest
```

The engine currently has no third-party runtime dependencies. Immutable Python
dataclasses provide validation and preserve explicit unknown values.

Development dependencies:

- `pytest`: calculation and rule tests.

## Inputs needed from teammates

From Tharuka, request a small Sri Lankan crop-catalog draft containing crop ID,
name, family, Maha/Yala suitability, seasonal water demand in millimetres,
source URLs, geographic applicability, and limitations or unknowns. Do not add
unsourced crop values to the scoring rules.

From Matheesha, request one normalized seasonal observation fixture containing
rainfall in millimetres, observation start/end dates, source/product metadata,
and missing-data behavior. Agree whether rainfall is total rainfall or effective
rainfall before adding runoff or efficiency factors.

From Dulanjaya, request the shared farm and rotation-analysis API fixtures and a
versioning convention for catalog and scoring assumptions.

From Shehani, align her catalog validator with `Crop` in `models.py`; scientific
approval of the values remains Bhagya's responsibility.

## NASA and event resources

Do not bulk-download the supplied datasets for this module. For the Sri Lankan
demo, prioritize these handoffs:

1. NASA POWER: accessible temperature, rainfall, radiation, and meteorological
   inputs; useful for an initial demo fixture or cross-check.
2. GPM IMERG: precipitation observations for the seasonal rainfall input.
3. SMAP: regional surface-soil-moisture context; it is not a field soil test and
   must not be converted into exact nutrient or root-zone values.
4. Landsat/HLS or MODIS/VIIRS: later vegetation context, not required by the
   first candidate generator.
5. SRTM: later slope/erosion constraints if the team adds sourced terrain rules.

Most USDA resources in the event list are United States-specific (WSS,
SSURGO/STATSGO2, CDL, NAIP, NLCD, PRISM, NASS, and much of OpenET). They should
not be used as local Sri Lankan agronomy evidence. FAO GAEZ is globally relevant
and may support suitability research, subject to checking its resolution,
license, units, and applicability.

Access credentials, provider downloads, caching, and geospatial processing
belong in Matheesha's adapter/backend work. This package accepts normalized
values and preserves their source label.

## Next implementation order

1. Approve a small sourced crop catalog.
2. Add three-to-five-season candidate generation.
3. Add hard exclusions before ranking: season, farmer exclusions, crop history,
   and documented repeat-family/crop rules.
4. Add score components with reasons and assumptions in every result.
5. Confirm effective-rainfall and irrigation-efficiency assumptions with
   Matheesha, then extend the water budget and scenario tests.
