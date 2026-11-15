# GPM IMERG and HLS integration

AgroSphere keeps these optional NASA layers separate from the existing NASA
POWER baseline and SMAP surface-moisture context. An unavailable layer returns
an explicit `404` and never falls back to invented values.

## Selected NASA products

| Context | Product | Version/resolution | Intended use |
|---|---|---|---|
| Satellite rainfall | GPM IMERG Final Daily (`GPM_3IMERGDF`) | V07, 0.1 degree, daily | Independent precipitation context; not a rain gauge and not silently substituted for POWER |
| Surface reflectance | HLS Landsat 30 m (`HLSL30`) and Sentinel-2 30 m (`HLSS30`) | V2.0, 30 m | Quality-screened NDVI/greenness context; not crop identity, yield, nutrients, or proof of plant health |

Official references:

- NASA GES DISC, [GPM IMERG Final precipitation products](https://disc.gsfc.nasa.gov/datasets?keywords=GPM_3IMERGDF&page=1)
- NASA Earthdata, [Harmonized Landsat Sentinel-2](https://www.earthdata.nasa.gov/data/projects/hls)
- HLS project, [vegetation-index user guide](https://lpdaac.usgs.gov/documents/1372/HLS-VI_User_Guide_V2.pdf)

These products use NASA Earthdata authentication. Credentials and tokens must
remain outside the repository.

## Reproducible normalization

The repository deliberately does not commit large or account-derived downloads.
After obtaining an export from the official provider, normalize it locally:

```powershell
.venv312\Scripts\python.exe -m scripts.normalize_gpm --input path\gpm.csv --output .cache\gpm\series.json --latitude 8.3 --longitude 80.4 --start 2025-01-01 --end 2025-01-31 --source-ref "NASA GPM_3IMERGDF V07 Earthdata export"
.venv312\Scripts\python.exe -m scripts.normalize_hls --input path\hls.csv --output .cache\hls\series.json --latitude 8.3 --longitude 80.4 --source-ref "NASA HLS V2.0 Earthdata export"
```

The GPM CSV columns are `date,precipitation_mm`. The HLS CSV columns are
`date,product,ndvi,cloud_percent,quality_accepted,rejection_reason`. Rejected
HLS samples must have an empty NDVI. Missing GPM dates become explicit nulls.

## API and safety behavior

- `GET /api/v1/farms/{farm_id}/gpm-precipitation`
- `GET /api/v1/farms/{farm_id}/hls-vegetation`

The API validates the artifact schema and compares its requested point to the
farm. GPM point artifacts are limited to 8 km and HLS point artifacts to 1 km;
outside those bounds the endpoint returns `*_CONTEXT_UNAVAILABLE`. The frontend
shows a card only when a verified artifact is available. POWER remains the
rotation engine's historical weather input until a separately reviewed fusion
rule is implemented.
