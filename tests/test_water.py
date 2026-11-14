import pytest

from agrosphere_rotation import ClimateInput, calculate_water_budget


def test_reduced_rainfall_recomputes_same_budget() -> None:
    climate = ClimateInput(
        rainfall_mm=500,
        irrigation_mm=100,
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

