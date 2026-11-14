"""Regressions for Shehani's real client contracts; all data is synthetic."""
import pytest

from test_scenarios import baseline, approved_baseline


@pytest.mark.parametrize("language", ["si", "ta"])
def test_assistant_language_code_enables_frontend_english_retry(client, baseline, language):
    response = client.post("/api/v1/assistant/messages", json={
        "farm_id": baseline["farm_id"], "analysis_id": baseline["analysis_id"],
        "language": language, "message": "Explain the farm area",
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_LANGUAGE"
    assert "language" in response.json()["error"]["fields"]


def test_other_validation_keeps_existing_code(client):
    response = client.post("/api/v1/assistant/messages", json={})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("method,path", [
    ("POST", "/api/v1/farms"), ("PATCH", "/api/v1/farms/unknown"),
    ("POST", "/api/v1/assistant/messages"),
])
def test_frontend_json_cors_preflight(client, method, path):
    response = client.options(path, headers={"Origin": "http://localhost:5173",
        "Access-Control-Request-Method": method, "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert method in response.headers["access-control-allow-methods"]


def test_error_envelope_is_also_readable_cross_origin(client):
    response = client.get("/api/v1/plans/unknown", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_frontend_count_only_rotation_accepts_empty_catalog(client, baseline):
    # Exactly the count-only body sent by RotationPage (no guessed calendar).
    response = client.post(f"/api/v1/farms/{baseline['farm_id']}/rotations", json={
        "input_version": baseline["input_version"], "observation_id": baseline["observation_id"],
        "seasons": 3, "catalog_version": baseline["catalog_version"],
        "priority_weights": {"water": .5, "soil": .3, "climate": .2},
    })
    assert response.status_code == 200
    assert response.json()["candidates"] == []
    assert response.json()["reasons"]


def test_invalid_null_observation_is_not_replaced_by_fake_data(client, baseline):
    response = client.post(f"/api/v1/farms/{baseline['farm_id']}/rotations", json={
        "input_version": 1, "observation_id": None, "seasons": 3,
        "catalog_version": baseline["catalog_version"],
        "priority_weights": {"water": .5, "soil": .3, "climate": .2},
    })
    assert response.status_code == 422
    assert "observation_id" in response.json()["error"]["fields"]
