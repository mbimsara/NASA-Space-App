"""Contracts for quality-filtered regional SMAP surface-moisture context."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.farm import Location, StrictSchema


class SmapPass(StrictSchema):
    pass_name: Literal["AM", "PM"] = Field(alias="pass")
    accepted: bool
    soil_moisture_m3_m3: float | None = Field(default=None, ge=0, le=1)
    rejection_reason: str | None = None
    pixel_latitude: float | None = Field(default=None, ge=-90, le=90)
    pixel_longitude: float | None = Field(default=None, ge=-180, le=180)
    distance_km: float | None = Field(default=None, ge=0)
    subset_array_index: list[int] | None = None
    acquisition_time_utc_raw: str | None = None
    surface_flag: int | None = None
    input_units: str | None = None
    retrieval_quality_flag: int | None = None


class SmapDay(StrictSchema):
    date: date
    granule_supplied: bool
    AM: SmapPass
    PM: SmapPass


class SmapPeriod(StrictSchema):
    start: date
    end: date


class SmapCoverage(StrictSchema):
    expected_days: int = Field(gt=0)
    supplied_granule_days: int = Field(ge=0)
    accepted_AM: int = Field(ge=0)
    accepted_PM: int = Field(ge=0)


class SoilMoistureResponse(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["smap_surface_soil_moisture_series"]
    data_kind: Literal["satellite_retrieval"]
    farm_id: str
    input_version: int = Field(ge=1)
    product: Literal["SPL3SMP_E"]
    version: Literal["006"]
    units: Literal["m3/m3"]
    requested_point: Location
    farm_distance_km: float = Field(ge=0)
    period: SmapPeriod
    max_distance_km: float = Field(gt=0)
    coverage: SmapCoverage
    daily: list[SmapDay]
    source_refs: list[str]
    limitations: list[str]
