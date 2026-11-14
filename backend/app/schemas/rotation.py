"""Strict HTTP contracts for immutable rotation analyses."""

from datetime import date
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from app.schemas.farm import PriorityWeights, StrictSchema


SeasonLabel = Literal["maha", "yala", "inter-season"]


class SeasonPeriodRequest(StrictSchema):
    """Inclusive historical reference period (UTC dates) for one planned season."""

    start: date
    end: date


class SeasonInputResponse(StrictSchema):
    season_index: int = Field(ge=1)
    season_label: SeasonLabel
    period_start: date
    period_end: date
    period_source: Literal["season_calendar", "request"]
    observation_id: str
    data_kind: Literal["observed", "modeled", "synthetic", "mixed"]
    expected_days: int = Field(gt=0)
    rainfall_valid_days: int = Field(ge=0)
    rainfall_total_mm: float | None = Field(ge=0, allow_inf_nan=False)
    source_refs: list[str]
    limitations: list[str]


class RotationRequest(StrictSchema):
    input_version: int = Field(ge=1, strict=True)
    observation_id: str = Field(min_length=1)
    seasons: int = Field(ge=3, le=5, strict=True)
    season_labels: list[SeasonLabel]
    catalog_version: str = Field(min_length=1)
    priority_weights: PriorityWeights
    # Optional season-specific water inputs. Omitted: water stays unknown (original
    # behavior). "calendar": the server picks the latest matching historical season
    # for each planned season. A list: one explicit chronological period per season.
    season_periods: Literal["calendar"] | list[SeasonPeriodRequest] | None = None

    @model_validator(mode="after")
    def labels_match_seasons(self):
        if len(self.season_labels) != self.seasons:
            raise ValueError("season_labels must have one label per season")
        return self


class SequenceStep(StrictSchema):
    season_index: int = Field(ge=1)
    crop_id: str
    crop_name: str | None = None


class ScoreComponentResponse(StrictSchema):
    name: str
    requested_weight: float = Field(ge=0)
    effective_weight: float = Field(ge=0)
    value: float | None = Field(default=None, ge=0, le=100)
    direction: Literal["higher_is_better", "lower_is_better"]


class ConstraintCheckResponse(StrictSchema):
    rule: str
    passed: bool
    note: str | None


class WaterBudgetResponse(StrictSchema):
    period: str
    demand_mm: float | None
    rainfall_mm: float | None
    rainfall_total_mm: float | None
    effective_rainfall_mm: float | None
    irrigation_supply_mm: float | None
    deficit_mm: float | None
    unit: Literal["mm"]
    assumptions: list[str]


class WaterBudgetRangeResponse(StrictSchema):
    season_index: int
    season_label: SeasonLabel
    crop_id: str
    demand_low_mm: float | None
    demand_nominal_mm: float | None
    demand_high_mm: float | None
    baseline_rainfall_mm: float | None
    scenario_rainfall_mm: float | None
    irrigation_mm: float | None
    baseline_available_water_mm: float | None
    baseline_coverage_low_percent: float | None
    baseline_coverage_high_percent: float | None
    available_water_mm: float | None
    balance_low_mm: float | None
    balance_high_mm: float | None
    coverage_low_percent: float | None
    coverage_high_percent: float | None
    demand_basis: str | None
    model_version: str | None
    source_url: str | None
    assumptions: list[str]
    limitations: list[str]


class RotationCandidateResponse(StrictSchema):
    candidate_id: str
    sequence: list[SequenceStep]
    score: float | None = Field(default=None, ge=0, le=100)
    score_components: list[ScoreComponentResponse]
    water_budget: WaterBudgetResponse
    water_budget_range: list[WaterBudgetRangeResponse]
    reasons: list[str]
    constraint_checks: list[ConstraintCheckResponse]


class RotationAnalysisResponse(StrictSchema):
    analysis_id: str
    farm_id: str
    input_version: int = Field(ge=1)
    observation_id: str
    catalog_version: str
    model_version: str
    data_kind: Literal["observed", "modeled", "synthetic", "mixed"]
    created_at: AwareDatetime
    candidates: list[RotationCandidateResponse]
    reasons: list[str]
    assumptions: list[str]
    source_refs: list[str]
    limitations: list[str]
    # Present only when season_periods was requested; one dated rainfall input per season.
    season_inputs: list[SeasonInputResponse] = Field(default_factory=list)
