# NASA POWER adapter — Matheesha's first working module

NASA POWER is explicitly listed in the [challenge resources](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/?tab=resources). The adapter uses only NASA's daily point API and the Sri Lankan demo point (8.3, 80.4); no other provider is contacted.

## Run from repository root

Python 3.10+; no third-party packages required. Normalize the downloaded PowerShell response without making a network request:

```powershell
python -m scripts.nasa_power --start 2025-01-01 --end 2025-01-31 --input .cache/nasa-power/demo-2025-01.json --output .cache/nasa-power/january-summary.json
```

Fetch a full year (requires network):

```powershell
python -m scripts.nasa_power --latitude 8.3 --longitude 80.4 --start 2025-01-01 --end 2025-12-31 --output .cache/nasa-power/year-summary.json
```

Existing outputs are protected from accidental replacement. Reuse saved files; pass `--refresh` only when intentionally replacing an output. Imported responses have null retrieval time because the original download time is unknown. Fresh retrievals record a UTC timestamp and request URL. Cache outputs remain ignored by Git.

## Output and calculation behavior

`daily` contains ISO dates, Celsius temperature and precipitation rates in mm/day. `monthly` summarizes each requested month's intersection with the requested period, not necessarily a complete calendar month. `summary` covers the whole requested period. Missing date keys and provider fill values become null. Zero remains valid. Unsupported units, incorrect periods, non-UTC data and invalid values fail clearly.

Temperature averages use available valid days and expose their count. Rainfall totals sum the daily rate over one-day intervals and are null if any day is missing. `rainfall_available_days_mm` is a separately labeled partial sum, never a substitute for a full-period total. A dry-run rainfall scenario is not a weather forecast; scenario and water-demand models are not implemented yet.

The domain adapter returns environmental results only. Dulanjaya must add farm/observation IDs, input versions, persistence and HTTP envelopes when integrating it with the proposed API. Shehani can use the daily and monthly arrays after agreeing those chart fields with Matheesha.

## Verification on 2026-11-14

| Retrieval | Temperature coverage | Rain coverage | Mean temperature | Rainfall depth |
| --- | --- | --- | --- | --- |
| User-downloaded January 2025 response | 31/31 | 31/31 | 24.4877 C | 221.69 mm |
| Live January–December 2025 response | 365/365 | 365/365 | 26.6745 C | 1872.54 mm |

These results describe the demo point's gridded estimates, not verified farm conditions. Provider datasets may be revised. Keep actual retrieval metadata with saved analyses.

```powershell
python -m unittest discover -s tests -v
python scripts/validate_data.py
```

Offline tests cover leap days/month boundaries, valid zeros, fill values, absent dates, incomplete rainfall totals, wrong units/periods and invalid request inputs. Live access is tested separately and never required by CI.

## Historical indicators and rainfall scenario

Run the next stage without another provider request:

```powershell
python -m scripts.analyze_climate --input .cache/nasa-power/normalized-2025.json --output .cache/nasa-power/climate-2025.json --rainfall-change-pct -30
```

Use your own normalized filename if different. Choose a new output name when rerunning; existing results are protected. Optional exploration settings are `--dry-below-mm 1`, `--warm-at-or-above-c 30`, and `--rain-at-or-above-mm 20`. These defaults are interface exploration choices, not researched crop risk thresholds. Daily mean temperature cannot establish maximum-temperature heat stress.

The historical output counts valid days below/above these explicit thresholds and the longest contiguous observed dry run. Missing rainfall breaks runs and flags the resulting maximum as a lower bound. All-missing data yields null counts, not a false zero.

The scenario uniformly scales available daily rainfall and returns daily/monthly/full-period baseline differences. Missing values remain missing, full-period totals remain null when incomplete, and historical observations are never mutated. This does not simulate shifted rainfall timing, effective rainfall, crop demand, irrigation deficit, or rotation ranking; those require Bhagya's reviewed water model.

Verified on the saved full-year dataset: 174 days below 1 mm/day, 20 days at or above 20 mm/day, 23-day longest observed run below 1 mm/day, and one day with mean temperature at or above 30 C. These are descriptive counts for this gridded series. A -30% scenario gives 1310.778 mm versus 1872.54 mm baseline, a difference of -561.762 mm.

Nine offline tests now cover the adapter and climate functions, including baseline preservation, incomplete coverage, threshold boundaries, invalid scenario settings, and out-of-order dates. CI runs them with the shared-data checks.

## Multi-year monthly comparison

Retrieve once and reuse the normalized file:

```powershell
python -m scripts.nasa_power --start 2015-01-01 --end 2025-12-31 --output .cache/nasa-power/normalized-2015-2025.json
python -m scripts.compare_climate --input .cache/nasa-power/normalized-2015-2025.json --output .cache/nasa-power/comparison-2025.json --reference-start 2015 --reference-end 2024 --target-year 2025
```

These files have already been generated locally during verification; do not repeat downloads unnecessarily. This compares each 2025 calendar month with the equal-year-weighted 2015–2024 mean for that calendar month. The target year must be outside the reference years. Complete months are required separately for temperature and rainfall; output lists the actual contributing years. At least two complete reference years are needed per variable/month. A zero rainfall reference returns null percentage difference. Inspect coverage before interpreting differences.

This is a descriptive historical reference, not an official climate normal, trend attribution, or forecast. Leap-day contributions remain part of February totals; February lengths can therefore affect rainfall-total comparisons. The historical comparison itself does not compute climate twin scores; the experimental finder below is a separate stage.

Live verification returned all 4,018 days for both variables, 2015–2025. For the demonstration grid point, January 2025 rainfall was approximately 137.20% above the 2015–2024 January average, while July was approximately 82.52% below its July average. Different months need not move in the same direction. These values are sample analysis outputs, not a claim of field conditions.

NASA's [meteorological source documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) verifies the MERRA-2 grid at 0.5 degrees latitude by 0.625 degrees longitude. The adapter includes that metadata for MERRA2-only responses; older saved outputs may still contain null and can be regenerated deliberately. Thirteen offline tests cover retrieval normalization, threshold indicators, scenarios and reference comparisons.

## Experimental climate twin finder

Daily maximum/minimum support and exposure counts are documented in [temperature exposure](TEMPERATURE_EXPOSURE.md).

`backend/services/climate_twins.py` compares supplied NASA POWER histories over the same reference years. Only complete months for both variables in every reference year are accepted. Source products, time standard and data kind must match; target/duplicate coordinates are excluded. It does not automatically discover or download global candidates.

For each location, calculate 12 mean monthly rainfall totals and 12 mean monthly temperatures, weighting years equally. The distance is:

```text
rain_rms = sqrt(mean((candidate_month_rain - target_month_rain)^2))
temperature_rms = sqrt(mean((candidate_month_temperature - target_month_temperature)^2))
distance = sqrt((rain_rms / rain_scale_mm)^2 + (temperature_rms / temperature_scale_c)^2)
```

Defaults of 100 mm and 1 C are explicit exploratory scaling choices, not scientifically calibrated importance weights. Lower distance means closer under this metric; it is not a percentage match, probability, yield prediction, or crop-suitability score. The output preserves differences by month, provenance and rejected-candidate reasons. Monthly averages omit extremes, soil, topography and irrigation. Nearby sites may share a source grid cell.

Two permitted Sri Lankan demo candidates have been retrieved from NASA POWER, each with all 3,653 days during 2015–2024:

```powershell
python -m scripts.nasa_power --latitude 6.12 --longitude 81.12 --start 2015-01-01 --end 2024-12-31 --output .cache/nasa-power/hambantota-2015-2024.json
python -m scripts.nasa_power --latitude 9.66 --longitude 80.03 --start 2015-01-01 --end 2024-12-31 --output .cache/nasa-power/jaffna-2015-2024.json
python -m scripts.find_climate_twins --target .cache/nasa-power/normalized-2015-2025.json --candidate "Hambantota=.cache/nasa-power/hambantota-2015-2024.json" --candidate "Jaffna=.cache/nasa-power/jaffna-2015-2024.json" --start-year 2015 --end-year 2024 --output .cache/nasa-power/twins-2015-2024.json
```

Do not redownload existing local files. These are illustrative points near the named locations, not surveyed farm boundaries. Among these two candidates only, the verified distance was 1.3502 for Hambantota and 1.4653 for Jaffna against the original demo point. This is an experimental regional demonstration, not a global best-match claim. Expanding the candidate set requires the owner's source/location restrictions and a reviewed comparison method.

Sixteen offline tests cover the current module set. Raw and derived provider downloads remain under ignored `.cache/`; code, tests, and documentation can be shared without committing those files.

The [climate handoff](CLIMATE_HANDOFF.md) now provides integration helpers and reproducible synthetic examples. [Attribution notes](ATTRIBUTION.md) record verified NASA credit guidance. Remaining team decisions: review comparison scales/method, agree final HTTP/chart contracts, and approve rainfall-period/units and agronomic formulas with Bhagya.
