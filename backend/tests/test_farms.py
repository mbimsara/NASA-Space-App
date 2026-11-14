
import json
from pathlib import Path


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
