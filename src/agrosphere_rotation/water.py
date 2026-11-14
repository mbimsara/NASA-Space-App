"""Deterministic seasonal water-budget calculations."""

from .models import ClimateInput, WaterBudget


def calculate_water_budget(crop_demand_mm: float, climate: ClimateInput) -> WaterBudget:
    """Compare crop demand with scenario-adjusted rainfall plus irrigation.

    This first version treats all supplied rainfall as available water. Effective
    rainfall, runoff, soil storage, and irrigation efficiency must be added only
    after the team agrees on sourced assumptions.
    """

    if crop_demand_mm <= 0:
        raise ValueError("crop_demand_mm must be greater than zero")

    multiplier = 1 + climate.rainfall_change_percent / 100
    scenario_rainfall = climate.rainfall_mm * multiplier
    available = scenario_rainfall + climate.irrigation_mm

    return WaterBudget(
        crop_demand_mm=crop_demand_mm,
        baseline_rainfall_mm=climate.rainfall_mm,
        scenario_rainfall_mm=scenario_rainfall,
        irrigation_mm=climate.irrigation_mm,
        available_water_mm=available,
        balance_mm=available - crop_demand_mm,
        coverage_percent=available / crop_demand_mm * 100,
        assumptions=(
            "All values cover the same crop season and use millimetres of water.",
            "Rainfall-change percentage defines a hypothetical scenario.",
            "No effective-rainfall, runoff, storage, or irrigation-efficiency factor is applied.",
        ),
    )

