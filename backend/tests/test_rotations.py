"""Synthetic integration fixtures; no live providers or production approvals."""
import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import main
from app.main import app
from app.models.rotation import RotationAnalysis
from app.models.observation import ObservationSnapshot
from app.models.farm import Farm
from app.services.rotations import RotationService, get_rotation_service
from observation_fixtures import DATES


@pytest.fixture
def context(client, farm, adapter):
    observation = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES).json()
    request = {"input_version": 1, "observation_id": observation["observation_id"],
        "seasons": 3, "catalog_version": "0.1-draft",
        "priority_weights": {"water": 1, "soil": 1, "climate": 1}}
    return farm, observation, request


def post(client, context, **changes):
    farm, _, body = context
    return client.post(f"/api/v1/farms/{farm['id']}/rotations", json=body | changes)


def test_empty_analysis_is_persisted_with_original_inputs(client, context):
    result = post(client, context)
    assert result.status_code == 200
    payload = result.json()
    assert payload["candidates"] == []
    assert payload["reasons"]
    assert payload["data_kind"] == "synthetic"
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, payload["analysis_id"])
        assert row.payload == payload
        assert row.inputs["farm_profile"] == context[0]["profile"]
        assert row.inputs["engine_commit"]
    assert client.get(f"/api/v1/observations/{context[1]['observation_id']}").json() == context[1]
    assert client.get(f"/api/v1/farms/{context[0]['id']}").json() == context[0]


@pytest.mark.parametrize("changes,status", [
    ({"input_version": 2}, 409), ({"observation_id": "missing"}, 404),
    ({"observation_id": None}, 422), ({"catalog_version": "unknown"}, 422),
    ({"seasons": 2}, 422), ({"seasons": 6}, 422), ({"seasons": True}, 422),
    ({"season_labels": ["maha"]}, 422),
    ({"season_labels": ["invalid"] * 3}, 422),
    ({"priority_weights": {"water": 0, "soil": 0, "climate": 0}}, 422),
])
def test_invalid_context_and_fields(client, context, changes, status):
    assert post(client, context, **changes).status_code == status
    with Session(main.engine) as db:
        assert db.scalar(select(RotationAnalysis)) is None


def test_unknown_farm(client, context):
    assert client.post("/api/v1/farms/missing/rotations", json=context[2]).status_code == 404


def test_wrong_farm_observation(client, context):
    other = client.post("/api/v1/farms", json=context[0]["profile"]).json()
    assert client.post(f"/api/v1/farms/{other['id']}/rotations", json=context[2]).status_code == 409


def test_outdated_observation(client, context):
    farm = context[0]
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1, "profile": farm["profile"]})
    assert post(client, context, input_version=2).status_code == 409


@pytest.fixture
def approved_service(tmp_path, client):
    document = {"schema_version": "0.1", "catalog_version": "test-approved", "status": "reviewed",
        "crops": [{"id": crop_id, "name": crop_id, "family": "test-family",
            "season_labels": seasons, "water_demand_mm_per_cycle": None,
            "sources": [{"url": "https://example.invalid/test-only"}], "review_status": "approved"}
            for crop_id, seasons in [("test-maha", ["maha"]), ("test-yala", ["yala"])]]}
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    service = RotationService(path)
    app.dependency_overrides[get_rotation_service] = lambda: service
    return service, document


def test_actual_engine_season_checks_scores_and_stable_ids(client, context, approved_service):
    payload = post(client, context, catalog_version="test-approved", season_labels=["maha", "yala", "maha"]).json()
    candidate = payload["candidates"][0]
    assert [step["crop_id"] for step in candidate["sequence"]] == ["test-maha", "test-yala", "test-maha"]
    assert candidate["score"] == pytest.approx(200 / 3)
    assert candidate["water_budget"]["deficit_mm"] is None
    assert candidate["score_components"][0]["value"] is None
    assert all(check["passed"] for check in candidate["constraint_checks"])
    with Session(main.engine) as db:
        assert db.get(RotationAnalysis, payload["analysis_id"]).payload["candidates"][0]["candidate_id"] == candidate["candidate_id"]


def test_exclusions_remove_sequences(client, context, approved_service):
    with Session(main.engine) as db:
        farm = db.get(Farm, context[0]["id"])
        farm.profile = farm.profile | {"excluded_crop_ids": ["test-yala"]}
        db.commit()
    payload = post(client, context, catalog_version="test-approved", season_labels=["maha", "yala", "maha"]).json()
    assert payload["candidates"] == []
    assert any("yala" in reason for reason in payload["reasons"])


def test_pending_catalog_blocks_individually_approved_entries(client, context, approved_service):
    service, document = approved_service
    document["status"] = "research_pending"
    service.catalog_path.write_text(json.dumps(document), encoding="utf-8")
    assert post(client, context, catalog_version="test-approved", season_labels=["maha"] * 3).json()["candidates"] == []


def test_unavailable_weighted_scores_remain_null(client, context, approved_service):
    result = post(client, context, catalog_version="test-approved", season_labels=["maha"] * 3,
        priority_weights={"water": 1, "soil": 0, "climate": 0}).json()
    assert result["candidates"][0]["score"] is None


def test_expired_snapshot_is_still_valid(client, context):
    with Session(main.engine) as db:
        db.get(ObservationSnapshot, context[1]["observation_id"]).expires_at = 0
        db.commit()
    assert post(client, context).status_code == 200


def test_farm_edit_during_analysis_rejected(client, context, monkeypatch):
    from app.services import rotations
    original = rotations.RotationService.analyze
    def edit(self, *args):
        result = original(self, *args)
        with Session(main.engine) as db:
            farm = db.get(Farm, context[0]["id"])
            farm.input_version += 1
            db.commit()
        return result
    monkeypatch.setattr(rotations.RotationService, "analyze", edit)
    assert post(client, context).status_code == 409
    with Session(main.engine) as db:
        assert db.scalar(select(RotationAnalysis)) is None


def test_corrupt_catalog_returns_safe_error(client, context, approved_service):
    approved_service[0].catalog_path.write_text("invalid JSON", encoding="utf-8")
    result = post(client, context)
    assert result.status_code == 503
    assert result.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_storage_failure_never_returns_unsaved_analysis(client, context, monkeypatch):
    from sqlalchemy.exc import OperationalError
    def fail(*args, **kwargs):
        raise OperationalError("test statement", {}, Exception("private storage detail"))
    monkeypatch.setattr(Session, "commit", fail)
    response = post(client, context)
    assert response.status_code == 503
    assert "private storage detail" not in response.text
    with Session(main.engine) as db:
        assert db.scalar(select(RotationAnalysis)) is None


def test_saved_analysis_survives_farm_edit(client, context):
    original = post(client, context).json()
    farm = context[0]
    changed = farm["profile"] | {"name": "Changed synthetic farm"}
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1, "profile": changed})
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, original["analysis_id"])
        assert row.payload == original
        assert row.input_version == 1
        assert row.inputs["farm_profile"] == farm["profile"]
