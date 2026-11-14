"""Shared temporary database fixture for farm and observation API tests."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main
from app.main import app
from app.database.connection import Base, get_db
from app.models.farm import Farm
from services import nasa_power
from app.services.observations import ObservationAdapter, get_observation_adapter
from observation_fixtures import synthetic_observations


@pytest.fixture(autouse=True)
def prevent_live_nasa_requests(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Tests must mock NASA access; live requests are not allowed.")

    monkeypatch.setattr(nasa_power, "urlopen", forbidden)


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Separate database for each test
    database_path = tmp_path / "test.db"

    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=test_engine)
    # The lifespan must also use the test DB, never the configured application DB.
    monkeypatch.setattr(main, "engine", test_engine)

    TestingSession = sessionmaker(
        bind=test_engine,
        autoflush=False
    )

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


@pytest.fixture
def provider_fixture():
    return json.loads(
        (Path(__file__).parent / "fixtures/nasa_power.synthetic.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def adapter(client, provider_fixture):
    adapter = Mock(spec=ObservationAdapter)
    adapter.cache_namespace = "synthetic-power-tests-v1"
    adapter.observe.return_value = synthetic_observations(provider_fixture)
    app.dependency_overrides[get_observation_adapter] = lambda: adapter
    return adapter


@pytest.fixture
def farm(client):
    profile_path = Path(__file__).resolve().parents[2] / "data/fixtures/farm.synthetic.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    response = client.post("/api/v1/farms", json=profile)
    assert response.status_code == 201
    return response.json()
