# Farm environment integration contract — v0.1

Owner: Matheesha. Consumers: Dulanjaya, Shehani, Bhagya and Akash. Implemented as Python functions and offline CLI; this does not create HTTP endpoints or database records.

## Reproduce examples

```powershell
python -m scripts.generate_climate_examples
python -m scripts.generate_environment_example
python -m unittest discover -s tests -v
```

The generated `data/fixtures/environment.synthetic.json` is a deterministic, invented frontend/backend example. It includes seven POWER-style days and one SMAP-style date to demonstrate unequal periods and missing passes. All values are labeled synthetic. Ordinary Python runs skip the two optional HDF5 tests; use the configured virtual environment for the full 36-test suite.

To combine already downloaded real outputs locally:

```powershell
python -m scripts.build_environment --power .cache/nasa-power/normalized-2025-extremes.json --smap .cache/smap/series-2025-01-01-03.json --farm-id farm-demo-001 --observation-id environment-demo-001 --input-version 1 --output .cache/environment-demo.json
```

That output already exists locally; choose a new path when rerunning. Omit `--smap` to get an explicitly `not_supplied` moisture section. Existing outputs are protected. This command never performs downloads.

## Payload

| Field | Contract |
| --- | --- |
| `schema_version`, `kind` | `0.1`, `farm_environment` |
| `farm_id`, `observation_id`, `input_version` | Caller-supplied server identifiers and positive farm version |
| `requested_point` | WGS84 latitude/longitude; component requested points must agree |
| `data_kind` | Synthetic examples stay synthetic; real POWER + SMAP is `mixed`, preserving component kinds |
| `climate.status` | `complete` or `partial` for daily mean temperature and precipitation coverage; extrema retain independent counts |
| `climate.result` | Existing climate bundle, including observations, threshold summary, scenario and temperature exposure |
| `soil_moisture.status` | `not_supplied`, `no_accepted_retrievals`, `partial`, or `complete` (both passes accepted for every requested date) |
| `soil_moisture.result` | Original SMAP series, including separate passes, quality, distance, per-source period and provenance; null when not supplied |
| `date_label_overlap` | Intersecting calendar labels, or null if periods do not overlap; never a claim of matched acquisition times |
| `limitations` | Required interpretation context; display or link alongside results |

The builder checks period/coverage consistency, shared point, known SMAP product/version/units and synthetic/provider compatibility. It copies caller-owned structures. It consumes validated normalized source payloads, not arbitrary untrusted provider JSON; API owners still need boundary schema validation, authentication, authorization, ID allocation and persistence. Invalid input raises ValueError; malformed structures can raise KeyError/TypeError. Map those to the agreed API error format.

**Shehani:** chart each source's own dates/units; use null as a gap. Do not claim complete temperature extrema when only mean temperature is complete. Keep soil AM/PM separate and display accepted counts, acquisition times, pixel distance and source footprints. Do not place the same resolution label on both sources.

**Dulanjaya:** save this snapshot against the farm input version, retain source metadata and IDs, and reject mismatched farm coordinates. The package includes a hypothetical scenario for exploration, not an independently approved agronomic analysis. Add analysis/scenario identifiers before connecting saved rotation plans.

**Bhagya/Akash:** consuming the common payload does not produce a combined soil-health score. Crop demand, effective rainfall, thresholds and agronomic interpretation still require review.

## Experimental twin sensitivity

```powershell
python -m scripts.check_twin_sensitivity --input .cache/nasa-power/twins-2015-2024.json --output .cache/nasa-power/twin-sensitivity.json
```

The CLI tests nine combinations of rainfall scales 50/100/200 mm and temperature scales 0.5/1/2 C. It rescales the existing per-candidate RMS components, preserves tied best sets and reports whether the best set changed. The saved real two-candidate Sri Lankan example **changes its best set across these settings**. Do not present its default winner as a stable global analogue. Sensitivity checks do not calibrate or validate the comparison metric.

The importable `sensitivity(ranking, settings)` function accepts explicit settings. Its invariance statement applies only to those settings and supplied candidates. No candidates yields unknown stability; ties are explicit. Tests include a known rank reversal and tie.

## Independent readiness

Source adapters, missing-data handling, combined payloads, sample fixtures, contract checks and sensitivity reporting are ready for integration. Still pending: repeatable authenticated SMAP subset automation and longer live soil-moisture coverage; crop-model and twin-metric review; HTTP endpoints and actual UI. This milestone does not claim those tasks are completed.
