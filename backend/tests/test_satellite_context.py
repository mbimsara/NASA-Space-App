"""GPM/HLS artifacts are local, provenance-preserving and location-gated."""

import json

from app.api.routes import satellite_context as route
from app.services.satellite_context import load_gpm, load_hls


def _farm(source):
    return type("Farm", (), {
        "id": source["id"], "input_version": source["input_version"], "profile": source["profile"],
    })()


def test_gpm_service_preserves_missing_days(tmp_path, farm):
    payload = {"schema_version": "0.1", "kind": "gpm_imerg_daily_series", "data_kind": "satellite_retrieval",
               "product": "GPM_3IMERGDF", "version": "07", "units": "mm/day",
               "requested_point": farm["profile"]["location"], "period": {"start": "2025-01-01", "end": "2025-01-02"},
               "spatial_resolution_degrees": 0.1, "coverage": {"expected_days": 2, "valid_days": 1},
               "daily": [{"date": "2025-01-01", "precipitation_mm": 4.2}, {"date": "2025-01-02", "precipitation_mm": None}],
               "source_refs": ["NASA GPM_3IMERGDF V07"], "retrieved_at": None,
               "limitations": ["Not a rain gauge."]}
    path = tmp_path / "gpm.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    result = load_gpm(_farm(farm), path)
    assert result.daily[1].precipitation_mm is None


def test_hls_service_preserves_product_and_quality(tmp_path, farm):
    payload = {"schema_version": "0.1", "kind": "hls_vegetation_series", "data_kind": "satellite_retrieval",
               "products": ["HLSL30", "HLSS30"], "version": "2.0", "index": "NDVI",
               "requested_point": farm["profile"]["location"], "spatial_resolution_m": 30,
               "period": {"start": "2025-01-01", "end": "2025-01-01"},
               "coverage": {"supplied_observations": 1, "accepted_observations": 0},
               "observations": [{"date": "2025-01-01", "product": "HLSL30", "ndvi": None,
                                 "cloud_percent": 80, "quality_accepted": False, "rejection_reason": "cloud"}],
               "source_refs": ["NASA HLSL30 V2.0"], "retrieved_at": None,
               "limitations": ["NDVI is not yield."]}
    path = tmp_path / "hls.json"; path.write_text(json.dumps(payload), encoding="utf-8")
    result = load_hls(_farm(farm), path)
    assert result.observations[0].product == "HLSL30" and result.observations[0].ndvi is None


def test_routes_return_explicit_unavailable_codes(client, farm, monkeypatch):
    def unavailable(_farm):
        from app.services.satellite_context import SatelliteContextUnavailable
        raise SatelliteContextUnavailable()
    monkeypatch.setattr(route, "load_gpm", unavailable)
    monkeypatch.setattr(route, "load_hls", unavailable)
    gpm = client.get(f"/api/v1/farms/{farm['id']}/gpm-precipitation")
    hls = client.get(f"/api/v1/farms/{farm['id']}/hls-vegetation")
    assert (gpm.status_code, gpm.json()["error"]["code"]) == (404, "GPM_CONTEXT_UNAVAILABLE")
    assert (hls.status_code, hls.json()["error"]["code"]) == (404, "HLS_CONTEXT_UNAVAILABLE")
