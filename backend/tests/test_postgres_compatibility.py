"""Real PostgreSQL opt-in checks, isolated in a generated schema; no migration."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker

from app import main
from app.database.connection import Base, get_db
from app.models.farm import Farm
from app.services.observations import get_observation_adapter
from app.services import rotations
from observation_fixtures import synthetic_observations, DATES

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(not os.environ.get("TEST_POSTGRES_URL"), reason="Real PostgreSQL TEST_POSTGRES_URL not configured")


@pytest.fixture
def postgres(tmp_path, monkeypatch):
    url = os.environ["TEST_POSTGRES_URL"]
    assert url.startswith("postgresql+psycopg://"), "Use an explicit psycopg URL"
    schema = "agrosphere_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema} -clock_timeout=5000"})
    factory = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(main, "engine", engine)
    Base.metadata.create_all(engine)
    def db():
        with factory() as session:
            yield session
    main.app.dependency_overrides[get_db] = db
    raw = json.loads((ROOT / "backend/tests/fixtures/nasa_power.synthetic.json").read_text())
    class Adapter:
        cache_namespace = "synthetic-postgresql-compatibility-only"
        def observe(self, **kwargs):
            return synthetic_observations(raw)
    main.app.dependency_overrides[get_observation_adapter] = Adapter
    catalog = {"schema_version": "0.1", "catalog_version": "synthetic-postgres-v1", "status": "reviewed", "crops": [{
        "id": "test-only", "name": "Fictional compatibility crop", "family": "Test",
        "season_labels": ["maha", "yala"], "water_demand_mm_per_cycle": None,
        "sources": [{"url": "https://example.invalid/synthetic-only"}], "review_status": "approved",
    }]}
    path = tmp_path / "synthetic-catalog.json"
    path.write_text(json.dumps(catalog))
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)
    try:
        yield engine, factory
    finally:
        main.app.dependency_overrides.clear()
        engine.dispose()
        # Only our newly generated schema is ever removed; never public or a DB.
        assert schema.startswith("agrosphere_test_") and len(schema) == 48
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_postgres_complete_synthetic_workflow_and_restart(postgres):
    engine, _ = postgres
    profile = json.loads((ROOT / "data/fixtures/farm.synthetic.json").read_text())
    with TestClient(main.app) as client:
        farm = client.post("/api/v1/farms", json=profile).json()
        farm_path = "/api/v1/farms/" + farm["id"]
        obs_response = client.get(farm_path + "/observations", params=DATES)
        assert obs_response.status_code == 200
        obs = obs_response.json()
        assert obs["data_kind"] == "synthetic"
        assert client.get(farm_path + "/observations", params=DATES).json() == obs
        response = client.post(farm_path + "/rotations", json={
            "input_version": 1, "observation_id": obs["observation_id"], "seasons": 3,
            "season_labels": ["maha", "yala", "maha"], "catalog_version": "synthetic-postgres-v1",
            "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
        })
        assert response.status_code == 201, response.text
        analysis = response.json()
        response = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios", json={"rainfall_change_pct": -20})
        assert response.status_code == 201, response.text
        scenario = response.json()
        candidate = scenario["candidates"][0]["candidate_id"]
        selection = {"analysis_id": analysis["analysis_id"], "scenario_id": scenario["scenario_id"], "candidate_id": candidate}
        assistant = client.post("/api/v1/assistant/messages", json={**selection, "farm_id": farm["id"], "language": "en", "message": "Explain the selected scenario."})
        assert assistant.status_code == 200, assistant.text
        response = client.post(farm_path + "/plans", json={**selection, "expected_input_version": 1})
        assert response.status_code == 201, response.text
        plan_path = "/api/v1/plans/" + response.json()["plan_id"]
        plan = client.get(plan_path).json()
        assert plan["observation_snapshot"] == obs
        assert client.post(plan_path + "/feedback", json={"season_index": 1, "notes": "Explicit synthetic compatibility test"}).status_code == 201
        changed = {**profile, "area_ha": 2.0}
        assert client.patch(farm_path, json={"expected_input_version": 1, "profile": changed}).status_code == 200
        assert client.patch(farm_path, json={"expected_input_version": 1, "profile": changed}).status_code == 409
        assert client.post(farm_path + "/plans", json={**selection, "expected_input_version": 1}).status_code == 409
        assert client.get(plan_path).json() == plan
    engine.dispose()  # New pool/connections, preserving the test schema.
    with TestClient(main.app) as restarted:
        assert restarted.get(plan_path).json() == plan
        assert restarted.get("/api/v1/observations/" + obs["observation_id"]).json() == obs


def test_postgres_conditional_update_serializes_version_changes(postgres):
    _, factory = postgres
    farm_id = str(uuid4())
    with factory.begin() as db:
        db.add(Farm(id=farm_id, input_version=1, profile={"synthetic": True}))
    def conditional_guard():
        with factory.begin() as db:
            return db.execute(update(Farm).where(Farm.id == farm_id, Farm.input_version == 1).values(input_version=Farm.input_version)).rowcount
    with ThreadPoolExecutor(max_workers=1) as executor, factory() as db:
        db.execute(update(Farm).where(Farm.id == farm_id).values(input_version=2))
        pending = executor.submit(conditional_guard)
        db.commit()
        assert pending.result(timeout=10) == 0
