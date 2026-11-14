"""Season-specific rainfall inputs for rotation water screening (provider mocked)."""

import json
from datetime import date, timedelta

import pytest

from app.main import app
from app.services import rotations
from app.services.observations import get_observation_adapter
from app.services.season_inputs import (
    SeasonPeriod, SeasonPeriodInvalid, calendar_periods, validate_periods,
)
from observation_fixtures import DATES, synthetic_observations


APPROVED_CATALOG = {
    "schema_version": "0.1", "catalog_version": "approved-test-v1", "status": "reviewed",
    "crops": [
        {
            "id": "rice", "name": "Rice", "family": "Poaceae",
            "season_labels": ["maha"], "water_demand_mm_per_cycle": 575,
            "sources": [{"url": "https://example.org/rice"}], "review_status": "approved",
        },
        {
            "id": "mung-bean", "name": "Mung bean", "family": "Fabaceae",
            "season_labels": ["yala"], "water_demand_mm_per_cycle": 400,
            "sources": [{"url": "https://example.org/mung"}], "review_status": "approved",
        },
    ],
}


def daily_rain(day: date) -> float:
    """Synthetic, month-dependent rainfall so different seasons have different totals."""
    return {10: 6, 11: 8, 12: 5, 1: 3, 2: 2}.get(day.month, 1.5)


def raw_power(start: date, end: date) -> dict:
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    key = lambda d: d.strftime("%Y%m%d")  # noqa: E731
    return {
        "header": {"start": key(start), "end": key(end), "time_standard": "UTC",
                   "fill_value": -999, "sources": ["synthetic-test-not-nasa"],
                   "api": {"version": "synthetic-test-version"}},
        "parameters": {"T2M": {"units": "C", "longname": "Synthetic"},
                       "PRECTOTCORR": {"units": "mm/day", "longname": "Synthetic"}},
        "geometry": {"coordinates": [80.4, 8.3]},
        "properties": {"parameter": {
            "T2M": {key(d): 27 for d in days},
            "PRECTOTCORR": {key(d): daily_rain(d) for d in days},
        }},
    }


def expected_total(start: date, end: date) -> float:
    return sum(daily_rain(start + timedelta(days=i)) for i in range((end - start).days + 1))


@pytest.fixture
def period_adapter(adapter):
    def observe(*, latitude, longitude, start, end):
        return synthetic_observations(raw_power(start, end), start.isoformat(), end.isoformat())
    adapter.observe.side_effect = observe
    return adapter


@pytest.fixture
def approved_catalog(tmp_path, monkeypatch):
    path = tmp_path / "crops.json"
    path.write_text(json.dumps(APPROVED_CATALOG), encoding="utf-8")
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)


def set_irrigation(client, farm, value):
    profile = client.get(f"/api/v1/farms/{farm['id']}").json()["profile"]
    profile["irrigation_supply_mm_per_season"] = value
    response = client.patch(f"/api/v1/farms/{farm['id']}", json={
        "expected_input_version": farm["input_version"], "profile": profile,
    })
    assert response.status_code == 200
    return response.json()


def analyse(client, farm, **changes):
    obs = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES)
    assert obs.status_code == 200
    body = {
        "input_version": farm["input_version"], "observation_id": obs.json()["observation_id"],
        "seasons": 3, "season_labels": ["maha", "yala", "maha"],
        "catalog_version": "approved-test-v1",
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
        **changes,
    }
    return client.post(f"/api/v1/farms/{farm['id']}/rotations", json=body)


# --- calendar -----------------------------------------------------------------

def test_calendar_gives_each_season_its_own_chronological_period():
    periods = calendar_periods(["maha", "yala", "maha"], today=date(2026, 11, 14))
    assert periods == [
        SeasonPeriod(date(2024, 10, 1), date(2025, 2, 28)),
        SeasonPeriod(date(2025, 3, 1), date(2025, 8, 31)),
        SeasonPeriod(date(2025, 10, 1), date(2026, 2, 28)),
    ]
    assert len(set(periods)) == len(periods)


def test_calendar_handles_inter_season_and_leap_february():
    periods = calendar_periods(["yala", "inter-season", "maha"], today=date(2024, 3, 15))
    assert periods == [
        SeasonPeriod(date(2023, 3, 1), date(2023, 8, 31)),
        SeasonPeriod(date(2023, 9, 1), date(2023, 9, 30)),
        SeasonPeriod(date(2023, 10, 1), date(2024, 2, 29)),
    ]


@pytest.mark.parametrize("periods", [
    [SeasonPeriod(date(2024, 1, 1), date(2024, 3, 1)), SeasonPeriod(date(2024, 3, 1), date(2024, 5, 1))],
    [SeasonPeriod(date(2024, 5, 1), date(2024, 6, 1)), SeasonPeriod(date(2024, 1, 1), date(2024, 2, 1))],
    [SeasonPeriod(date(2024, 1, 1), date(2024, 2, 1)), SeasonPeriod(date(2026, 11, 1), date(2026, 11, 20))],
    [SeasonPeriod(date(1980, 1, 1), date(1980, 2, 1)), SeasonPeriod(date(2024, 1, 1), date(2024, 2, 1))],
    [SeasonPeriod(date(2022, 1, 1), date(2023, 6, 1)), SeasonPeriod(date(2024, 1, 1), date(2024, 2, 1))],
])
def test_invalid_explicit_periods_are_rejected(periods):
    with pytest.raises(SeasonPeriodInvalid):
        validate_periods(periods, seasons=2, today=date(2026, 11, 14))


# --- API ------------------------------------------------------------------------

def test_calendar_seasons_compute_separate_water_budgets(client, period_adapter, farm, approved_catalog):
    farm = set_irrigation(client, farm, 100)
    response = analyse(client, farm, season_periods="calendar")

    assert response.status_code == 201
    analysis = response.json()
    seasons = analysis["season_inputs"]
    assert [s["season_label"] for s in seasons] == ["maha", "yala", "maha"]
    assert all(s["period_source"] == "season_calendar" for s in seasons)
    # Every season has its own observation snapshot and period; nothing is reused.
    assert len({s["observation_id"] for s in seasons}) == 3
    assert len({(s["period_start"], s["period_end"]) for s in seasons}) == 3
    assert seasons[0]["period_end"] < seasons[1]["period_start"] < seasons[2]["period_start"]
    for s in seasons:
        start, end = date.fromisoformat(s["period_start"]), date.fromisoformat(s["period_end"])
        assert s["rainfall_total_mm"] == pytest.approx(expected_total(start, end))
        assert s["observation_id"] in analysis["source_refs"]

    candidate = analysis["candidates"][0]
    assert [step["crop_id"] for step in candidate["sequence"]] == ["rice", "mung-bean", "rice"]
    rows = candidate["water_budget_range"]
    for row, season in zip(rows, seasons):
        assert row["baseline_rainfall_mm"] == pytest.approx(season["rainfall_total_mm"])
        assert row["irrigation_mm"] == 100
        assert row["available_water_mm"] == pytest.approx(season["rainfall_total_mm"] + 100)
        assert row["demand_basis"] == "seasonal_crop_water_need_etc"
    assert (rows[0]["demand_low_mm"], rows[0]["demand_high_mm"]) == (450, 700)
    assert (rows[1]["demand_low_mm"], rows[1]["demand_high_mm"]) == (300, 500)
    assert rows[0]["coverage_low_percent"] == pytest.approx((seasons[0]["rainfall_total_mm"] + 100) / 700 * 100)

    components = {c["name"]: c for c in candidate["score_components"]}
    expected_water = sum(r["baseline_coverage_low_percent"] for r in rows) / 3
    assert components["water_sufficiency"]["value"] == pytest.approx(min(100, expected_water))
    assert components["scenario_resilience"]["value"] is None
    assert period_adapter.observe.call_count == 4  # request window + three seasons


def test_unknown_irrigation_keeps_rainfall_but_not_budgets(client, period_adapter, farm, approved_catalog):
    response = analyse(client, farm, season_periods="calendar")

    assert response.status_code == 201
    analysis = response.json()
    row = analysis["candidates"][0]["water_budget_range"][0]
    assert row["baseline_rainfall_mm"] == pytest.approx(analysis["season_inputs"][0]["rainfall_total_mm"])
    assert row["irrigation_mm"] is None
    assert row["available_water_mm"] is None and row["coverage_low_percent"] is None
    assert "Irrigation is unknown" in row["limitations"][0]
    components = {c["name"]: c for c in analysis["candidates"][0]["score_components"]}
    assert components["water_sufficiency"]["value"] is None


def test_explicit_periods_and_scenario_recalculation(client, period_adapter, farm, approved_catalog):
    farm = set_irrigation(client, farm, 50)
    periods = [
        {"start": "2023-10-01", "end": "2024-01-31"},
        {"start": "2024-04-01", "end": "2024-07-31"},
        {"start": "2024-10-01", "end": "2025-01-31"},
    ]
    analysis = analyse(client, farm, season_periods=periods).json()
    assert [s["period_source"] for s in analysis["season_inputs"]] == ["request"] * 3
    assert [s["period_start"] for s in analysis["season_inputs"]] == [p["start"] for p in periods]

    scenario = client.post(
        f"/api/v1/analyses/{analysis['analysis_id']}/scenarios", json={"rainfall_change_pct": -30},
    )
    assert scenario.status_code == 201
    row = scenario.json()["candidates"][0]["water_budget_range"][0]
    baseline_rain = analysis["season_inputs"][0]["rainfall_total_mm"]
    assert row["scenario_rainfall_mm"] == pytest.approx(baseline_rain * 0.7)
    components = {c["name"]: c for c in scenario.json()["candidates"][0]["score_components"]}
    assert components["scenario_resilience"]["value"] is not None


@pytest.mark.parametrize("periods", [
    [{"start": "2024-01-01", "end": "2024-03-01"}],
    [{"start": "2024-01-01", "end": "2024-03-01"}, {"start": "2024-02-01", "end": "2024-04-01"},
     {"start": "2024-05-01", "end": "2024-06-01"}],
    [{"start": "2024-01-01", "end": "2024-02-01"}, {"start": "2024-03-01", "end": "2024-04-01"},
     {"start": "2099-01-01", "end": "2099-02-01"}],
])
def test_invalid_periods_return_422(client, period_adapter, farm, approved_catalog, periods):
    response = analyse(client, farm, season_periods=periods)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SEASON_PERIODS_INVALID"


def test_unknown_season_periods_value_is_validation_error(client, period_adapter, farm, approved_catalog):
    response = analyse(client, farm, season_periods="forecast")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_provider_unavailable_returns_503(client, period_adapter, farm, approved_catalog):
    obs = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES).json()
    app.dependency_overrides[get_observation_adapter] = lambda: None
    response = client.post(f"/api/v1/farms/{farm['id']}/rotations", json={
        "input_version": farm["input_version"], "observation_id": obs["observation_id"],
        "seasons": 3, "season_labels": ["maha", "yala", "maha"],
        "catalog_version": "approved-test-v1",
        "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
        "season_periods": "calendar",
    })
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_without_season_periods_behavior_is_unchanged(client, period_adapter, farm, approved_catalog):
    analysis = analyse(client, farm).json()
    assert analysis["season_inputs"] == []
    assert all(row["baseline_rainfall_mm"] is None for row in analysis["candidates"][0]["water_budget_range"])
    assert period_adapter.observe.call_count == 1
