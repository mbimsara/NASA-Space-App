"""SMAP context stays regional, quality-filtered and unavailable outside its point."""

import json
from pathlib import Path

from app.api.routes import soil_moisture as route
from app.services.soil_moisture import load_soil_moisture


def series():
    rejected = {"pass": "AM", "accepted": False, "soil_moisture_m3_m3": None,
                "rejection_reason": "no_valid_geolocation_for_pass"}
    accepted = {"pass": "PM", "accepted": True, "soil_moisture_m3_m3": 0.42,
                "rejection_reason": None, "pixel_latitude": 8.3, "pixel_longitude": 80.4,
                "distance_km": 0.0, "subset_array_index": [0, 0],
                "acquisition_time_utc_raw": "2025-01-01T12:00:00Z", "surface_flag": 128,
                "input_units": "cm**3/cm**3", "retrieval_quality_flag": 8}
    return {
        "schema_version": "0.1", "kind": "smap_surface_soil_moisture_series",
        "data_kind": "satellite_retrieval", "product": "SPL3SMP_E", "version": "006",
        "units": "m3/m3", "requested_point": {"latitude": 8.3, "longitude": 80.4},
        "period": {"start": "2025-01-01", "end": "2025-01-01"}, "max_distance_km": 15,
        "coverage": {"expected_days": 1, "supplied_granule_days": 1, "accepted_AM": 0, "accepted_PM": 1},
        "daily": [{"date": "2025-01-01", "granule_supplied": True, "AM": rejected, "PM": accepted}],
        "limitations": ["AM/PM remain separate; missing/rejected samples are null and are never interpolated or averaged."],
    }


def write(tmp_path: Path) -> Path:
    path = tmp_path / "series.json"
    path.write_text(json.dumps(series()), encoding="utf-8")
    return path


def test_service_preserves_passes_and_disclaims_field_inference(tmp_path, farm):
    class Farm:
        id, input_version, profile = farm["id"], farm["input_version"], farm["profile"]
    result = load_soil_moisture(Farm(), write(tmp_path))
    assert result.daily[0].AM.soil_moisture_m3_m3 is None
    assert result.daily[0].PM.soil_moisture_m3_m3 == 0.42
    assert any("not a field measurement" in item for item in result.limitations)


def test_route_returns_context_and_unknown_farm_is_404(client, farm, tmp_path, monkeypatch):
    path = write(tmp_path)
    original = route.load_soil_moisture
    monkeypatch.setattr(route, "load_soil_moisture", lambda selected: original(selected, path))
    response = client.get(f"/api/v1/farms/{farm['id']}/soil-moisture")
    assert response.status_code == 200
    assert response.json()["coverage"]["accepted_PM"] == 1
    assert client.get("/api/v1/farms/missing/soil-moisture").status_code == 404


def test_route_does_not_reuse_demo_point_for_distant_farm(client, farm, tmp_path, monkeypatch):
    profile = {**farm["profile"], "location": {"latitude": 6.0, "longitude": 79.0}}
    updated = client.patch(f"/api/v1/farms/{farm['id']}", json={
        "expected_input_version": farm["input_version"], "profile": profile,
    })
    assert updated.status_code == 200
    path = write(tmp_path)
    original = route.load_soil_moisture
    monkeypatch.setattr(route, "load_soil_moisture", lambda selected: original(selected, path))
    response = client.get(f"/api/v1/farms/{farm['id']}/soil-moisture")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SMAP_CONTEXT_UNAVAILABLE"
