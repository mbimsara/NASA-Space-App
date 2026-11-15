from typing import Literal

from pydantic import Field

from app.schemas.farm import Location, StrictSchema


class ClimateTwin(StrictSchema):
    farm_id: str
    observation_id: str
    input_version: int = Field(ge=1)
    requested_location: Location
    mean_temperature_c: float
    rainfall_total_mm: float = Field(ge=0)
    temperature_difference_c: float
    rainfall_difference_mm: float
    similarity_score: float = Field(ge=0, le=100)


class ClimateTwinExclusion(StrictSchema):
    observation_id: str | None
    reason: Literal["period_mismatch", "same_farm", "incomplete_climate_summary"]


class ClimateTwinsResponse(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["historical_climate_twins"]
    farm_id: str
    observation_id: str
    period: dict[str, str]
    twins: list[ClimateTwin]
    excluded: list[ClimateTwinExclusion]
    source_refs: list[str]
    assumptions: list[str]
    limitations: list[str]
