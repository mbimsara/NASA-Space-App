"""Deterministic seasonal water-budget calculations."""

from .models import ClimateInput, WaterBudget, WaterBudgetRange, WaterDemandRange


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


def calculate_water_budget_range(
    demand: WaterDemandRange, climate: ClimateInput
) -> WaterBudgetRange:
    """Screen a crop-water range against rainfall plus entered irrigation.

    The result is deliberately a range. It uses total rainfall as a provisional
    upper-bound input until an effective-rainfall model is approved.
    """

    multiplier = 1 + climate.rainfall_change_percent / 100
    scenario_rainfall = climate.rainfall_mm * multiplier
    available = scenario_rainfall + climate.irrigation_mm
    baseline_available = climate.rainfall_mm + climate.irrigation_mm
    return WaterBudgetRange(
        crop_id=demand.crop_id,
        demand_low_mm=demand.low_mm,
        demand_high_mm=demand.high_mm,
        baseline_rainfall_mm=climate.rainfall_mm,
        scenario_rainfall_mm=scenario_rainfall,
        irrigation_mm=climate.irrigation_mm,
        baseline_available_water_mm=baseline_available,
        available_water_mm=available,
        baseline_coverage_low_percent=baseline_available / demand.high_mm * 100,
        baseline_coverage_high_percent=baseline_available / demand.low_mm * 100,
        balance_low_mm=available - demand.high_mm,
        balance_high_mm=available - demand.low_mm,
        coverage_low_percent=available / demand.high_mm * 100,
        coverage_high_percent=available / demand.low_mm * 100,
        demand_basis=demand.basis,
        model_version=demand.model_version,
        assumptions=(
            "Demand is an indicative seasonal ETc range, not gross irrigation delivery.",
            "All values must cover the same crop period and use millimetres.",
            "Total rainfall is provisionally treated as available; effective rainfall is not modeled.",
            "Irrigation efficiency, runoff, storage, seepage and percolation are not modeled.",
            "The rainfall change is a hypothetical scenario, not a forecast.",
        ),
    )
