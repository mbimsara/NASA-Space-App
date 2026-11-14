"""HTTP contracts around Matheesha's normalized POWER observations."""

from datetime import date, datetime, timezone
import re
from typing import Any, Literal

from pydantic import AwareDatetime, ConfigDict, Field, FiniteFloat, field_validator, model_validator

from app.schemas.farm import Location, StrictSchema


class ObservationQuery(StrictSchema):
    start: date
    end: date

    @field_validator("start", "end", mode="before")
    @classmethod
    def require_iso_date(cls, value):
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Use a calendar date in YYYY-MM-DD format.")
        return value

    @model_validator(mode="after")
    def validate_period(self):
        if self.start > self.end:
            raise ValueError("Start date must not be later than end date.")
        if self.start < date(1981, 1, 1):
            raise ValueError("NASA POWER historical dates start at 1981-01-01.")
        if self.end >= datetime.now(timezone.utc).date():
            raise ValueError("End date must be before today in UTC.")
        return self


class ObservationPeriod(StrictSchema):
    start: date
    end: date


class ObservationCoverage(StrictSchema):
    expected_days: int = Field(gt=0)
    available_days: int = Field(ge=0)
    temperature_valid_days: int = Field(ge=0)
    precipitation_valid_days: int = Field(ge=0)


class ObservationSummary(StrictSchema):
    # Preserve additional summary fields supplied by Matheesha's normalizer.
    model_config = ConfigDict(extra="allow")
    rainfall_mm: float | None = Field(ge=0, allow_inf_nan=False)
    rainfall_total_mm: float | None = Field(ge=0, allow_inf_nan=False)
    rainfall_available_days_mm: float | None = Field(ge=0, allow_inf_nan=False)
    mean_temperature_c: float | None = Field(allow_inf_nan=False)


class DailyObservation(StrictSchema):
    date: date
    temperature_c: float | None = Field(allow_inf_nan=False)
    precipitation_mm_per_day: float | None = Field(ge=0, allow_inf_nan=False)
    temperature_max_c: float | None = Field(default=None, allow_inf_nan=False)
    temperature_min_c: float | None = Field(default=None, allow_inf_nan=False)


class ObservationResponse(StrictSchema):
    schema_version: Literal["0.1"]
    observation_id: str
    farm_id: str
    input_version: int = Field(ge=1)
    data_kind: Literal["observed", "modeled", "synthetic", "mixed"]
    provider: str = Field(min_length=1)
    period: ObservationPeriod
    retrieved_at: AwareDatetime | None
    source_refs: list[str] = Field(min_length=1)
    source_url: str | None
    documentation_url: str
    api: dict[str, Any]
    parameter_metadata: dict[str, Any]
    spatial_resolution: dict[str, Any] | None
    time_standard: Literal["UTC"]
    requested_location: Location
    coordinates: list[FiniteFloat] = Field(min_length=2)
    coverage: ObservationCoverage
    summary: ObservationSummary
    daily: list[DailyObservation]
    monthly: list[dict[str, Any]]
    units: dict[str, str]
    aggregation_method: dict[str, str]
    missing_data: dict[str, list[date]]
    limitations: list[str]
