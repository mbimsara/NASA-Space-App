# Data source register

Owner: Matheesha. Documentation support: Tharuka. The backend now integrates Matheesha's NASA POWER module from `matheesha/nasa-power-integration` at commit `c580b4fc620212f5450e388ed951e7cef5c014f6`. Live adapter retrieval and persisted API cache reuse were verified in an isolated database on 2026-11-14; see the backend verification record. Other products below are not integrated into this observations route.

| Candidate | Intended investigation | Status |
| --- | --- | --- |
| NASA POWER | Daily T2M and PRECTOTCORR, AG community, UTC | Existing fetch/normalize adapter connected to farm observations API; see [backend instructions](../backend/README.md#climate-observations) |
| GPM | Precipitation observations | Product/version, access, coverage and resolution to verify |
| SMAP | Regional soil-moisture context | Separate pipeline exists on Matheesha's branch; not exposed by this route |
| HLS | Vegetation/land-surface history | Access, cloud masking, processing effort and useful time coverage to verify |

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
