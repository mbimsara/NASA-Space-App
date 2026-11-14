"""All observations and approved crops here are explicitly synthetic fixtures."""
from copy import deepcopy
import json

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import main
from app.main import app
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from app.models.observation import ObservationSnapshot
from app.services.rotations import RotationService, get_rotation_service
from observation_fixtures import DATES


@pytest.fixture
def baseline(client, farm, adapter):
    observation = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES).json()
    request = {"input_version": farm["input_version"], "observation_id": observation["observation_id"],
        "seasons": 3, "catalog_version": "0.1-draft", "season_labels": ["maha", "yala", "maha"],
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2}}
    response = client.post(f"/api/v1/farms/{farm['id']}/rotations", json=request)
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def approved_baseline(client, farm, adapter, tmp_path):
    # Approval belongs only to this invented test catalog, never production data.
    catalog = {"schema_version": "0.1", "catalog_version": "scenario-test", "status": "reviewed",
        "crops": [{"id": "test-crop", "name": "Synthetic test crop", "family": "Test",
            "season_labels": ["maha", "yala"], "water_demand_mm_per_cycle": None,
            "review_status": "approved", "sources": [{"url": "https://example.invalid/test"}]}]}
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    service = RotationService(path)
    app.dependency_overrides[get_rotation_service] = lambda: service
    observation = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES).json()
    request = {"input_version": 1, "observation_id": observation["observation_id"], "seasons": 3,
        "season_labels": ["maha", "yala", "maha"], "catalog_version": "scenario-test",
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2}}
    response = client.post(f"/api/v1/farms/{farm['id']}/rotations", json=request)
    assert response.status_code == 200
    return response.json(), path


def scenario(client, baseline, change=-20):
    return client.post(f"/api/v1/analyses/{baseline['analysis_id']}/scenarios",
        json={"rainfall_change_pct": change})


@pytest.mark.parametrize("change", [-100, -20, 0, 20, 100])
def test_valid_empty_scenario_and_persistence(client, baseline, adapter, change):
    calls = adapter.observe.call_count
    response = scenario(client, baseline, change)
    assert response.status_code == 200
    payload = response.json()
    assert payload["hypothetical"] is True
    assert payload["data_kind"] == "synthetic"
    assert payload["baseline_analysis_id"] == baseline["analysis_id"]
    assert payload["parameters"] == {"rainfall_change_pct": change}
    assert payload["candidates"] == []
    assert payload["baseline_differences"] == {}
    assert payload["reasons"] and payload["limitations"]
    assert adapter.observe.call_count == calls
    with Session(main.engine) as db:
        saved = db.get(ClimateScenario, payload["scenario_id"])
        assert saved.payload == payload
        assert saved.parameters == payload["parameters"]
        assert saved.inputs["baseline"] == baseline


@pytest.mark.parametrize("body", [
    {}, {"rainfall_change_pct": -101}, {"rainfall_change_pct": 101},
    {"rainfall_change_pct": None}, {"rainfall_change_pct": True},
    {"rainfall_change_pct": "-20"}, {"rainfall_change_pct": "NaN"},
    {"rainfall_change_pct": 0, "extra": 1},
])
def test_invalid_parameters_do_not_save(client, baseline, body):
    response = client.post(f"/api/v1/analyses/{baseline['analysis_id']}/scenarios", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    with Session(main.engine) as db:
        assert db.scalar(select(ClimateScenario)) is None


def test_unknown_analysis(client):
    assert scenario(client, {"analysis_id": "unknown"}).status_code == 404


def test_each_post_has_distinct_stable_id(client, baseline):
    first, second = scenario(client, baseline).json(), scenario(client, baseline).json()
    assert first["scenario_id"] != second["scenario_id"]
    with Session(main.engine) as db:
        assert db.get(ClimateScenario, first["scenario_id"]).payload == first
        assert db.get(ClimateScenario, second["scenario_id"]).payload == second


def test_real_engine_replay_preserves_candidate_ids_and_null_water(client, approved_baseline):
    baseline, _ = approved_baseline
    result = scenario(client, baseline).json()
    candidate = result["candidates"][0]
    original = baseline["candidates"][0]
    assert candidate["candidate_id"] == original["candidate_id"]
    assert candidate["sequence"] == original["sequence"]
    assert candidate["score"] == original["score"]
    assert candidate["water_budget"]["deficit_mm"] is None
    assert candidate["water_budget_range"] is None
    assert result["baseline_differences"][candidate["candidate_id"]] == {
        "score_delta": 0, "water_budget_delta": None, "water_budget_range_delta": None}


def test_snapshots_unchanged_even_after_farm_edit_and_cache_expiry(client, baseline, farm):
    with Session(main.engine) as db:
        analysis = db.get(RotationAnalysis, baseline["analysis_id"])
        original_inputs = deepcopy(analysis.inputs)
        observation = db.get(ObservationSnapshot, baseline["observation_id"])
        original_observation = deepcopy(observation.payload)
        observation.expires_at = 0
        db.commit()
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1,
        "profile": farm["profile"] | {"name": "Edited synthetic farm"}})
    result = scenario(client, baseline)
    assert result.status_code == 200
    assert result.json()["input_version"] == 1
    with Session(main.engine) as db:
        analysis = db.get(RotationAnalysis, baseline["analysis_id"])
        assert analysis.payload == baseline and analysis.inputs == original_inputs
        assert db.get(ObservationSnapshot, baseline["observation_id"]).payload == original_observation


def test_uses_saved_catalog_not_current_file(client, approved_baseline):
    baseline, path = approved_baseline
    path.write_text("unavailable current catalog", encoding="utf-8")
    assert scenario(client, baseline).status_code == 200


@pytest.mark.parametrize("corruption,status", [
    ("engine", 503), ("catalog", 503), ("context", 409),
    ("observation_context", 409), ("missing_observation", 503),
    ("model", 503), ("request", 503),
])
def test_unavailable_or_inconsistent_baselines(client, baseline, corruption, status):
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, baseline["analysis_id"])
        if corruption in {"engine", "catalog", "request"}:
            inputs = deepcopy(row.inputs)
            if corruption == "engine":
                inputs["engine_commit"] = "unsupported"
            elif corruption == "catalog":
                del inputs["catalog"]
            else:
                inputs["request"]["catalog_version"] = "mismatch"
            row.inputs = inputs
        elif corruption in {"context", "model"}:
            row.payload = row.payload | ({"farm_id": "mismatch"} if corruption == "context" else {"model_version": "unknown"})
        else:
            snapshot = db.get(ObservationSnapshot, baseline["observation_id"])
            if corruption == "missing_observation":
                db.delete(snapshot)
            else:
                snapshot.input_version += 1
        db.commit()
    result = scenario(client, baseline)
    assert result.status_code == status
    with Session(main.engine) as db:
        assert db.scalar(select(ClimateScenario)) is None


def test_unsupported_water_results_are_not_silently_erased(client, approved_baseline):
    baseline, _ = approved_baseline
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, baseline["analysis_id"])
        payload = deepcopy(row.payload)
        payload["candidates"][0]["water_budget_range"] = [{"unrecognized_future_model": True}]
        row.payload = payload
        db.commit()
    assert scenario(client, baseline).status_code == 503


def test_failed_commit_does_not_return_unsaved_scenario(client, baseline, monkeypatch):
    def fail(*args, **kwargs):
        raise OperationalError("test", {}, Exception("private detail"))
    monkeypatch.setattr(Session, "commit", fail)
    response = scenario(client, baseline)
    assert response.status_code == 503
    assert "private detail" not in response.text
    with Session(main.engine) as db:
        assert db.scalar(select(ClimateScenario)) is None
