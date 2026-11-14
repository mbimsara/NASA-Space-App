# SMAP integration — access and preparation

Status: public discovery, quality filtering, local file inspection, and nearest-pixel extraction are implemented. A spatially trimmed January 1, 2025 Harmony file has been downloaded and verified. The three-day order remains partly processed; the January 3 download timed out, and January 2 was not yet available at the last check.

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

Remaining: obtain/verify the other subset files, retain download/provenance information, and agree how to present passes and quality limitations in the application. Never treat absent passes as zero moisture.
