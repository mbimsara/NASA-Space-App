import pytest

from agrosphere_rotation import (
    ClimateInput,
    calculate_water_budget,
    calculate_water_budget_range,
    load_water_requirements,
)


def test_reduced_rainfall_recomputes_same_budget() -> None:
    climate = ClimateInput(
        rainfall_mm=500,
        irrigation_mm=100,
        irrigation_basis="field_applied_depth",
        rainfall_change_percent=-20,
        source="normalized NASA observation fixture",
        observation_start="2026-05-01",
        observation_end="2026-08-31",
    )

    result = calculate_water_budget(600, climate)

    assert result.scenario_rainfall_mm == pytest.approx(400)
    assert result.available_water_mm == pytest.approx(500)
    assert result.balance_mm == pytest.approx(-100)
    assert result.coverage_percent == pytest.approx(83.333333)


def test_crop_demand_must_be_positive() -> None:
    climate = ClimateInput(
        rainfall_mm=500,
        source="fixture",
        observation_start="2026-05-01",
        observation_end="2026-08-31",
    )

    with pytest.raises(ValueError, match="greater than zero"):
        calculate_water_budget(0, climate)


def test_fao_water_ranges_load_on_one_comparable_basis() -> None:
    version, requirements = load_water_requirements(
        "data/catalogs/crop-water-requirements.json"
    )

    assert version == "fao-seasonal-etc-0.1"
    assert requirements["rice"].low_mm == 450
    assert requirements["rice"].high_mm == 700
    assert requirements["rice"].basis == "seasonal_crop_water_need_etc"
    assert set(requirements) == {
        "rice",
        "mung-bean",
        "maize",
        "groundnut",
        "cowpea",
        "finger-millet",
        "black-gram",
        "chilli",
    }


def test_range_budget_uses_conservative_demand_endpoints() -> None:
    _, requirements = load_water_requirements(
        "data/catalogs/crop-water-requirements.json"
    )
    climate = ClimateInput(
        rainfall_mm=500,
        irrigation_mm=100,
        irrigation_basis="field_applied_depth",
        rainfall_change_percent=-20,
        source="normalized NASA observation fixture",
        observation_start="2026-05-01",
        observation_end="2026-08-31",
    )

    result = calculate_water_budget_range(requirements["maize"], climate)

    assert result.available_water_mm == pytest.approx(500)
    assert result.balance_low_mm == pytest.approx(-300)
    assert result.balance_high_mm == pytest.approx(0)
    assert result.coverage_low_percent == pytest.approx(62.5)
    assert result.coverage_high_percent == pytest.approx(100)
    assert result.demand_basis == "seasonal_crop_water_need_etc"


def test_unknown_irrigation_does_not_silently_become_zero() -> None:
    climate = ClimateInput(
        rainfall_mm=500,
        source="fixture",
        observation_start="2026-05-01",
        observation_end="2026-08-31",
    )

    assert climate.irrigation_mm is None
    with pytest.raises(ValueError, match="irrigation is unknown"):
        calculate_water_budget(600, climate)


def test_explicit_zero_irrigation_uses_declared_basis() -> None:
    climate = ClimateInput(
        rainfall_mm=500,
        irrigation_mm=0,
        irrigation_basis="field_applied_depth",
        source="fixture",
        observation_start="2026-05-01",
        observation_end="2026-08-31",
    )

    assert calculate_water_budget(600, climate).available_water_mm == 500
