# Daily temperature exposure

NASA POWER T2M_MAX and T2M_MIN are optional additions to the historical adapter. NASA's [API tutorial](https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/) demonstrates these parameters; [source methodology](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) explains that daily extremes use hourly values rather than daily means. No projection API or additional model source is used here.

```powershell
python -m scripts.nasa_power --start 2025-01-01 --end 2025-12-31 --include-extremes --output .cache/nasa-power/normalized-2025-extremes.json
python -m scripts.analyze_climate --input .cache/nasa-power/normalized-2025-extremes.json --output .cache/nasa-power/climate-2025-extremes.json --hot-max-at-or-above-c 35 --cold-min-below-c 10
```

These outputs have already been generated locally; reuse them rather than redownload. Other team members can run these commands once. Existing outputs are protected. `--include-extremes` requires both variables when importing a raw response as well.

Normalized daily rows add nullable `temperature_max_c` and `temperature_min_c`. Summaries add extrema coverage counts and highest/lowest available daily values. Missing days remain unknown; zero and negative Celsius values are valid. Wrong units or inconsistent minimum/mean/maximum values fail validation.

Analysis and handoff bundles add `temperature_exposure`: threshold counts, available coverage and the longest observed consecutive hot run. `cold_nights` is the daily-minimum threshold count, not an assertion that observations occurred at night. Older files without extrema produce null exposure counts. Missing maxima break runs and mark the longest observed run as a lower bound.

Defaults of maximum >=35 C and minimum <10 C are exploratory, not crop-specific thresholds or a heatwave definition. Review thresholds with Bhagya before crop scoring. Daily-mean warm-day and daily-maximum hot-day counts remain separate.

## Verified 2025 demonstration

All 365 extrema days were retrieved at latitude 8.3, longitude 80.4. Highest daily maximum: 37.40 C; lowest daily minimum: 18.68 C. With the defaults: 17 hot days, zero daily minima below 10 C, and a four-day longest hot run. These are regional gridded historical estimates, not individual field measurements or forecasts.

All 22 offline tests pass, including optional-field compatibility, coverage, threshold equality, missing-day breaks, and inconsistent extrema rejection. Run `python -m unittest discover -s tests -v`. See [attribution](ATTRIBUTION.md).
