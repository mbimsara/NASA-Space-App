from datetime import date
from typing import Literal

from pydantic import Field, FiniteFloat, model_validator

from app.schemas.farm import StrictSchema


class FeedbackRequest(StrictSchema):
    season_index: int = Field(ge=1, le=5)
    planted_on: date | None = None
    harvested_on: date | None = None
    actual_crop_id: str | None = Field(default=None, min_length=1, max_length=100)
    yield_value: FiniteFloat | None = Field(default=None, ge=0)
    yield_unit: Literal["kg", "kg/ha", "t", "t/ha"] | None = None
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def consistent(self):
        if (self.yield_value is None) != (self.yield_unit is None):
            raise ValueError("yield_value and yield_unit must be supplied together")
        if self.planted_on and self.harvested_on and self.harvested_on < self.planted_on:
            raise ValueError("harvested_on cannot precede planted_on")
        return self


class FeedbackResponse(FeedbackRequest):
    schema_version: Literal["0.1"]
    feedback_id: str
    plan_id: str
    data_kind: Literal["farmer_input"]
    created_at: str
    limitations: list[str]
