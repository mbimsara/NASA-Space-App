# Data source register

Owner: Matheesha. Documentation support: Tharuka. This register contains candidates, not verified integrations or confirmed specifications.

| Candidate | Intended investigation | Status |
| --- | --- | --- |
| NASA POWER | Weather/climate variables useful for the initial location/time summary | Access, variables, aggregation and resolution to verify |
| GPM | Precipitation observations | Product/version, access, coverage and resolution to verify |
| SMAP | Regional soil-moisture context | Product, quality flags, coverage and field-scale limitations to verify |
| HLS | Vegetation/land-surface history | Access, cloud masking, processing effort and useful time coverage to verify |

Before implementing an adapter, record its official documentation URL, product/version, access/authentication method, permitted use/attribution, variables/units, spatial/temporal resolution, coverage/latency, missing-value/quality flags, aggregation method, retrieval date, cache policy, and known limitations. Do not copy unverified specifications into the UI.

## First integration gate

Demonstrate one successful retrieval for the agreed location and date range, record the request pattern without secrets, inspect missing/quality values, and compare a normalized result with the raw response. Agree with Bhagya how the values enter the water/climate model.

## Provenance rules

Keep source references with analyses and reports. Satellite/regional values do not establish exact field nutrients, weed coverage, or guaranteed yields. Historical data does not by itself predict future weather. Synthetic fixtures under `data/fixtures/` are invented and must never appear as live NASA data.
