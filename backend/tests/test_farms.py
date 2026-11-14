
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import Base, get_db
from app.models.farm import Farm


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "fixtures"
    / "farm.synthetic.json"
)


def sample_farm():
    return json.loads(
        FIXTURE_PATH.read_text(encoding="utf-8")
    )


@pytest.fixture
def client(tmp_path):
    # Separate database for each test
    database_path = tmp_path / "test.db"

    test_engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=test_engine)

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


def test_create_farm(client):
    response = client.post(
        "/api/v1/farms",
        json=sample_farm()
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["input_version"] == 1


def test_get_farm(client):
    created = client.post(
        "/api/v1/farms",
        json=sample_farm()
    )

    farm_id = created.json()["id"]

    response = client.get(
        f"/api/v1/farms/{farm_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == farm_id


def test_update_farm(client):
    created = client.post(
        "/api/v1/farms",
        json=sample_farm()
    )

    farm_id = created.json()["id"]

    updated_profile = sample_farm()
    updated_profile["area_ha"] = 2.5

    response = client.patch(
        f"/api/v1/farms/{farm_id}",
        json={
            "expected_input_version": 1,
            "profile": updated_profile
        }
    )

    assert response.status_code == 200
    assert response.json()["input_version"] == 2
    assert response.json()["profile"]["area_ha"] == 2.5


def test_invalid_farm_area(client):
    farm = sample_farm()
    farm["area_ha"] = -5

    response = client.post(
        "/api/v1/farms",
        json=farm
    )

    assert response.status_code == 422


def test_nonexistent_farm(client):
    response = client.get(
        "/api/v1/farms/nonexistent-id"
    )

    assert response.status_code == 404


def test_version_conflict(client):
    created = client.post(
        "/api/v1/farms",
        json=sample_farm()
    )

    farm_id = created.json()["id"]

    update_body = {
        "expected_input_version": 1,
        "profile": sample_farm()
    }

    first_update = client.patch(
        f"/api/v1/farms/{farm_id}",
        json=update_body
    )

    assert first_update.status_code == 200

    second_update = client.patch(
        f"/api/v1/farms/{farm_id}",
        json=update_body
    )

    assert second_update.status_code == 409
