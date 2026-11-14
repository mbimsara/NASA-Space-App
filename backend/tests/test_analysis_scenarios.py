"""Climate-scenario API tests for saved rotation analyses; provider access remains mocked."""

import json
from copy import deepcopy

import pytest

from app.database.connection import get_db
from app.main import app
from app.models.rotation import RotationAnalysisSnapshot
from app.services import rotations
from observation_fixtures import DATES


APPROVED_CATALOG = {
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
SEASON_WATER = {
    "demand_low_mm": 400, "demand_nominal_mm": 500, "demand_high_mm": 600,
    "baseline_rainfall_mm": 300, "scenario_rainfall_mm": 300, "irrigation_mm": 100,
    "baseline_available_water_mm": 400,
    "baseline_coverage_low_percent": 400 / 600 * 100, "baseline_coverage_high_percent": 100,
    "available_water_mm": 400, "balance_low_mm": -200, "balance_high_mm": 0,
    "coverage_low_percent": 400 / 600 * 100, "coverage_high_percent": 100,
    "demand_basis": "seasonal_crop_water_need_etc", "model_version": "water-test-v1",
    "source_url": "https://example.org/water", "limitations": [],
}


@pytest.fixture
def approved_catalog(tmp_path, monkeypatch):
    path = tmp_path / "crops.json"
    path.write_text(json.dumps(APPROVED_CATALOG), encoding="utf-8")
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)


def create_analysis(client, farm, catalog_version="approved-test-v1"):
    obs = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES).json()
    response = client.post(f"/api/v1/farms/{farm['id']}/rotations", json={
        "input_version": farm["input_version"], "observation_id": obs["observation_id"],
        "seasons": 3, "season_labels": ["maha", "yala", "maha"],
        "catalog_version": catalog_version,
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
    })
    assert response.status_code == 201
    return obs, response.json()


def with_known_season_water(analysis_id):
    """Simulate a saved analysis whose seasons have dated water inputs."""
    db = next(app.dependency_overrides[get_db]())
    try:
        stored = db.get(RotationAnalysisSnapshot, analysis_id)
        payload = deepcopy(stored.payload)
        for candidate in payload["candidates"]:
            for row in candidate["water_budget_range"]:
                row.update(deepcopy(SEASON_WATER))
        stored.payload = payload
        db.commit()
        return payload
    finally:
        db.close()


def scenario_url(analysis_id):
    return f"/api/v1/analyses/{analysis_id}/scenarios"


def test_recalculates_water_and_scores_from_saved_analysis(client, adapter, farm, approved_catalog):
    obs, analysis = create_analysis(client, farm)
    baseline = with_known_season_water(analysis["analysis_id"])
    saved_observation = client.get(f"/api/v1/observations/{obs['observation_id']}").json()

    response = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": -30})

    assert response.status_code == 201
    result = response.json()
    assert result["kind"] == "hypothetical_rotation_scenario"
    assert result["baseline_analysis_id"] == analysis["analysis_id"]
    assert result["observation_id"] == obs["observation_id"]
    assert result["parameters"] == {"rainfall_change_pct": -30.0}
    assert result["data_kind"] == "synthetic"
    assert result["baseline_outdated"] is False

    row = result["candidates"][0]["water_budget_range"][0]
    assert row["baseline_rainfall_mm"] == 300
    assert row["scenario_rainfall_mm"] == pytest.approx(210)
    assert row["baseline_available_water_mm"] == 400
    assert row["available_water_mm"] == pytest.approx(310)
    assert row["balance_low_mm"] == pytest.approx(-290)
    assert row["coverage_low_percent"] == pytest.approx(310 / 600 * 100)

    candidate = result["candidates"][0]
    components = {c["name"]: c for c in candidate["score_components"]}
    assert components["water_sufficiency"]["value"] == pytest.approx(66.6666666667)
    assert components["scenario_resilience"]["value"] == pytest.approx(310 / 600 * 100)
    assert candidate["score"] == pytest.approx(0.5 * 200 / 3 + 0.3 * 200 / 3 + 0.2 * 310 / 6)

    diff = result["baseline_differences"][candidate["candidate_id"]]
    assert diff["rank_baseline"] == 1 and diff["rank_scenario"] == 1
    assert diff["score_change"] == pytest.approx(candidate["score"] - baseline["candidates"][0]["score"])

    # Original NASA observation is preserved and summarised alongside the scenario.
    assert result["observation_rainfall"]["baseline_rainfall_mm"] == 6
    assert result["observation_rainfall"]["scenario_rainfall_mm"] == 4.2
    assert client.get(f"/api/v1/observations/{obs['observation_id']}").json() == saved_observation
    assert any("not a weather" in item.lower() for item in result["limitations"])


def test_baseline_analysis_snapshot_is_not_mutated(client, adapter, farm, approved_catalog):
    _, analysis = create_analysis(client, farm)
    baseline = with_known_season_water(analysis["analysis_id"])
    client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": 50})

    db = next(app.dependency_overrides[get_db]())
    try:
        assert db.get(RotationAnalysisSnapshot, analysis["analysis_id"]).payload == baseline
    finally:
        db.close()


def test_unknown_season_water_stays_unknown(client, adapter, farm, approved_catalog):
    _, analysis = create_analysis(client, farm)
    response = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": -30})

    assert response.status_code == 201
    candidate = response.json()["candidates"][0]
    assert all(row["scenario_rainfall_mm"] is None for row in candidate["water_budget_range"])
    components = {c["name"]: c for c in candidate["score_components"]}
    assert components["scenario_resilience"]["value"] is None
    assert candidate["score"] == pytest.approx(analysis["candidates"][0]["score"])
    assert response.json()["baseline_differences"][candidate["candidate_id"]]["score_change"] == pytest.approx(0)


def test_scenario_snapshot_is_persisted_and_reopened(client, adapter, farm, approved_catalog):
    _, analysis = create_analysis(client, farm)
    first = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": -30}).json()
    second = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": -30}).json()

    assert first["scenario_id"] != second["scenario_id"]
    reopened = client.get(f"/api/v1/scenarios/{first['scenario_id']}")
    assert reopened.status_code == 200
    assert reopened.json() == first


def test_empty_analysis_is_a_valid_scenario(client, adapter, farm):
    _, analysis = create_analysis(client, farm, catalog_version="0.1-draft-referenced")
    response = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": 20})
    assert response.status_code == 201
    assert response.json()["candidates"] == []
    assert response.json()["baseline_differences"] == {}


def test_outdated_baseline_is_flagged(client, adapter, farm, approved_catalog):
    _, analysis = create_analysis(client, farm)
    profile = client.get(f"/api/v1/farms/{farm['id']}").json()["profile"]
    profile["area_ha"] = profile["area_ha"] + 1
    patched = client.patch(f"/api/v1/farms/{farm['id']}", json={
        "expected_input_version": farm["input_version"], "profile": profile,
    })
    assert patched.status_code == 200

    result = client.post(scenario_url(analysis["analysis_id"]), json={"rainfall_change_pct": -10}).json()
    assert result["baseline_outdated"] is True
    assert result["input_version"] == analysis["input_version"]


@pytest.mark.parametrize(
    ("url", "body", "status_code", "code"),
    [
        ("/api/v1/analyses/missing/scenarios", {"rainfall_change_pct": -30}, 404, "NOT_FOUND"),
        ("/api/v1/analyses/missing/scenarios", {"rainfall_change_pct": -101}, 422, "VALIDATION_ERROR"),
        ("/api/v1/analyses/missing/scenarios", {"rainfall_change_pct": 101}, 422, "VALIDATION_ERROR"),
        ("/api/v1/analyses/missing/scenarios", {}, 422, "VALIDATION_ERROR"),
    ],
)
def test_request_errors(client, url, body, status_code, code):
    response = client.post(url, json=body)
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def test_unknown_scenario_is_404(client):
    response = client.get("/api/v1/scenarios/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
