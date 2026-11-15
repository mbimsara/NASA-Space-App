# Data source register

Owner: Matheesha. Documentation support: Tharuka. NASA POWER is integrated through the Python adapter and persisted backend observation cache. The verified local SMAP demonstration series is exposed separately at `GET /api/v1/farms/{farm_id}/soil-moisture`; it returns 404 outside the series distance policy or when the local verified file is unavailable. It is never merged into field soil tests or rotation scores.

## Source selection policy

Use resources listed on the [competition resources page](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/?tab=resources), verified in the browser on 2026-11-14. Per the project owner's instruction, do not add China-related data providers, datasets, locations, or examples. Current integration uses the NASA POWER endpoint and a Sri Lankan demonstration point only. No additional source is approved merely because it appears in an older plan.

| Candidate | Intended investigation | Status |
| --- | --- | --- |
| NASA POWER | Daily T2M and PRECTOTCORR via AG community, UTC | Connected to the farm observations API; live 2025 demo retrieval and cache reuse verified |
| GPM | Precipitation observations | Product/version, access, coverage and resolution to verify |
| SMAP SPL3SMP_E V006 | Regional soil-moisture context | January 2025 Sri Lankan subset automation verified: 31 files, 12 accepted AM / 11 accepted PM retrievals. See [SMAP guide](SMAP.md) |
| Landsat / MODIS / VIIRS | Competition-listed vegetation/land-surface history | Specific products, access and quality processing to verify; HLS is not currently approved |

Additional listed candidates include SRTM, ECOSTRESS, GLDAS/NLDAS, FAO GAEZ, and partner resources Sentinel-2/ERA5. Evaluate geographic coverage and relevance before adding integrations; many other resources on the page focus on the United States.

## Verified NASA POWER adapter

See [usage and verification](NASA_POWER.md). Official documentation: https://power.larc.nasa.gov/docs/services/api/temporal/daily/ . Response metadata identifies MERRA2, API v2.10.3, T2M in C, PRECTOTCORR in mm/day, fill value -999 and UTC. These are gridded source estimates, not direct field measurements. NASA's [meteorology source documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/) confirms a 0.5-degree latitude by 0.625-degree longitude MERRA-2 grid; the adapter reports this only for responses identifying MERRA2 alone, otherwise null. Access used no API key. Project credit and data-reference guidance are recorded in [attribution notes](ATTRIBUTION.md); preserve actual access metadata in published outputs.

Before implementing an adapter, record its official documentation URL, product/version, access/authentication method, permitted use/attribution, variables/units, spatial/temporal resolution, coverage/latency, missing-value/quality flags, aggregation method, retrieval date, cache policy, and known limitations. Do not copy unverified specifications into the UI.

## First integration gate

Demonstrate one successful retrieval for the agreed location and date range, record the request pattern without secrets, inspect missing/quality values, and compare a normalized result with the raw response. Agree with Bhagya how the values enter the water/climate model.

## Provenance rules

The imported POWER module uses the fixed NASA daily point endpoint and no API key. Its
results retain `data_kind: modeled`, source identifiers, API/parameter metadata and UTC
retrieval time. It reports MERRA2 grid resolution only when the source metadata matches;
otherwise resolution is null. Missing days and fill values stay null. The HTTP integration
adds explicit units, aggregation descriptions and coverage; it does not invent dataset versions
or substitute fixtures on provider failure. Immutable database snapshots preserve the original
retrieval metadata and farm version. Fresh-cache lifetime defaults to 24 hours; failed expired
refreshes return 503. Old snapshots remain explicitly readable by ID.

Keep source references with analyses and reports. Satellite/regional values do not establish exact field nutrients, weed coverage, or guaranteed yields. Historical data does not by itself predict future weather. Synthetic fixtures under `data/fixtures/` are invented and must never appear as live NASA data.
