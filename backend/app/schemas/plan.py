"""Saved plan contracts, including the existing frontend's metadata snapshot."""
from typing import Any

from pydantic import AwareDatetime, Field

from app.schemas.farm import StrictSchema


class PlanRequest(StrictSchema):
    analysis_id: str = Field(min_length=1)
    scenario_id: str | None = Field(default=None, min_length=1)
    candidate_id: str = Field(min_length=1)
    expected_input_version: int = Field(ge=1, strict=True)


class PlanCreateRequest(PlanRequest):
    farm_id: str = Field(min_length=1)


class PlanCreated(StrictSchema):
    plan_id: str


class PlanResponse(StrictSchema):
    plan_id: str
    farm_id: str
    analysis_id: str
    scenario_id: str | None
    observation_id: str
    candidate_id: str
    input_version: int
    created_at: AwareDatetime
    input_snapshot: dict[str, Any]
    candidate_snapshot: dict[str, Any]
    analysis_snapshot: dict[str, Any]
    analysis_result_snapshot: dict[str, Any]
    scenario_snapshot: dict[str, Any] | None
    observation_snapshot: dict[str, Any]
