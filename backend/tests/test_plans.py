"""Saved-plan integration tests using explicitly synthetic catalogs and NASA data."""
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

from app import main
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.plan import SavedPlan
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from test_scenarios import approved_baseline, baseline  # Shared synthetic fixtures.


def request_for(analysis, **changes):
    return {"analysis_id": analysis["analysis_id"], "candidate_id": analysis["candidates"][0]["candidate_id"],
        "expected_input_version": analysis["input_version"], **changes}


def save(client, analysis, **changes):
    return client.post(f"/api/v1/farms/{analysis['farm_id']}/plans", json=request_for(analysis, **changes))


def assert_no_plans():
    with Session(main.engine) as db:
        assert db.scalar(select(SavedPlan)) is None


def test_save_baseline_and_retrieve(client, approved_baseline, adapter):
    analysis, _ = approved_baseline
    calls = adapter.observe.call_count
    result = save(client, analysis)
    assert result.status_code == 201
    assert set(result.json()) == {"plan_id"}
    response = client.get(f"/api/v1/plans/{result.json()['plan_id']}")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    plan = response.json()
    assert plan["analysis_id"] == analysis["analysis_id"]
    assert plan["candidate_snapshot"] == analysis["candidates"][0]
    assert plan["scenario_id"] is None and plan["scenario_snapshot"] is None
    assert plan["observation_id"] == analysis["observation_id"]
    assert plan["analysis_snapshot"]["data_kind"] == "synthetic"
    assert plan["analysis_snapshot"]["source_refs"] == analysis["source_refs"]
    with Session(main.engine) as db:
        row = db.get(SavedPlan, plan["plan_id"])
        assert row.provenance["baseline"] == analysis
        assert row.provenance["rotation_inputs"]["farm_profile"] == plan["input_snapshot"]
        assert db.get(RotationAnalysis, analysis["analysis_id"]).payload == analysis
    assert adapter.observe.call_count == calls


def test_save_scenario_candidate_and_metadata(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    response = save(client, analysis, scenario_id=scenario["scenario_id"])
    assert response.status_code == 201
    plan = client.get(f"/api/v1/plans/{response.json()['plan_id']}").json()
    assert plan["candidate_snapshot"] == scenario["candidates"][0]
    assert plan["scenario_snapshot"] == scenario
    assert plan["scenario_snapshot"]["hypothetical"] is True
    assert plan["analysis_snapshot"]["limitations"] == scenario["limitations"]
    assert plan["analysis_snapshot"]["assumptions"] == scenario["assumptions"]
    with Session(main.engine) as db:
        assert db.get(ClimateScenario, scenario["scenario_id"]).payload == scenario


@pytest.mark.parametrize("resource", ["farm", "analysis", "scenario", "candidate"])
def test_unknown_resources(client, approved_baseline, resource):
    analysis, _ = approved_baseline
    if resource == "farm":
        response = client.post("/api/v1/farms/missing/plans", json=request_for(analysis))
    else:
        response = save(client, analysis, **{resource + "_id": "missing"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert_no_plans()


def test_unknown_plan(client):
    assert client.get("/api/v1/plans/missing").status_code == 404


@pytest.mark.parametrize("changes", [
    {"analysis_id": ""}, {"candidate_id": "  "}, {"scenario_id": ""},
    {"expected_input_version": 0}, {"expected_input_version": True},
    {"expected_input_version": "1"}, {"expected_input_version": 1.5},
    {"analysis_id": None}, {"candidate_id": None}, {"extra": True},
])
def test_invalid_requests(client, approved_baseline, changes):
    analysis, _ = approved_baseline
    assert save(client, analysis, **changes).status_code == 422
    assert_no_plans()


def test_missing_required_fields(client, farm):
    assert client.post(f"/api/v1/farms/{farm['id']}/plans", json={}).status_code == 422


def test_wrong_farm_analysis(client, approved_baseline, farm):
    analysis, _ = approved_baseline
    other = client.post("/api/v1/farms", json=farm["profile"]).json()
    response = client.post(f"/api/v1/farms/{other['id']}/plans", json=request_for(analysis))
    assert response.status_code == 409
    assert_no_plans()


def test_wrong_analysis_scenario(client, approved_baseline):
    analysis, _ = approved_baseline
    with Session(main.engine) as db:
        request = deepcopy(db.get(RotationAnalysis, analysis["analysis_id"]).inputs["request"])
    other = client.post(f"/api/v1/farms/{analysis['farm_id']}/rotations", json=request).json()
    scenario = client.post(f"/api/v1/analyses/{other['analysis_id']}/scenarios",
        json={"rainfall_change_pct": 10}).json()
    assert save(client, analysis, scenario_id=scenario["scenario_id"]).status_code == 409
    assert_no_plans()


def test_empty_analysis_never_creates_candidate(client, baseline):
    response = client.post(f"/api/v1/farms/{baseline['farm_id']}/plans", json={
        "analysis_id": baseline["analysis_id"], "candidate_id": "invented", "expected_input_version": 1})
    assert response.status_code == 404
    assert_no_plans()


@pytest.mark.parametrize("expected", [1, 2])
def test_outdated_request_or_analysis(client, approved_baseline, farm, expected):
    analysis, _ = approved_baseline
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1, "profile": farm["profile"]})
    assert save(client, analysis, expected_input_version=expected).status_code == 409
    assert_no_plans()


def test_snapshot_preserved_after_farm_catalog_and_model_changes(client, approved_baseline, farm, monkeypatch):
    analysis, path = approved_baseline
    plan_id = save(client, analysis).json()["plan_id"]
    original = client.get(f"/api/v1/plans/{plan_id}").json()
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1,
        "profile": farm["profile"] | {"name": "Edited synthetic farm"}})
    path.write_text("unavailable catalog", encoding="utf-8")
    from app.services.rotations import RotationService
    def fail(*args, **kwargs):
        raise AssertionError("Plan reads must not rerun calculations")
    monkeypatch.setattr(RotationService, "analyze", fail)
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, analysis["analysis_id"])
        row.payload = row.payload | {"model_version": "changed-model"}
        db.commit()
    assert client.get(f"/api/v1/plans/{plan_id}").json() == original
    assert client.get(f"/api/v1/observations/{analysis['observation_id']}").status_code == 200
    assert client.get(f"/api/v1/farms/{farm['id']}").json()["input_version"] == 2


def test_farm_edit_during_save_is_rejected(client, approved_baseline, monkeypatch):
    from app.api.routes import plans
    analysis, _ = approved_baseline
    original = plans.prepare_plan
    def edit(*args):
        result = original(*args)
        with Session(main.engine) as db:
            db.get(Farm, analysis["farm_id"]).input_version += 1
            db.commit()
        return result
    monkeypatch.setattr(plans, "prepare_plan", edit)
    assert save(client, analysis).status_code == 409
    assert_no_plans()


@pytest.mark.parametrize("corruption", ["pending", "draft", "excluded", "sequence", "observation"])
def test_inconsistent_or_unapproved_saved_data_is_rejected(client, approved_baseline, corruption):
    analysis, _ = approved_baseline
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, analysis["analysis_id"])
        inputs = deepcopy(row.inputs)
        if corruption == "pending":
            inputs["catalog"]["status"] = "research_pending"
        elif corruption == "draft":
            inputs["catalog"]["crops"][0]["review_status"] = "draft"
        elif corruption == "excluded":
            inputs["farm_profile"]["excluded_crop_ids"] = ["test-crop"]
        elif corruption == "sequence":
            payload = deepcopy(row.payload)
            payload["candidates"][0]["sequence"][0]["crop_id"] = "unknown-crop"
            row.payload = payload
        else:
            db.get(ObservationSnapshot, analysis["observation_id"]).input_version += 1
        row.inputs = inputs
        db.commit()
    assert save(client, analysis).status_code == 409
    assert_no_plans()


def test_storage_failure_is_safe_and_does_not_save(client, approved_baseline, monkeypatch):
    analysis, _ = approved_baseline
    def fail(*args, **kwargs):
        raise OperationalError("private statement", {}, Exception("private detail"))
    monkeypatch.setattr(Session, "commit", fail)
    response = save(client, analysis)
    assert response.status_code == 503
    assert "private detail" not in response.text
    assert_no_plans()


def test_plan_survives_process_restart(client, approved_baseline, tmp_path):
    analysis, _ = approved_baseline
    plan_id = save(client, analysis).json()["plan_id"]
    original = client.get(f"/api/v1/plans/{plan_id}").json()
    backend = Path(__file__).resolve().parents[1]
    script = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from services import nasa_power
def forbidden(*args, **kwargs):
    raise AssertionError("Plan reads must not call NASA")
nasa_power.urlopen = forbidden
saved = json.load(sys.stdin)
with TestClient(app) as client:
    result = client.get('/api/v1/plans/' + saved['plan_id'])
    assert result.status_code == 200, result.text
    assert result.json() == saved
'''
    result = subprocess.run([sys.executable, "-c", script], input=json.dumps(original),
        env={**os.environ, "PYTHONPATH": str(backend), "DATABASE_URL": str(main.engine.url)},
        cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_scenario_selection_never_falls_back_to_baseline(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    with Session(main.engine) as db:
        row = db.get(ClimateScenario, scenario["scenario_id"])
        row.payload = row.payload | {"candidates": []}
        db.commit()
    assert save(client, analysis, scenario_id=scenario["scenario_id"]).status_code == 404
    assert_no_plans()


def test_corrupt_scenario_context_is_rejected(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    with Session(main.engine) as db:
        row = db.get(ClimateScenario, scenario["scenario_id"])
        row.payload = row.payload | {"input_version": 2}
        db.commit()
    assert save(client, analysis, scenario_id=scenario["scenario_id"]).status_code == 409
    assert_no_plans()


def test_missing_observation_returns_safe_unavailable(client, approved_baseline):
    analysis, _ = approved_baseline
    with Session(main.engine) as db:
        db.delete(db.get(ObservationSnapshot, analysis["observation_id"]))
        db.commit()
    assert save(client, analysis).status_code == 503
    assert_no_plans()


def test_repeated_posts_create_separate_plans(client, approved_baseline):
    analysis, _ = approved_baseline
    first, second = save(client, analysis).json(), save(client, analysis, scenario_id=None).json()
    assert first["plan_id"] != second["plan_id"]
    for saved in (first, second):
        assert client.get(f"/api/v1/plans/{saved['plan_id']}").status_code == 200
