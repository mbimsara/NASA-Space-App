"""HTTP contracts for observation-based climate exploration."""

from datetime import date
from typing import Any, Literal

from pydantic import AwareDatetime, Field, FiniteFloat

from app.schemas.farm import StrictSchema


class RainfallScenarioRequest(StrictSchema):
    rainfall_change_pct: FiniteFloat = Field(ge=-100, le=100)


class RainfallScenarioDaily(StrictSchema):
    date: date
    baseline_mm_per_day: float | None = Field(ge=0, allow_inf_nan=False)
    scenario_mm_per_day: float | None = Field(ge=0, allow_inf_nan=False)


class RainfallScenarioTotals(StrictSchema):
    expected_days: int = Field(gt=0)
    valid_days: int = Field(ge=0)
    baseline_rainfall_mm: float | None = Field(ge=0, allow_inf_nan=False)
    scenario_rainfall_mm: float | None = Field(ge=0, allow_inf_nan=False)
    difference_mm: float | None = Field(allow_inf_nan=False)


class RainfallScenarioMonth(RainfallScenarioTotals):
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class ObservationRainfallScenarioResponse(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["hypothetical_rainfall_scenario"]
    observation_id: str
    farm_id: str
    input_version: int = Field(ge=1)
    baseline_data_kind: Literal["observed", "modeled", "synthetic", "mixed"]
    parameters: RainfallScenarioRequest
    baseline_source_refs: list[str] = Field(min_length=1)
    baseline_source_url: str | None
    baseline_retrieved_at: AwareDatetime | None
    summary: RainfallScenarioTotals
    monthly: list[RainfallScenarioMonth]
    daily: list[RainfallScenarioDaily]
    assumptions: list[str]
    limitations: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
