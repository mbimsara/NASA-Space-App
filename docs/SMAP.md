# SMAP integration — access and preparation

For resumable authenticated subsetting, see [automation instructions and verified January 2025 results](SMAP_AUTOMATION.md). The full-month live run completed: all 31 files verified, with 12 accepted AM and 11 accepted PM retrievals. File delivery is complete; retrieval coverage remains partial.

Status: public discovery, quality filtering, local file inspection, nearest-pixel extraction and combined time-series output are implemented. All three January 1–3, 2025 Harmony subset files have now downloaded and been extracted successfully. Missing passes remain unknown.

## Selected product

[NSIDC SPL3SMP_E Version 6](https://nsidc.org/data/spl3smp_e/versions/6), DOI https://doi.org/10.5067/M20OXIZHY3RJ . This enhanced daily radiometer product is distributed in HDF5 on a 9 km EASE grid and covers the demonstration point in Sri Lanka. Grid posting is not proof of independent field-scale resolution. NSIDC requires Earthdata access for data and a dataset citation when used. Record the subset and actual access date. Use the dataset landing page's current citation, not an invented project license.

## Account step — user action

1. Open [NASA Earthdata registration](https://urs.earthdata.nasa.gov/users/new).
2. Complete registration, any email verification, and sign in yourself.
3. Tell the assistant only that registration is complete. Do not paste passwords or tokens into chat, source files, or Git.
4. Next, use Earthdata Search/Harmony to request a small Sri Lankan subset. Do not download a full global granule for this project task. Authentication and any account agreements remain user-controlled.

No credentials have been requested or stored. Public discovery needs no authentication. NASA NSIDC's [migration notice](https://nsidc.org/data/user-resources/data-announcements/user-notice-nasa-earthdata-harmony-data-transformation-services-now-available-smap-l2-l4-data-sets) directs customization to Earthdata Harmony; avoid obsolete legacy download scripts.

## Discovery

```powershell
python -m scripts.discover_smap --start 2025-01-01 --end 2025-01-03 --output .cache/smap/discovery-2025-01-01-03.json
```

This sample has already run locally: three granules, no truncation. It contacts only NASA CMR and does not follow returned download links. Query coordinates default to the existing Sri Lankan demo point. Discovery is limited to 31 requested days; output reports truncation rather than implying full pagination. Search overlap does not establish valid pixel retrievals. See [CMR API documentation](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).

## Quality preparation

According to the [V006 user guide](https://nsidc.org/sites/default/files/documents/user-guide/spl3smp_e-v006-userguide.pdf), soil moisture uses m3/m3, with -9999 fill. Recommended soil-moisture retrieval flags are 0 or 8. `quality_filter` retains flags and rejection reasons and returns null for rejected samples. Its broad physical guard is not a substitute for per-file valid limits/porosity. AM and PM passes must stay distinguishable; PM variable names carry `_pm` suffixes.

The future file reader must inspect dataset units, fill/valid attributes, coordinates, product/version and group names, preserve surface flags, and verify distance to the requested location before interpreting pixels. Do not silently choose a farther high-quality pixel when the nearest pixel is rejected. Preserve actual acquisition times and do not invent daily coverage from compositing cadence.

## Tests and remaining gate

The full optional-dependency environment runs 27 tests. SMAP coverage includes mocked discovery, quality flags, missing values, file inventory, nearest-pixel rejection, distance limits and missing-pass geolocation. Public discovery and the first downloaded science subset were also verified live; further dates and application integration remain pending.

## Verified subset reader

The signed-in Earthdata Search request used V006, January 1–3, 2025, and spatial trimming to 8.2–8.4 N / 80.3–80.5 E. Harmony returned a NetCDF-4 subset; no full global file was downloaded. It contains 4-by-3 global-grid arrays. Files and results stay in ignored `.cache/smap/`.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-smap.txt
.venv/Scripts/python.exe -m scripts.inspect_smap_file --input .cache/smap/subsets/SMAP_L3_SM_P_E_20250101_R19240_001_subsetted.nc4 --output .cache/smap/inventory-2025-01-01.json
.venv/Scripts/python.exe -m scripts.extract_smap_point --input .cache/smap/subsets/SMAP_L3_SM_P_E_20250101_R19240_001_subsetted.nc4 --output .cache/smap/point-2025-01-01.json
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The environment/files already exist locally; skip setup and use different output paths when rerunning. Optional dependency: h5py 3.16.0, tested on Python 3.14. The normal standard-library suite skips file-reader tests if h5py is absent; run the full suite in the environment for all 27 tests. CI also runs an optional-dependency job.

Extraction reads global AM/PM groups separately, selects the nearest geolocated pixel before quality checks, rejects pixels farther than the explicit 15 km default, and checks actual file units/fill/valid limits. The input volume ratio `cm**3/cm**3` is numerically identical to output m3/m3. Surface and retrieval flags, raw acquisition time, pixel coordinates, distance, file hash and version-selection basis are preserved. No farther valid pixel replaces a rejected nearest sample. No geolocation in a pass yields an explicit unavailable result.

Live January 1 result: AM unavailable; PM accepted with retrieval flag 8 and surface flag 128, soil moisture 0.4747059 m3/m3 at (8.3252602, 80.4304962), 4.3759 km from the demo point. Raw PM acquisition time is 2025-01-01T12:37:21.592Z. This single retrieval does not establish a drought threshold, field irrigation requirement, or root-zone condition. Product V006 selection is verified through the Earthdata collection, not guessed from the granule release string.

## Completed three-day series

All three spatially trimmed files were downloaded after Harmony completed. January 3's earlier download timeout was resolved by retrying the available subset link; no new global-data request was needed.

| Composite date | AM filtered moisture (m3/m3) | PM filtered moisture (m3/m3) |
| --- | --- | --- |
| 2025-01-01 | Unknown: no valid pass geolocation | 0.4747059 |
| 2025-01-02 | 0.4464757 | Unknown: no valid pass geolocation |
| 2025-01-03 | Unknown: no valid pass geolocation | Unknown: no valid pass geolocation |

Both accepted samples use quality flag 8, surface flag 128 and the same nearest grid point about 4.3759 km away. January 2 AM acquisition time is 2025-01-02T00:51:07.654Z. This is not a continuous two-day change measurement at a fixed time of day; AM and PM must remain separate.

After extracting each file with `scripts.extract_smap_point`, combine the explicit inputs:

```powershell
.venv/Scripts/python.exe -m scripts.build_smap_series --input .cache/smap/point-2025-01-01.json --input .cache/smap/point-2025-01-02.json --input .cache/smap/point-2025-01-03.json --start 2025-01-01 --end 2025-01-03 --output .cache/smap/series-2025-01-01-03.json
```

This file already exists locally. `build_series(records, start, end)` is also importable from `backend.services.smap_series` without optional HDF5 dependencies. It checks common product/version, requested point and distance policy, rejects duplicate granule dates and pass identifiers, and fills unsupplied dates/passes with explicit null reasons. It does not interpolate or average. Sources remain traceable through file hashes and version-selection notes.

### Frontend/backend handoff

- **Dulanjaya:** persist extracted records and the series with farm/input version and observation IDs. Verify ownership and coordinates before serving; add recorded download/source metadata. Do not infer V006 from the release code in a filename.
- **Shehani:** plot separate AM/PM series from `daily[].AM.soil_moisture_m3_m3` and `daily[].PM.soil_moisture_m3_m3`; preserve gaps. Use `granule_supplied`, `accepted`, `rejection_reason`, actual acquisition time and distance in tooltips/source details.
- **Coverage:** this example has 3 supplied granule days, 1 accepted AM and 1 accepted PM retrieval, out of 3 requested dates. Display these separately rather than saying 3 complete moisture days.
- **Bhagya/Akash:** no drought, saturation or crop-risk class is assigned. Review agronomic interpretation before recommendations; explain quality and missing values without inventing them.

The full optional-dependency suite now has 30 passing tests. New cases cover duplicates, mixed versions/locations, rejected-value consistency, missing dates/passes, and out-of-period records. Remaining work is application integration and scientific review, not downloading this sample again.
