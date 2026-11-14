# SMAP integration — access and preparation

Status: public metadata discovery and a pixel-quality filter are implemented. Authenticated download, HDF5 extraction, and live soil-moisture validation are pending. No actual soil-moisture result is claimed yet.

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

`python -m unittest discover -s tests -v` currently runs 25 tests. SMAP tests use synthetic pixel values and mocked metadata, covering quality codes, missing values, coordinates/dates and inclusive-date boundary filtering. The public discovery call was also verified live. Once the account/subset is ready, install a documented HDF5 reader in a project-local environment and verify the science extraction against an actual subset before integrating soil-moisture charts.
