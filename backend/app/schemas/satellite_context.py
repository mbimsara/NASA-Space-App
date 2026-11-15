"""Contracts for optional GPM IMERG rainfall and HLS vegetation context."""

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from app.schemas.farm import Location, StrictSchema


class ContextPeriod(StrictSchema):
    start: date
    end: date


class GpmCoverage(StrictSchema):
    expected_days: int = Field(gt=0)
    valid_days: int = Field(ge=0)


class GpmDay(StrictSchema):
    date: date
    precipitation_mm: float | None = Field(default=None, ge=0)


class GpmContext(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["gpm_imerg_daily_series"]
    data_kind: Literal["satellite_retrieval"]
    farm_id: str
    input_version: int = Field(ge=1)
    product: Literal["GPM_3IMERGDF"]
    version: Literal["07"]
    units: Literal["mm/day"]
    requested_point: Location
    farm_distance_km: float = Field(ge=0)
    period: ContextPeriod
    spatial_resolution_degrees: float = Field(gt=0)
    coverage: GpmCoverage
    daily: list[GpmDay]
    source_refs: list[str]
    retrieved_at: datetime | None = None
    limitations: list[str]


class HlsCoverage(StrictSchema):
    supplied_observations: int = Field(ge=0)
    accepted_observations: int = Field(ge=0)


class HlsObservation(StrictSchema):
    date: date
    product: Literal["HLSL30", "HLSS30"]
    ndvi: float | None = Field(default=None, ge=-1, le=1)
    cloud_percent: float = Field(ge=0, le=100)
    quality_accepted: bool
    rejection_reason: str | None = None


class HlsContext(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["hls_vegetation_series"]
    data_kind: Literal["satellite_retrieval"]
    farm_id: str
    input_version: int = Field(ge=1)
    products: list[Literal["HLSL30", "HLSS30"]]
    version: Literal["2.0"]
    index: Literal["NDVI"]
    requested_point: Location
    farm_distance_km: float = Field(ge=0)
    spatial_resolution_m: int = Field(gt=0)
    period: ContextPeriod
    coverage: HlsCoverage
    observations: list[HlsObservation]
    source_refs: list[str]
    retrieved_at: datetime | None = None
    limitations: list[str]
