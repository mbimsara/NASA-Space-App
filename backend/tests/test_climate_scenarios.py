"""Observation rainfall-scenario API tests; provider access remains mocked."""

from copy import deepcopy

from observation_fixtures import DATES


def create_observation(client, farm):
    response = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES)
    assert response.status_code == 200
    return response.json()


def test_scenario_uses_snapshot_and_preserves_baseline(client, adapter, farm):
    observation = create_observation(client, farm)
    saved = deepcopy(observation)
    response = client.post(
        f"/api/v1/observations/{observation['observation_id']}/rainfall-scenarios",
        json={"rainfall_change_pct": -30},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["kind"] == "hypothetical_rainfall_scenario"
    assert result["observation_id"] == observation["observation_id"]
    assert result["farm_id"] == farm["id"]
    assert result["baseline_data_kind"] == "synthetic"
    assert result["parameters"] == {"rainfall_change_pct": -30.0}
    assert result["baseline_source_refs"] == observation["source_refs"]
    assert result["summary"]["baseline_rainfall_mm"] == 6
    assert result["summary"]["scenario_rainfall_mm"] == 4.2
    assert result["summary"]["difference_mm"] == -1.8
    assert "not a weather or yield forecast" in result["limitations"][0]
    assert client.get(f"/api/v1/observations/{observation['observation_id']}").json() == saved


def test_scenario_validates_change_and_unknown_snapshot(client):
    unknown = "/api/v1/observations/00000000-0000-0000-0000-000000000000/rainfall-scenarios"
    assert client.post(unknown, json={"rainfall_change_pct": -30}).status_code == 404
    response = client.post(unknown, json={"rainfall_change_pct": -101})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_scenario_preserves_missing_values(client, adapter, farm):
    adapter.observe.return_value["daily"][1]["precipitation_mm_per_day"] = None
    adapter.observe.return_value["summary"]["precipitation_valid_days"] = 2
    adapter.observe.return_value["summary"]["rainfall_total_mm"] = None
    adapter.observe.return_value["summary"]["rainfall_available_days_mm"] = 4
    observation = create_observation(client, farm)
    response = client.post(
        f"/api/v1/observations/{observation['observation_id']}/rainfall-scenarios",
        json={"rainfall_change_pct": 50},
    )
    result = response.json()
    assert response.status_code == 200
    assert result["summary"]["baseline_rainfall_mm"] is None
    assert result["summary"]["scenario_rainfall_mm"] is None
    assert result["daily"][1]["baseline_mm_per_day"] is None
    assert result["daily"][1]["scenario_mm_per_day"] is None
