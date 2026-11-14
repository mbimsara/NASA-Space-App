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

### Current NASA POWER handoff

Matheesha's `matheesha/nasa-power-integration` branch now produces a normalized
NASA POWER result. For the connected first milestone, pass that result to
`ClimateInput.from_nasa_power(...)`, then pass the returned input to
`calculate_water_budget(...)`.

Only `summary.rainfall_total_mm` is accepted. It represents the complete
requested period in millimetres. If even one daily rainfall value is missing,
Matheesha's adapter returns `null` for the total and this engine rejects it.
Never replace it with `rainfall_available_days_mm`, and never interpret NASA
POWER as an individual-field measurement.

The requested POWER dates must cover the same period as the crop-demand value.
Before integration, Bhagya and Matheesha still need to agree on:

- crop-cycle start and end dates;
- whether crop demand uses total or effective rainfall;
- irrigation efficiency, runoff, and soil-storage assumptions;
- acceptable observation coverage and source/version metadata.

SMAP can later add regional surface-moisture context, while GPM IMERG can later
provide a precipitation comparison. Neither is needed to run the initial
candidate generator. Landsat/HLS, MODIS/VIIRS, SRTM, and ECOSTRESS are later
contextual inputs and should not delay the connected core.

## Current shared contracts

The branch includes the shared `origin/main` contract commit. The crop loader
reads `data/catalogs/crops.json` according to
`data/schemas/crop-catalog.schema.json`. The committed catalog is deliberately
empty and research-pending, so it produces no recommendations.

Candidate generation example:

```python
from agrosphere_rotation import RepeatPolicy, generate_candidates, load_catalog

catalog_version, crops = load_catalog("data/catalogs/crops.json")
result = generate_candidates(
    crops,
    ("maha", "yala", "maha"),
    excluded_crop_ids=frozenset(),
    repeat_policy=RepeatPolicy(
        forbid_consecutive_crop=False,
        forbid_consecutive_family=False,
    ),
)
```

Repeat constraints default to disabled because no scientific rule has been
approved. Enable them only after recording evidence and Bhagya's review in
`docs/AGRONOMY_RULES.md`.

## Next implementation order

1. Approve a small sourced crop catalog; the shared catalog is currently empty.
2. Record and approve repeat-crop/family rules in the agronomy register.
3. Connect farm history and farmer exclusions from the shared farm contract.
4. Specify score components, normalization, tie-breaking, reasons, and model
   version before implementing numerical ranking.
5. Confirm effective-rainfall and irrigation-efficiency assumptions with
   Matheesha, then extend the water budget and scenario tests.
