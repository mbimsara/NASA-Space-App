"""Offline HTTP integration tests for the real rotation-engine adapter."""

import json

import pytest

from app.services import rotations
from observation_fixtures import DATES


CATALOG_VERSION = json.loads(rotations.CATALOG_PATH.read_text(encoding="utf-8"))["catalog_version"]


def observation(client, adapter, farm):
    response = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES)
    assert response.status_code == 200
    return response.json()


def request_for(farm, obs, **changes):
    body = {
        "input_version": farm["input_version"],
        "observation_id": obs["observation_id"],
        "seasons": 3,
        "season_labels": ["maha", "yala", "maha"],
        "catalog_version": CATALOG_VERSION,
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
    }
    body.update(changes)
    return body


def endpoint(farm):
    return f"/api/v1/farms/{farm['id']}/rotations"


def test_demo_reviewed_repository_catalog_produces_screening_candidates(client, adapter, farm):
    obs = observation(client, adapter, farm)
    response = client.post(endpoint(farm), json=request_for(farm, obs))

    assert response.status_code == 201
    payload = response.json()
    assert payload["farm_id"] == farm["id"]
    assert payload["observation_id"] == obs["observation_id"]
    assert payload["model_version"] == "rotation-score-0.1"
    assert payload["data_kind"] == "synthetic"
    assert payload["candidates"]
    assert all(candidate["sequence"] for candidate in payload["candidates"])
    assert obs["observation_id"] in payload["source_refs"]
    assert any("not a yield prediction" in item for item in payload["limitations"])


def test_approved_catalog_uses_engine_and_keeps_seasonal_water_unknown(
    client, adapter, farm, tmp_path, monkeypatch,
):
    catalog = {
        "schema_version": "0.1", "catalog_version": "approved-test-v1", "status": "reviewed",
        "crops": [
            {
                "id": "rice", "name": "Rice", "family": "Poaceae",
                "season_labels": ["maha"], "water_demand_mm_per_cycle": 575,
                "sources": [{"url": "https://example.org/rice"}], "review_status": "approved",
            },
            {
                "id": "mung-bean", "name": "Mung bean", "family": "Fabaceae",
                "season_labels": ["yala"], "water_demand_mm_per_cycle": 400,
                "sources": [{"url": "https://example.org/mung"}], "review_status": "approved",
            },
        ],
    }
    path = tmp_path / "crops.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)
    obs = observation(client, adapter, farm)
    body = request_for(farm, obs, catalog_version="approved-test-v1")

    response = client.post(endpoint(farm), json=body)

    assert response.status_code == 201
    candidate = response.json()["candidates"][0]
    assert [step["crop_id"] for step in candidate["sequence"]] == ["rice", "mung-bean", "rice"]
    assert candidate["score"] == pytest.approx(66.6666666667)
    components = {item["name"]: item for item in candidate["score_components"]}
    assert components["water_sufficiency"]["value"] is None
    assert components["crop_diversity"]["value"] == pytest.approx(66.6666666667)
    assert components["crop_diversity"]["effective_weight"] == 1
    assert all(item["baseline_rainfall_mm"] is None for item in candidate["water_budget_range"])
    assert all("dated observation period" in item["limitations"][0] for item in candidate["water_budget_range"])


@pytest.mark.parametrize(
    ("change", "status_code", "code"),
    [
        ({"observation_id": "missing"}, 404, "NOT_FOUND"),
        ({"input_version": 999}, 409, "VERSION_CONFLICT"),
        ({"catalog_version": "wrong"}, 409, "CATALOG_VERSION_CONFLICT"),
        ({"season_labels": ["maha"]}, 422, "VALIDATION_ERROR"),
    ],
)
def test_context_and_request_errors(client, adapter, farm, change, status_code, code):
    obs = observation(client, adapter, farm)
    response = client.post(endpoint(farm), json=request_for(farm, obs, **change))
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def test_analysis_ids_are_immutable_snapshots(client, adapter, farm):
    obs = observation(client, adapter, farm)
    first = client.post(endpoint(farm), json=request_for(farm, obs)).json()
    second = client.post(endpoint(farm), json=request_for(farm, obs)).json()
    assert first["analysis_id"] != second["analysis_id"]


@pytest.mark.parametrize("mode", ["soil_revive", "drought_recovery", "flood_recovery"])
def test_planning_modes_return_explainable_reviewed_evidence(client, adapter, farm, mode):
    obs = observation(client, adapter, farm)
    response = client.post(endpoint(farm), json=request_for(farm, obs, planning_mode=mode))

    assert response.status_code == 201
    payload = response.json()
    assert payload["planning_mode"] == mode
    evidence = [candidate["planning_evidence"] for candidate in payload["candidates"]]
    assert all(item["mode"] == mode for item in evidence)
    assert all(item["source_refs"] for item in evidence)
    assert all("china" not in ref.lower() for item in evidence for ref in item["source_refs"])
    assert all(item["interpretation"] for item in evidence)
    assert all(item["local_checks_required"] for item in evidence)
    if mode == "soil_revive":
        assert evidence[0]["legume_seasons"] == max(item["legume_seasons"] for item in evidence)
    if mode == "drought_recovery":
        demands = [item["mean_crop_water_demand_mm"] for item in evidence]
        assert demands[0] == min(demands)


def test_unknown_planning_mode_is_rejected(client, adapter, farm):
    obs = observation(client, adapter, farm)
    response = client.post(endpoint(farm), json=request_for(farm, obs, planning_mode="magic"))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
