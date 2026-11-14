"""Offline integration tests. Every invented measurement is labeled synthetic."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from http.client import IncompleteRead
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from uuid import UUID

import pytest

from app.main import app
from app.services import observations
from app.services.observations import (
    NASAPowerObservationAdapter, ObservationAdapter, ObservationServiceUnavailable,
    get_observation_adapter,
)
from services import nasa_power


from observation_fixtures import DATES, RETRIEVED_AT, SYNTHETIC_URL, synthetic_observations


def endpoint(farm):
    return f"/api/v1/farms/{farm['id']}/observations"


def test_valid_request_and_provenance(client, adapter, farm):
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 200
    payload = response.json()
    assert UUID(payload["observation_id"])
    assert payload["farm_id"] == farm["id"]
    assert payload["input_version"] == 1
    assert payload["data_kind"] == "synthetic"
    assert payload["provider"] == "NASA POWER"
    assert payload["period"] == DATES
    assert datetime.fromisoformat(payload["retrieved_at"]) == datetime.fromisoformat(RETRIEVED_AT)
    assert payload["source_refs"] == ["synthetic-test-not-nasa"]
    assert payload["api"] == {"version": "synthetic-test-version"}
    assert payload["source_url"] == SYNTHETIC_URL
    assert payload["parameter_metadata"]["PRECTOTCORR"]["units"] == "mm/day"
    assert payload["spatial_resolution"] is None  # Never guess resolution for an unknown source.
    assert payload["time_standard"] == "UTC"
    assert payload["units"]["rainfall_mm"] == "mm"
    assert payload["units"]["mean_temperature_c"] == "C"
    assert payload["aggregation_method"]["rainfall_mm"]
    assert payload["coverage"] == {
        "expected_days": 3, "available_days": 3,
        "temperature_valid_days": 3, "precipitation_valid_days": 3,
    }
    assert payload["summary"]["rainfall_mm"] == 6
    assert payload["summary"]["rainfall_total_mm"] == 6
    assert payload["summary"]["mean_temperature_c"] == 22
    assert len(payload["daily"]) == 3
    assert len(payload["monthly"]) == 2
    assert payload["daily"][1]["date"] == "2024-02-29"
    assert any("Invented test" in item for item in payload["limitations"])


def test_uses_saved_coordinates_and_version_without_mutating_farm(client, adapter, farm):
    profile = deepcopy(farm["profile"])
    profile["location"] = {"latitude": 6.12, "longitude": 81.12}
    updated = client.patch(f"/api/v1/farms/{farm['id']}", json={
        "expected_input_version": 1, "profile": profile,
    }).json()
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 200
    assert response.json()["input_version"] == 2
    assert response.json()["requested_location"] == profile["location"]
    adapter.observe.assert_called_once_with(
        latitude=6.12, longitude=81.12, start=date(2024, 2, 28), end=date(2024, 3, 1),
    )
    assert client.get(f"/api/v1/farms/{farm['id']}").json() == updated


@pytest.mark.parametrize("farm_id", ["not-a-uuid", "00000000-0000-0000-0000-000000000000"])
def test_unknown_ids_are_404_without_provider_access(client, adapter, farm_id):
    response = client.get(f"/api/v1/farms/{farm_id}/observations", params=DATES)
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Farm not found."}}
    adapter.observe.assert_not_called()


@pytest.mark.parametrize("params", [
    {}, {"start": "2024-02-28"}, {"end": "2024-03-01"},
    {**DATES, "start": "bad-date"}, {**DATES, "start": "2024-02-30"},
    {**DATES, "end": "2023-02-29"}, {**DATES, "start": "2024-03-02"},
    {**DATES, "start": "1980-12-31"},
    {**DATES, "start": "1709078400"},
    {**DATES, "start": "2024-02-28T00:00:00Z"},
    {**DATES, "start": "20240228"}, {**DATES, "unexpected": "value"},
])
def test_invalid_queries_are_422(client, adapter, farm, params):
    response = client.get(endpoint(farm), params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["fields"]
    adapter.observe.assert_not_called()


@pytest.mark.parametrize("offset", [0, 1])
def test_today_and_future_dates_are_422(client, adapter, farm, offset):
    end = (datetime.now(timezone.utc).date() + timedelta(days=offset)).isoformat()
    response = client.get(endpoint(farm), params={**DATES, "end": end})
    assert response.status_code == 422
    adapter.observe.assert_not_called()


def test_missing_adapter_is_503(client, farm):
    app.dependency_overrides[get_observation_adapter] = lambda: None
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


@pytest.mark.parametrize("failure", [
    ObservationServiceUnavailable("private-token"),
    URLError("private-token"), TimeoutError("private-token"),
    HTTPError("https://example.invalid/private-token", 429, "rate limited", {}, None),
])
def test_provider_failures_are_safe_503(client, adapter, farm, failure):
    adapter.observe.side_effect = failure
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "private-token" not in response.text
    assert "rate limited" not in response.text


def test_incomplete_coverage_discloses_missing_days(client, adapter, farm, provider_fixture):
    raw = provider_fixture
    raw["properties"]["parameter"]["T2M"]["20240229"] = -999
    del raw["properties"]["parameter"]["PRECTOTCORR"]["20240301"]
    adapter.observe.return_value = synthetic_observations(raw)
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 200
    payload = response.json()
    assert payload["coverage"] == {
        "expected_days": 3, "available_days": 1,
        "temperature_valid_days": 2, "precipitation_valid_days": 2,
    }
    assert payload["summary"]["rainfall_mm"] is None
    assert payload["summary"]["rainfall_total_mm"] is None
    assert payload["summary"]["rainfall_available_days_mm"] == 2
    assert payload["summary"]["mean_temperature_c"] == 22
    assert payload["daily"][1]["temperature_c"] is None
    assert payload["daily"][2]["precipitation_mm_per_day"] is None
    assert payload["missing_data"] == {
        "temperature_missing_dates": ["2024-02-29"],
        "precipitation_missing_dates": ["2024-03-01"],
    }
    assert any("Incomplete coverage" in item for item in payload["limitations"])


@pytest.mark.parametrize("value,expected", [(-999, None), (0, 0)])
def test_missing_values_and_valid_zeros_are_distinct(client, adapter, farm, provider_fixture, value, expected):
    for parameter in provider_fixture["properties"]["parameter"].values():
        for day in parameter:
            parameter[day] = value
    adapter.observe.return_value = synthetic_observations(provider_fixture)
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["rainfall_mm"] == expected
    assert payload["summary"]["mean_temperature_c"] == expected
    assert payload["daily"][0]["temperature_c"] == expected


@pytest.mark.parametrize("change", [
    lambda value: value.pop("api"),
    lambda value: value["summary"].update(start="2024-02-27"),
    lambda value: value["summary"].update(temperature_valid_days=0),
    lambda value: value["daily"].pop(),
    lambda value: value["summary"].update(mean_temperature_c=float("nan")),
    lambda value: value.update(retrieved_at="2024-03-02T00:00:00"),
])
def test_unusable_provider_payload_is_503(client, adapter, farm, change):
    change(adapter.observe.return_value)
    response = client.get(endpoint(farm), params=DATES)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_bridge_calls_matheeshas_fetch_and_normalize(monkeypatch, provider_fixture):
    fetch = Mock(return_value=(provider_fixture, RETRIEVED_AT, SYNTHETIC_URL))
    normalized = synthetic_observations(provider_fixture)
    normalize = Mock(return_value=normalized)
    monkeypatch.setattr(nasa_power, "fetch", fetch)
    monkeypatch.setattr(nasa_power, "normalize", normalize)
    result = NASAPowerObservationAdapter().observe(
        latitude=8.3, longitude=80.4, start=date(2024, 2, 28), end=date(2024, 3, 1),
    )
    assert result is normalized
    fetch.assert_called_once_with(8.3, 80.4, "2024-02-28", "2024-03-01")
    normalize.assert_called_once_with(
        provider_fixture, "2024-02-28", "2024-03-01", RETRIEVED_AT, SYNTHETIC_URL,
    )


@pytest.mark.parametrize("failure", [
    URLError("secret"), TimeoutError(), IncompleteRead(b"partial"),
    ValueError(), KeyError(), TypeError(), AttributeError(),
])
def test_bridge_converts_expected_provider_errors(monkeypatch, failure):
    monkeypatch.setattr(nasa_power, "fetch", Mock(side_effect=failure))
    with pytest.raises(ObservationServiceUnavailable):
        NASAPowerObservationAdapter().observe(
            latitude=8.3, longitude=80.4, start=date(2024, 2, 28), end=date(2024, 3, 1),
        )


def test_bridge_rejects_bad_provider_units(monkeypatch, provider_fixture):
    provider_fixture["parameters"]["T2M"]["units"] = "unexpected"
    monkeypatch.setattr(nasa_power, "fetch", Mock(return_value=(
        provider_fixture, RETRIEVED_AT, SYNTHETIC_URL,
    )))
    with pytest.raises(ObservationServiceUnavailable):
        NASAPowerObservationAdapter().observe(
            latitude=8.3, longitude=80.4, start=date(2024, 2, 28), end=date(2024, 3, 1),
        )


def test_disabled_service_dependency(monkeypatch):
    monkeypatch.setattr(observations, "settings", Mock(nasa_power_enabled=False))
    assert get_observation_adapter() is None


def test_default_service_dependency(monkeypatch):
    monkeypatch.setattr(observations, "settings", Mock(nasa_power_enabled=True))
    assert isinstance(get_observation_adapter(), NASAPowerObservationAdapter)
