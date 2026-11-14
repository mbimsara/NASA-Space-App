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

Next steps: verify product spatial resolution and attribution; agree chart/API fields with Shehani and Dulanjaya; agree rainfall period/units with Bhagya before adding climate indicators or water scenarios.
