"""Validated domain contracts owned by the rotation engine.

These models intentionally preserve unknown agronomy values as ``None``. An
unknown value must not silently become zero or an invented default.
"""

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse


class Season(StrEnum):
    MAHA = "maha"
    YALA = "yala"
    INTER_SEASON = "inter-season"


@dataclass(frozen=True, slots=True)
class Crop:
    id: str
    name: str
    family: str
    suitable_seasons: frozenset[str]
    source_urls: tuple[str, ...]
    water_demand_mm: float | None = None
    review_status: str = "draft"
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not all(c.islower() or c.isdigit() or c == "-" for c in self.id):
            raise ValueError("crop id must contain lowercase letters, digits, or hyphens")
        if not self.name.strip() or not self.family.strip():
            raise ValueError("crop name and family are required")
        if not self.suitable_seasons:
            raise ValueError("at least one suitable season is required")
        if self.water_demand_mm is not None and self.water_demand_mm <= 0:
            raise ValueError("water_demand_mm must be positive when known")
        if not self.source_urls or any(urlparse(url).scheme not in {"http", "https"} for url in self.source_urls):
            raise ValueError("at least one HTTP(S) source URL is required")
        if self.review_status not in {"draft", "approved"}:
            raise ValueError("review_status must be draft or approved")


@dataclass(frozen=True, slots=True)
class ClimateInput:
    """Seasonal values normalized before entering the rotation engine."""

    rainfall_mm: float
    source: str
    observation_start: str
    observation_end: str
    irrigation_mm: float = 0
    rainfall_change_percent: float = 0

    def __post_init__(self) -> None:
        if self.rainfall_mm < 0 or self.irrigation_mm < 0:
            raise ValueError("rainfall and irrigation cannot be negative")
        if self.rainfall_change_percent < -100:
            raise ValueError("rainfall change cannot be below -100 percent")
        if not self.source.strip():
            raise ValueError("climate source is required")

    @classmethod
    def from_nasa_power(
        cls,
        normalized: dict,
        *,
        irrigation_mm: float = 0,
        rainfall_change_percent: float = 0,
    ) -> "ClimateInput":
        """Create an input from Matheesha's normalized NASA POWER result.

        Incomplete periods have a null rainfall total and are rejected. The
        available-days partial sum must never be substituted for a full total.
        """

        if normalized.get("provider") != "NASA POWER":
            raise ValueError("expected a normalized NASA POWER result")
        summary = normalized.get("summary", {})
        rainfall = summary.get("rainfall_total_mm")
        if rainfall is None:
            raise ValueError("complete-period rainfall_total_mm is required")
        return cls(
            rainfall_mm=rainfall,
            irrigation_mm=irrigation_mm,
            rainfall_change_percent=rainfall_change_percent,
            source="NASA POWER (modeled gridded estimate)",
            observation_start=summary["start"],
            observation_end=summary["end"],
        )

    @classmethod
    def from_season_inputs(
        cls,
        season: dict,
        *,
        irrigation_mm: float = 0,
        rainfall_change_percent: float = 0,
    ) -> "ClimateInput":
        """Consume Matheesha's PR #1 ``season_inputs`` handoff.

        The handoff deliberately leaves agronomic calculations null. This
        adapter accepts only complete rainfall coverage and retains ownership of
        scenario and water-budget calculations in this package.
        """

        expected = season.get("expected_days")
        valid = season.get("rain_valid_days")
        if type(expected) is not int or expected <= 0:
            raise ValueError("season expected_days must be a positive integer")
        if valid != expected or season.get("rainfall_total_mm") is None:
            raise ValueError("complete seasonal rainfall coverage is required")
        if season.get("effective_rainfall_mm") is not None:
            raise ValueError("effective rainfall must use Bhagya's approved model")
        if season.get("crop_water_demand_mm") is not None:
            raise ValueError("crop water demand must use Bhagya's approved catalog")
        if season.get("irrigation_deficit_mm") is not None:
            raise ValueError("irrigation deficit must be calculated by the rotation engine")

        return cls(
            rainfall_mm=season["rainfall_total_mm"],
            irrigation_mm=irrigation_mm,
            rainfall_change_percent=rainfall_change_percent,
            source="NASA POWER season_inputs (modeled gridded estimate)",
            observation_start=season["start"],
            observation_end=season["end"],
        )


@dataclass(frozen=True, slots=True)
class WaterBudget:
    crop_demand_mm: float
    baseline_rainfall_mm: float
    scenario_rainfall_mm: float
    irrigation_mm: float
    available_water_mm: float
    balance_mm: float
    coverage_percent: float
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.crop_demand_mm <= 0:
            raise ValueError("crop demand must be positive")
        if min(self.baseline_rainfall_mm, self.scenario_rainfall_mm, self.irrigation_mm, self.available_water_mm) < 0:
            raise ValueError("water inputs cannot be negative")
        expected = self.available_water_mm - self.crop_demand_mm
        if abs(self.balance_mm - expected) > 1e-9:
            raise ValueError("balance_mm must equal available water minus crop demand")


@dataclass(frozen=True, slots=True)
class WaterDemandRange:
    crop_id: str
    low_mm: float
    high_mm: float
    nominal_mm: float
    basis: str
    model_version: str
    source_url: str
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.crop_id:
            raise ValueError("crop_id is required")
        if not 0 < self.low_mm <= self.nominal_mm <= self.high_mm:
            raise ValueError("water demand must satisfy 0 < low <= nominal <= high")
        if self.basis != "seasonal_crop_water_need_etc":
            raise ValueError("unsupported water-demand basis")
        if urlparse(self.source_url).scheme not in {"http", "https"}:
            raise ValueError("water-demand source must be HTTP(S)")


@dataclass(frozen=True, slots=True)
class WaterBudgetRange:
    crop_id: str
    demand_low_mm: float
    demand_high_mm: float
    baseline_rainfall_mm: float
    scenario_rainfall_mm: float
    irrigation_mm: float
    available_water_mm: float
    balance_low_mm: float
    balance_high_mm: float
    coverage_low_percent: float
    coverage_high_percent: float
    demand_basis: str
    model_version: str
    assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not 0 < self.demand_low_mm <= self.demand_high_mm:
            raise ValueError("invalid demand range")
        if self.available_water_mm < 0:
            raise ValueError("available water cannot be negative")
        if abs(self.balance_low_mm - (self.available_water_mm - self.demand_high_mm)) > 1e-9:
            raise ValueError("low balance must use high demand")
        if abs(self.balance_high_mm - (self.available_water_mm - self.demand_low_mm)) > 1e-9:
            raise ValueError("high balance must use low demand")
