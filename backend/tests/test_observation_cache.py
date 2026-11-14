"""Real SQLite cache tests with synthetic adapters and no live provider access."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from threading import Barrier
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import main
from app.main import app
from app.models.observation import ObservationSnapshot
from app.services import observation_cache
from app.services.observation_cache import (
    ObservationContextConflict, ObservationNotFound, require_observation_for_analysis,
)
from app.services.observations import ObservationServiceUnavailable, get_observation_adapter
from observation_fixtures import DATES, synthetic_observations


def url(farm):
    return f"/api/v1/farms/{farm['id']}/observations"


def snapshot_count():
    with Session(main.engine) as db:
        return db.scalar(select(func.count()).select_from(ObservationSnapshot))


@pytest.fixture
def clock(monkeypatch):
    value = [1000.0]
    monkeypatch.setattr(observation_cache, "time", lambda: value[0])
    return value


def test_repeated_requests_reuse_stable_id_and_complete_payload(client, adapter, farm):
    first = client.get(url(farm), params=DATES)
    original = first.json()
    # Changes to the caller-owned adapter data cannot mutate a saved response.
    adapter.observe.return_value["summary"]["rainfall_total_mm"] = 999
    second = client.get(url(farm), params=DATES)
    assert first.status_code == second.status_code == 200
    assert first.headers["x-observation-cache"] == "MISS"
    assert second.headers["x-observation-cache"] == "HIT"
    assert second.headers["x-observation-expires-at"] == first.headers["x-observation-expires-at"]
    assert second.json() == original
    assert adapter.observe.call_count == 1
    assert snapshot_count() == 1
    stored = client.get(f"/api/v1/observations/{original['observation_id']}")
    assert stored.status_code == 200
    assert stored.json() == original


def test_cached_partial_coverage_and_provenance_survive(client, adapter, farm, provider_fixture):
    provider_fixture["properties"]["parameter"]["T2M"]["20240229"] = -999
    provider_fixture["properties"]["parameter"]["PRECTOTCORR"]["20240301"] = -999
    adapter.observe.return_value = synthetic_observations(provider_fixture)
    first = client.get(url(farm), params=DATES).json()
    adapter.observe.side_effect = ObservationServiceUnavailable("offline")
    cached = client.get(url(farm), params=DATES)
    assert cached.status_code == 200
    assert cached.json() == first
    assert cached.json()["summary"]["rainfall_mm"] is None
    assert cached.json()["coverage"]["available_days"] == 1
    assert cached.json()["missing_data"]["temperature_missing_dates"] == ["2024-02-29"]
    assert cached.json()["data_kind"] == "synthetic"
    assert adapter.observe.call_count == 1


def test_unknown_snapshot_id_is_404(client):
    response = client.get("/api/v1/observations/not-an-existing-id")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Observation not found."}}


def test_expiry_creates_new_snapshot_but_old_id_is_immutable(client, adapter, farm, clock):
    original = client.get(url(farm), params=DATES).json()
    clock[0] += observation_cache.settings.observation_cache_ttl_seconds
    adapter.observe.return_value["retrieved_at"] = "2024-03-03T00:00:00+00:00"
    response = client.get(url(farm), params=DATES)
    assert response.status_code == 200
    assert response.headers["x-observation-cache"] == "MISS"
    refreshed = response.json()
    assert refreshed["observation_id"] != original["observation_id"]
    assert refreshed["retrieved_at"] != original["retrieved_at"]
    assert client.get(url(farm), params=DATES).json() == refreshed
    assert client.get(f"/api/v1/observations/{original['observation_id']}").json() == original
    assert adapter.observe.call_count == 2
    assert snapshot_count() == 2


@pytest.mark.parametrize("change", [
    {"name": "Updated synthetic farm"},
    {"location": {"latitude": 6.12, "longitude": 81.12}},
])
def test_farm_edits_do_not_reuse_older_versions(client, adapter, farm, change):
    old = client.get(url(farm), params=DATES).json()
    new_profile = {**farm["profile"], **change}
    patched = client.patch(f"/api/v1/farms/{farm['id']}", json={
        "expected_input_version": 1, "profile": new_profile,
    })
    assert patched.status_code == 200
    current = client.get(url(farm), params=DATES)
    assert current.status_code == 200
    assert current.json()["input_version"] == 2
    assert current.json()["observation_id"] != old["observation_id"]
    assert current.headers["x-observation-cache"] == "MISS"
    assert client.get(url(farm), params=DATES).json() == current.json()
    assert client.get(f"/api/v1/observations/{old['observation_id']}").json() == old
    location = new_profile["location"]
    assert adapter.observe.call_args.kwargs["latitude"] == location["latitude"]
    assert adapter.observe.call_args.kwargs["longitude"] == location["longitude"]
    assert adapter.observe.call_count == 2
    with Session(main.engine) as db:
        snapshot = db.get(ObservationSnapshot, old["observation_id"])
        assert snapshot.farm_profile == farm["profile"]
        assert snapshot.input_version == 1


def test_same_coordinates_on_different_farms_have_separate_ids(client, adapter, farm):
    other = client.post("/api/v1/farms", json=farm["profile"]).json()
    first = client.get(url(farm), params=DATES).json()
    second = client.get(url(other), params=DATES).json()
    assert first["observation_id"] != second["observation_id"]
    assert first["farm_id"] != second["farm_id"]
    assert adapter.observe.call_count == 2


def test_different_periods_have_separate_cache_entries(client, adapter, farm, provider_fixture):
    first = client.get(url(farm), params=DATES).json()
    provider_fixture["header"]["end"] = "20240229"
    adapter.observe.return_value = synthetic_observations(provider_fixture, end="2024-02-29")
    second = client.get(url(farm), params={**DATES, "end": "2024-02-29"})
    assert second.status_code == 200
    assert second.json()["period"]["end"] == "2024-02-29"
    assert second.json()["observation_id"] != first["observation_id"]
    assert adapter.observe.call_count == 2


def test_provider_namespaces_do_not_share_cache(client, adapter, farm):
    first = client.get(url(farm), params=DATES).json()
    adapter.cache_namespace = "another-synthetic-provider-v1"
    second = client.get(url(farm), params=DATES).json()
    assert second["observation_id"] != first["observation_id"]
    assert adapter.observe.call_count == 2


def test_adapter_without_cache_identity_returns_503(client, farm):
    app.dependency_overrides[get_observation_adapter] = lambda: object()
    response = client.get(url(farm), params=DATES)
    assert response.status_code == 503
    assert snapshot_count() == 0


def test_synthetic_cache_cannot_substitute_for_disabled_real_service(client, adapter, farm):
    first = client.get(url(farm), params=DATES).json()
    app.dependency_overrides[get_observation_adapter] = lambda: None
    response = client.get(url(farm), params=DATES)
    assert response.status_code == 503
    assert client.get(f"/api/v1/observations/{first['observation_id']}").json()["data_kind"] == "synthetic"


def test_failure_during_expired_refresh_does_not_serve_stale_or_replace_snapshot(client, adapter, farm, clock):
    original = client.get(url(farm), params=DATES).json()
    clock[0] += observation_cache.settings.observation_cache_ttl_seconds
    adapter.observe.side_effect = ObservationServiceUnavailable("private-token")
    failed = client.get(url(farm), params=DATES)
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "private-token" not in failed.text
    assert snapshot_count() == 1
    assert client.get(f"/api/v1/observations/{original['observation_id']}").json() == original


def test_failure_on_cache_miss_is_not_persisted(client, adapter, farm):
    normalized = deepcopy(adapter.observe.return_value)
    adapter.observe.side_effect = [ObservationServiceUnavailable(), normalized]
    assert client.get(url(farm), params=DATES).status_code == 503
    assert snapshot_count() == 0
    success = client.get(url(farm), params=DATES)
    assert success.status_code == 200
    assert client.get(url(farm), params=DATES).json() == success.json()
    assert snapshot_count() == 1
    assert adapter.observe.call_count == 2


def test_invalid_provider_response_is_not_cached(client, adapter, farm):
    valid = deepcopy(adapter.observe.return_value)
    adapter.observe.return_value.pop("api")
    assert client.get(url(farm), params=DATES).status_code == 503
    assert snapshot_count() == 0
    adapter.observe.return_value = valid
    assert client.get(url(farm), params=DATES).status_code == 200
    assert snapshot_count() == 1


def test_storage_failure_does_not_return_a_transient_id(client, adapter, farm):
    failure = OperationalError("private-sql", {}, Exception("private-token"))
    with patch.object(Session, "commit", side_effect=failure):
        response = client.get(url(farm), params=DATES)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "observation_id" not in response.json()
    assert "private-token" not in response.text
    assert snapshot_count() == 0
    assert client.get(url(farm), params=DATES).status_code == 200


def test_concurrent_cache_misses_return_one_committed_id(client, adapter, farm):
    barrier = Barrier(2)
    normalized = deepcopy(adapter.observe.return_value)

    def fetch(**kwargs):
        barrier.wait(timeout=10)
        return deepcopy(normalized)

    adapter.observe.side_effect = fetch
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(client.get, url(farm), params=DATES) for _ in range(2)]
        responses = [future.result(timeout=20) for future in futures]
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert snapshot_count() == 1


def test_farm_edit_during_provider_call_keeps_original_snapshot_context(client, adapter, farm):
    original_profile = deepcopy(farm["profile"])
    normalized = deepcopy(adapter.observe.return_value)

    def edit_during_fetch(**kwargs):
        changed = {**original_profile, "area_ha": 2.5}
        response = client.patch(f"/api/v1/farms/{farm['id']}", json={
            "expected_input_version": 1, "profile": changed,
        })
        assert response.status_code == 200
        return normalized

    adapter.observe.side_effect = edit_during_fetch
    response = client.get(url(farm), params=DATES)
    assert response.status_code == 200
    saved = response.json()
    assert saved["input_version"] == 1
    with Session(main.engine) as db:
        row = db.get(ObservationSnapshot, saved["observation_id"])
        assert row.farm_profile == original_profile
        with pytest.raises(ObservationContextConflict):
            require_observation_for_analysis(db, row.id, farm_id=farm["id"], input_version=1)
    adapter.observe.side_effect = None
    newer = client.get(url(farm), params=DATES)
    assert newer.status_code == 200
    assert newer.json()["input_version"] == 2
    assert newer.json()["observation_id"] != saved["observation_id"]


def test_future_analysis_can_resolve_snapshot_and_original_inputs(client, adapter, farm, clock):
    payload = client.get(url(farm), params=DATES).json()
    # Cache expiry changes reuse policy, not the validity of an immutable reference.
    clock[0] += observation_cache.settings.observation_cache_ttl_seconds
    with Session(main.engine) as db:
        row = require_observation_for_analysis(
            db, payload["observation_id"], farm_id=farm["id"], input_version=1,
        )
        assert row.payload == payload
        assert row.farm_profile == farm["profile"]


def test_future_analysis_rejects_unknown_observation(client):
    with Session(main.engine) as db:
        with pytest.raises(ObservationNotFound):
            require_observation_for_analysis(db, "unknown", farm_id="unknown", input_version=1)


@pytest.mark.parametrize("mismatch", ["other_farm", "wrong_version", "outdated_version"])
def test_future_analysis_rejects_wrong_context(client, adapter, farm, mismatch):
    payload = client.get(url(farm), params=DATES).json()
    farm_id, version = farm["id"], 1
    if mismatch == "other_farm":
        farm_id = client.post("/api/v1/farms", json=farm["profile"]).json()["id"]
    elif mismatch == "wrong_version":
        version = 2
    else:
        assert client.patch(f"/api/v1/farms/{farm['id']}", json={
            "expected_input_version": 1, "profile": farm["profile"],
        }).status_code == 200
    with Session(main.engine) as db:
        with pytest.raises(ObservationContextConflict):
            require_observation_for_analysis(
                db, payload["observation_id"], farm_id=farm_id, input_version=version,
            )


def test_persistent_cache_and_id_survive_process_restart(tmp_path, provider_fixture):
    backend = Path(__file__).resolve().parents[1]
    profile = json.loads((backend.parent / "data/fixtures/farm.synthetic.json").read_text())
    request = {"profile": profile, "normalized": synthetic_observations(provider_fixture)}
    env = {
        **os.environ, "PYTHONPATH": str(backend),
        "DATABASE_URL": f"sqlite:///{(tmp_path / 'persistent.db').as_posix()}",
        "OBSERVATION_CACHE_TTL_SECONDS": "86400",
    }
    setup = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from app.services.observations import get_observation_adapter
from services import nasa_power
def no_network(*args, **kwargs):
    raise AssertionError("Live NASA requests are forbidden in offline tests")
nasa_power.urlopen = no_network
request = json.load(sys.stdin)
class Adapter:
    cache_namespace = "synthetic-restart-test"
    def observe(self, **kwargs):
        return request["normalized"]
app.dependency_overrides[get_observation_adapter] = lambda: Adapter()
with TestClient(app) as client:
    farm = client.post("/api/v1/farms", json=request["profile"]).json()
    response = client.get("/api/v1/farms/" + farm["id"] + "/observations", params={
        "start": "2024-02-28", "end": "2024-03-01",
    })
    assert response.status_code == 200
    print(json.dumps({"farm": farm, "observation": response.json()}))
'''
    created = subprocess.run(
        [sys.executable, "-c", setup], input=json.dumps(request), cwd=tmp_path,
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert created.returncode == 0, created.stderr
    restart = '''
import json, sys
from fastapi.testclient import TestClient
from app.main import app
from app.services.observations import get_observation_adapter
from services import nasa_power
def no_network(*args, **kwargs):
    raise AssertionError("No provider access is allowed after restart")
nasa_power.urlopen = no_network
class Adapter:
    cache_namespace = "synthetic-restart-test"
    observe = no_network
app.dependency_overrides[get_observation_adapter] = lambda: Adapter()
saved = json.load(sys.stdin)
with TestClient(app) as client:
    cached = client.get("/api/v1/farms/" + saved["farm"]["id"] + "/observations", params={
        "start": "2024-02-28", "end": "2024-03-01",
    })
    assert cached.status_code == 200
    assert cached.headers["x-observation-cache"] == "HIT"
    assert cached.json() == saved["observation"]
    direct = client.get("/api/v1/observations/" + saved["observation"]["observation_id"])
    assert direct.status_code == 200
    assert direct.json() == saved["observation"]
    assert client.get("/api/v1/farms/" + saved["farm"]["id"]).json() == saved["farm"]
'''
    resumed = subprocess.run(
        [sys.executable, "-c", restart], input=created.stdout, cwd=tmp_path,
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert resumed.returncode == 0, resumed.stderr
