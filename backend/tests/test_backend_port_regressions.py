"""Useful legacy-branch regressions adapted to canonical main, never legacy tables."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.routes import rotations as rotation_routes
from app.models.farm import Farm
from app.models.rotation import RotationAnalysisSnapshot
from app.models.scenario import RotationScenarioSnapshot
from app.models.plan import SavedPlanSnapshot
from test_rotations import observation, request_for, endpoint
from test_canonical_assistant_plans import journey, database, body, save, read_saved


@pytest.mark.parametrize("field,value", [
    ("input_version", True), ("input_version", "1"), ("input_version", 1.0),
    ("seasons", "3"), ("seasons", 3.0), ("seasons", True),
])
def test_rotation_integer_fields_do_not_coerce(client, farm, adapter, field, value):
    obs = observation(client, adapter, farm)
    response = client.post(endpoint(farm), json=request_for(farm, obs, **{field: value}))
    assert response.status_code == 422
    assert field in response.json()["error"]["fields"]


def test_farm_edit_after_calculation_before_insert_is_rejected(client, farm, adapter, monkeypatch):
    obs = observation(client, adapter, farm)
    original = rotation_routes.persist_analysis

    def edit_then_persist(db, payload):
        # Separate writer: precisely the gap left by a SELECT/version refresh.
        bind = db.get_bind()
        db.rollback()
        with Session(bind) as writer:
            current = writer.get(Farm, farm["id"])
            current.input_version += 1
            writer.commit()
        return original(db, payload)

    monkeypatch.setattr(rotation_routes, "persist_analysis", edit_then_persist)
    response = client.post(endpoint(farm), json=request_for(farm, obs))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"
    with database() as db:
        assert db.scalars(select(RotationAnalysisSnapshot)).all() == []
        assert db.get(Farm, farm["id"]).input_version == 2
    assert client.get(f"/api/v1/observations/{obs['observation_id']}").json() == obs


def test_successful_analysis_does_not_mutate_farm(client, farm, adapter):
    obs = observation(client, adapter, farm)
    result = client.post(endpoint(farm), json=request_for(farm, obs))
    assert result.status_code == 201
    assert client.get(f"/api/v1/farms/{farm['id']}").json() == farm


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
@pytest.mark.parametrize("method,path", [
    ("POST", "/api/v1/farms"), ("PATCH", "/api/v1/farms/missing"),
    ("POST", "/api/v1/assistant/messages"), ("POST", "/api/v1/farms/missing/plans"),
])
def test_frontend_json_cors_preflight(client, origin, method, path):
    response = client.options(path, headers={"Origin": origin,
        "Access-Control-Request-Method": method, "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert method in response.headers["access-control-allow-methods"]


def test_error_envelope_remains_readable_cross_origin(client):
    response = client.get("/api/v1/plans/missing", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_legacy_count_only_request_does_not_weaken_required_season_labels(client, farm, adapter):
    obs = observation(client, adapter, farm)
    body = request_for(farm, obs)
    del body["season_labels"]
    response = client.post(endpoint(farm), json=body)
    assert response.status_code == 422
    assert "season_labels" in response.json()["error"]["fields"]


@pytest.mark.parametrize("value", [None, "missing"])
def test_missing_observation_is_never_synthetic_fallback(client, farm, value):
    body = request_for(farm, {"observation_id": value})
    response = client.post(endpoint(farm), json=body)
    assert response.status_code == (422 if value is None else 404)
    with database() as db:
        assert db.scalars(select(RotationAnalysisSnapshot)).all() == []


@pytest.mark.parametrize("resource", ["analysis", "scenario", "plan"])
def test_commit_failure_never_returns_an_unsaved_identifier(client, journey, monkeypatch, resource):
    with database() as db:
        before = {model: len(db.scalars(select(model)).all()) for model in
            (RotationAnalysisSnapshot, RotationScenarioSnapshot, SavedPlanSnapshot)}

    def fail(*args, **kwargs):
        raise OperationalError("private-sql", {}, Exception("private-storage-token"))

    with monkeypatch.context() as scoped:
        scoped.setattr(Session, "commit", fail)
        if resource == "analysis":
            response = client.post(endpoint(journey["farm"]), json=request_for(
                journey["farm"], journey["observation"], catalog_version=journey["analysis"]["catalog_version"]))
        elif resource == "scenario":
            response = client.post(f"/api/v1/analyses/{journey['analysis']['analysis_id']}/scenarios",
                json={"rainfall_change_pct": -20})
        else:
            response = save(client, journey)
    assert response.status_code == 503
    assert "private-storage-token" not in response.text
    assert "private-sql" not in response.text
    with database() as db:
        for model, count in before.items():
            assert len(db.scalars(select(model)).all()) == count


@pytest.mark.parametrize("scenario", [False, True])
def test_saved_plan_is_readable_in_a_fresh_process(client, journey, tmp_path, scenario):
    original = read_saved(client, save(client, journey, scenario=scenario))
    with database() as db:
        url = str(db.get_bind().url)
    root = Path(__file__).resolve().parents[2]
    script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from services import nasa_power
def forbidden(*args, **kwargs):
    raise AssertionError("Plan reads must not call NASA")
nasa_power.urlopen = forbidden
expected = json.load(sys.stdin)
with TestClient(app) as client:
    response = client.get('/api/v1/plans/' + expected['plan_id'])
    assert response.status_code == 200, response.text
    assert response.json() == expected
'''
    result = subprocess.run([sys.executable, "-c", script], input=json.dumps(original),
        env={**os.environ, "PYTHONPATH": os.pathsep.join([str(root / "backend"), str(root), str(root / "src")]),
            "DATABASE_URL": url, "NASA_POWER_ENABLED": "false"},
        cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_separate_posts_save_separate_snapshots(client, journey):
    first = read_saved(client, save(client, journey))
    second = read_saved(client, save(client, journey))
    assert first["plan_id"] != second["plan_id"]
    assert first["candidate_snapshot"] == second["candidate_snapshot"]


def test_saved_plan_ignores_current_catalog_and_new_model_payloads(client, journey, tmp_path, monkeypatch):
    plan = read_saved(client, save(client, journey, scenario=True))
    from app.services import rotations
    monkeypatch.setattr(rotations, "CATALOG_PATH", tmp_path / "missing-catalog.json")
    with database() as db:
        row = db.get(RotationAnalysisSnapshot, journey["analysis"]["analysis_id"])
        payload = deepcopy(row.payload)
        payload["model_version"] = "changed-after-plan-save"
        row.payload = payload
        db.commit()
    assert client.get(f"/api/v1/plans/{plan['plan_id']}").json() == plan


def test_farm_only_answer_retains_selected_scenario_disclosure_without_invented_citations(client, journey):
    response = client.post("/api/v1/assistant/messages", json=body(
        journey, scenario=True, message="What is the farm name?"))
    assert response.status_code == 200
    result = response.json()
    assert any("hypothetical" in item for item in result["limitations"])
    assert any("synthetic demonstration" in item for item in result["limitations"])
    assert result["source_ids"] == []  # Farmer-entered name is not a NASA fact.
    assert result["context"]["scenario_id"] == journey["scenario"]["scenario_id"]
