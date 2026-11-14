
from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class StrictSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )


class Location(StrictSchema):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CropHistory(StrictSchema):
    crop_id: str = Field(min_length=1)
    planted_on: date
    harvested_on: date | None

    @model_validator(mode="after")
    def check_dates(self):
        if self.harvested_on is not None:
            if self.harvested_on < self.planted_on:
                raise ValueError(
                    "Harvest date cannot be before planting date"
                )
        return self


class SoilTest(StrictSchema):
    metric: str = Field(min_length=1)
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1)
    sampled_on: date


class PriorityWeights(StrictSchema):
    water: float = Field(ge=0, allow_inf_nan=False)
    soil: float = Field(ge=0, allow_inf_nan=False)
    climate: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def normalize_weights(self):
        total = self.water + self.soil + self.climate

        if total <= 0:
            raise ValueError(
                "At least one priority weight must be positive"
            )

        self.water /= total
        self.soil /= total
        self.climate /= total

        return self


class FarmProfile(StrictSchema):
    schema_version: Literal["0.1"]
    data_kind: Literal["synthetic", "farmer_input"]
    name: str = Field(min_length=1)
    location: Location
    area_ha: float = Field(gt=0, allow_inf_nan=False)
    irrigation_supply_mm_per_season: float | None = Field(
        ge=0, allow_inf_nan=False
    )
    crop_history: list[CropHistory]
    soil_tests: list[SoilTest]
    priority_weights: PriorityWeights
    excluded_crop_ids: list[str]

    @field_validator("excluded_crop_ids")
    @classmethod
    def check_excluded_crops(cls, values):
        if any(not value.strip() for value in values):
            raise ValueError("Crop IDs cannot be empty")

        if len(values) != len(set(values)):
            raise ValueError("Duplicate crop IDs are not allowed")

        return values


class FarmResponse(StrictSchema):
    id: str
    input_version: int
    profile: FarmProfile


class FarmUpdateRequest(StrictSchema):
    expected_input_version: int = Field(ge=1)
    profile: FarmProfile
