"""Dated, season-specific rainfall inputs for rotation water screening.

Each planned season gets its own historical reference period and its own
persisted NASA POWER observation snapshot. One rainfall total is never reused
for several seasons: repeated labels (for example maha, yala, maha) map to
different, chronologically ordered historical seasons.

These periods are historical analogs used for screening, not forecasts of the
future seasons being planned.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from agrosphere_rotation import (
    ClimateInput, WaterBudgetRange, WaterDemandRange,
    calculate_water_budget_range, load_water_requirements,
)

from app.models.farm import Farm
from app.services.observation_cache import get_or_fetch_snapshot, snapshot_response
from app.services.observations import ObservationAdapter


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
WATER_REQUIREMENTS_PATH = REPOSITORY_ROOT / "data" / "catalogs" / "crop-water-requirements.json"
EARLIEST_DATE = date(1981, 1, 1)
MAX_PERIOD_DAYS = 366
CALENDAR_VERSION = "sl-season-calendar-0.1"

# (start month, start day, end month, end day, crosses calendar year).
# Maha and Yala follow docs/AGRONOMY_RULES.md (Maha Oct–Feb, Yala Mar–Aug);
# the inter-season is the remaining September gap. Demo configuration only.
SEASON_WINDOWS = {
    "maha": (10, 1, 2, None, True),
    "yala": (3, 1, 8, 31, False),
    "inter-season": (9, 1, 9, 30, False),
}


class SeasonPeriodInvalid(ValueError):
    pass


@dataclass(frozen=True)
class SeasonPeriod:
    start: date
    end: date


def _month_end(year: int, month: int) -> date:
    following = date(year + month // 12, month % 12 + 1, 1)
    return following - timedelta(days=1)


def _window(label: str, start_year: int) -> SeasonPeriod:
    start_month, start_day, end_month, end_day, crosses = SEASON_WINDOWS[label]
    end_year = start_year + 1 if crosses else start_year
    end = date(end_year, end_month, end_day) if end_day else _month_end(end_year, end_month)
    return SeasonPeriod(date(start_year, start_month, start_day), end)


def calendar_periods(labels: list[str], *, today: date) -> list[SeasonPeriod]:
    """Most recent complete historical seasons, in planned order, without overlap.

    Walks backwards from today: the last planned season gets the latest
    complete matching window, each earlier season the latest window that ends
    before the following one starts.
    """
    periods: list[SeasonPeriod] = []
    boundary = today  # every window must end strictly before this date
    for label in reversed(labels):
        if label not in SEASON_WINDOWS:
            raise SeasonPeriodInvalid(f"No calendar window is defined for season '{label}'.")
        year = boundary.year
        window = _window(label, year)
        while window.end >= boundary:
            year -= 1
            window = _window(label, year)
        if window.start < EARLIEST_DATE:
            raise SeasonPeriodInvalid("Not enough NASA POWER history for the requested seasons.")
        periods.append(window)
        boundary = window.start
    return list(reversed(periods))


def validate_periods(periods: list[SeasonPeriod], *, seasons: int, today: date) -> list[SeasonPeriod]:
    if len(periods) != seasons:
        raise SeasonPeriodInvalid("season_periods must have one period per season.")
    for index, period in enumerate(periods):
        if period.start > period.end:
            raise SeasonPeriodInvalid(f"Season {index + 1} starts after it ends.")
        if period.start < EARLIEST_DATE or period.end >= today:
            raise SeasonPeriodInvalid(
                f"Season {index + 1} must lie between {EARLIEST_DATE.isoformat()} and yesterday (UTC)."
            )
        if (period.end - period.start).days + 1 > MAX_PERIOD_DAYS:
            raise SeasonPeriodInvalid(f"Season {index + 1} is longer than {MAX_PERIOD_DAYS} days.")
        if index and period.start <= periods[index - 1].end:
            raise SeasonPeriodInvalid("Season periods must be chronological and must not overlap.")
    return periods


def retrieve_season_inputs(
    db: Session, farm: Farm, *, labels: list[str], periods: list[SeasonPeriod],
    adapter: ObservationAdapter | None, period_source: str,
) -> list[dict]:
    """Fetch (or reuse cached) rainfall separately for every planned season."""
    inputs = []
    for index, (label, period) in enumerate(zip(labels, periods), 1):
        snapshot, _ = get_or_fetch_snapshot(db, farm, start=period.start, end=period.end, adapter=adapter)
        observation = snapshot_response(snapshot)
        coverage = observation.coverage
        limitations = []
        if observation.summary.rainfall_total_mm is None:
            limitations.append(
                "Incomplete rainfall coverage for this period: the seasonal total is unknown "
                "and partial sums are not substituted."
            )
        inputs.append({
            "season_index": index,
            "season_label": label,
            "period_start": period.start,
            "period_end": period.end,
            "period_source": period_source,
            "observation_id": observation.observation_id,
            "data_kind": observation.data_kind,
            "expected_days": coverage.expected_days,
            "rainfall_valid_days": coverage.precipitation_valid_days,
            "rainfall_total_mm": observation.summary.rainfall_total_mm,
            "source_refs": list(observation.source_refs),
            "limitations": limitations + list(observation.limitations),
        })
    return inputs


def load_demands() -> tuple[str, dict[str, WaterDemandRange]]:
    return load_water_requirements(WATER_REQUIREMENTS_PATH)


def season_water_row(
    season: dict, crop_id: str, *, irrigation_mm: float | None,
    demands: dict[str, WaterDemandRange],
) -> tuple[dict, WaterBudgetRange | None]:
    """One per-season water record and, when every input is known, the engine budget."""
    demand = demands.get(crop_id)
    rainfall = season["rainfall_total_mm"]
    period_text = f"{season['period_start'].isoformat()} to {season['period_end'].isoformat()}"
    assumptions = [
        f"Rainfall is the NASA POWER total for the historical reference period {period_text} "
        f"(observation {season['observation_id']}); it is not a forecast of the planned season.",
    ]
    limitations = [
        "Rainfall covers the whole season window; a shorter crop cycle may receive less rain, "
        "so available water may be overstated.",
    ]
    row = {
        "season_index": season["season_index"],
        "season_label": season["season_label"],
        "crop_id": crop_id,
        "demand_low_mm": demand.low_mm if demand else None,
        "demand_nominal_mm": demand.nominal_mm if demand else None,
        "demand_high_mm": demand.high_mm if demand else None,
        "baseline_rainfall_mm": rainfall,
        "scenario_rainfall_mm": rainfall,
        "irrigation_mm": irrigation_mm,
        "baseline_available_water_mm": None,
        "baseline_coverage_low_percent": None, "baseline_coverage_high_percent": None,
        "available_water_mm": None, "balance_low_mm": None, "balance_high_mm": None,
        "coverage_low_percent": None, "coverage_high_percent": None,
        "demand_basis": demand.basis if demand else None,
        "model_version": demand.model_version if demand else None,
        "source_url": demand.source_url if demand else None,
        "assumptions": assumptions,
        "limitations": limitations + list(season["limitations"]),
    }
    if demand is None:
        row["limitations"].insert(0, "No reviewed crop-water demand range exists for this crop.")
    else:
        row["limitations"].extend(demand.limitations)
    if irrigation_mm is None:
        row["limitations"].insert(0, "Irrigation is unknown; available water, balance and coverage are not calculated.")
    if demand is None or rainfall is None or irrigation_mm is None:
        return row, None

    budget = calculate_water_budget_range(demand, ClimateInput(
        rainfall_mm=rainfall, irrigation_mm=irrigation_mm, irrigation_basis="field_applied_depth",
        source="NASA POWER (modeled gridded estimate)",
        observation_start=season["period_start"].isoformat(),
        observation_end=season["period_end"].isoformat(),
        source_refs=tuple(season["source_refs"]), data_kind=season["data_kind"],
    ))
    row.update({
        "baseline_rainfall_mm": budget.baseline_rainfall_mm,
        "scenario_rainfall_mm": budget.scenario_rainfall_mm,
        "irrigation_mm": budget.irrigation_mm,
        "baseline_available_water_mm": budget.baseline_available_water_mm,
        "baseline_coverage_low_percent": budget.baseline_coverage_low_percent,
        "baseline_coverage_high_percent": budget.baseline_coverage_high_percent,
        "available_water_mm": budget.available_water_mm,
        "balance_low_mm": budget.balance_low_mm,
        "balance_high_mm": budget.balance_high_mm,
        "coverage_low_percent": budget.coverage_low_percent,
        "coverage_high_percent": budget.coverage_high_percent,
        "assumptions": assumptions + list(budget.assumptions),
    })
    return row, budget
