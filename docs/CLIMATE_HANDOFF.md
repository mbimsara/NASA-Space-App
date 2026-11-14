# Climate module handoff — Matheesha

Status: standalone Python functions and command-line tools are implemented and tested. HTTP routes, authentication, persistence and frontend screens are not implemented here. Use Python 3.10+; no third-party dependencies are required.

## Start without NASA access

```powershell
python -m unittest discover -s tests -v
python scripts/validate_data.py
python -m scripts.generate_climate_examples
```

The generator deterministically rewrites only `data/fixtures/climate-bundle.synthetic.json`. Its seven-day example is invented, visibly labeled synthetic, and has no provider request URL or retrieval date. It is for interface/integration development, not evidence of NASA conditions. Baseline rainfall is 35 mm and the -30% example is 24.5 mm. Real downloaded data remains in ignored `.cache/`.

## Backend — Dulanjaya

```python
from backend.services.nasa_power import fetch, normalize
from backend.services.climate_handoff import climate_bundle

raw, retrieved_at, url = fetch(8.3, 80.4, "2025-01-01", "2025-01-31")
observations = normalize(raw, "2025-01-01", "2025-01-31", retrieved_at, url)
payload = climate_bundle(observations, "farm-server-id", "obs-server-id", 1)
```

Run provider access outside latency-sensitive request handling where possible; cache by coordinates, dates, parameter list, community and time standard. Retain source/retrieval metadata. Do not repeat requests on each chart render. Use server-allocated IDs and the farm's actual input version, not the example strings.

The bundle has `observation`, `historical`, and `rainfall_scenario` keys. `observation_envelope` deep-copies inputs so consumers cannot mutate the historical baseline. It is a serializer, not an authorization/database layer; pass normalized adapter output. Backend integration must verify farm coordinates and relationships, persist the snapshot, handle concurrent farm edits, allocate scenario IDs, and mark older analyses outdated.

Errors: invalid dates/coordinates/units/coverage/settings raise `ValueError`; malformed provider payloads can raise `KeyError`/`TypeError`; network calls can raise `HTTPError`, `URLError`, or timeout/I/O errors. Map these to the agreed API errors without exposing provider internals. Missing observations within a structurally valid response become null. Network failure must not return synthetic data labeled as real.

## Frontend — Shehani; design — Tharuka

Use the committed synthetic bundle now. Chart `observation.daily` using `date`, `temperature_c`, and `precipitation_mm_per_day`. Monthly cards use `observation.monthly`; their periods may be partial calendar months. Keep nulls as chart gaps, never zero.

Display `data_kind`, provider/source, UTC period, resolution, retrieval date (or unknown), valid/expected day counts, and limitations. Scenario plots use `rainfall_scenario.daily` baseline/scenario columns; show the hypothetical label and change percentage. Do not label a daily mean-temperature threshold as maximum heat or a heatwave. Twin outputs use lower-is-closer distance and explicit scales, never a match percentage.

## Agronomy — Bhagya

```python
from backend.services.climate_handoff import season_inputs
season = season_inputs(observations, "2025-01-01", "2025-01-31")
```

Dates are inclusive UTC calendar days; demand must use the same period. Rainfall depth is millimeters, not liters or cubic meters. The helper rejects dates outside the supplied history; missing rainfall produces a null total. `effective_rainfall_mm`, `crop_water_demand_mm` and `irrigation_deficit_mm` stay null. Define those formulas, soil/storage/runoff assumptions, irrigation basis, and seasonal boundaries before using them to score rotations. No arbitrary efficiency factor is applied here.

## Assistant — Akash

Resolve farm/observation/scenario context on the server. Explain the bundle's numbers, settings, coverage and limitations. Missing values mean unknown. Uniform rainfall scaling is a what-if exercise; historical comparisons and candidate distances do not predict weather, yield, or crop success. Preserve sources and units in each supported language.

## Function inventory

Bundles now also include `temperature_exposure`. Fetch with `--include-extremes` for T2M_MAX/T2M_MIN coverage; older histories remain valid with null extrema-dependent counts. See [temperature exposure](TEMPERATURE_EXPOSURE.md) for fields, settings and live verification.

| Function | Output / constraint |
| --- | --- |
| `nasa_power.request_url` / `fetch` / `normalize` | Verified NASA endpoint, historical dates, UTC daily rows, summaries and provenance |
| `climate.historical_indicators` | Counts for explicit exploratory thresholds; missing-aware dry runs |
| `climate.rainfall_scenario` | Nonmutating rainfall scaling from -100% through +100% |
| `climate_baseline.compare_monthly` | Complete-month historical reference comparison; target excluded from reference |
| `climate_twins.rank_twins` | Supplied-candidate ranking with strict common coverage; experimental metric |
| `climate_handoff.season_inputs` | Historical season rainfall/temperature with coverage; agronomy values unknown |
| `climate_handoff.observation_envelope` / `climate_bundle` | Versioned module payloads with caller-supplied farm/observation IDs |

## Readiness and remaining decisions

SMAP is now a separate implemented sample pipeline: metadata discovery → authenticated spatial subset via Earthdata → local nearest-pixel/quality extraction → combined AM/PM series. See [SMAP output and integration instructions](SMAP.md). Do not pass it into NASA POWER-specific functions or merge passes by date without preserving their acquisition context.

Independent code, source metadata, tests, examples, run instructions and attribution guidance are ready. Integration still needs backend persistence/cache policy, UI agreement, agronomic model review and twin-distance scale review. NASA POWER and the small SMAP subset pipeline are implemented; other competition-listed products are not claimed as complete. Follow [source restrictions](DATA_SOURCES.md) for any future additions.
