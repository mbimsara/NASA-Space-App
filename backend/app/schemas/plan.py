"""Saved-plan contracts compatible with Shehani's API client."""
from typing import Any

from pydantic import AwareDatetime, Field

from app.schemas.farm import StrictSchema


class PlanRequest(StrictSchema):
    analysis_id: str = Field(min_length=1)
    scenario_id: str | None = Field(default=None, min_length=1)
    candidate_id: str = Field(min_length=1)
    expected_input_version: int = Field(ge=1, strict=True)


class PlanCreated(StrictSchema):
    plan_id: str


class PlanResponse(StrictSchema):
    plan_id: str
    farm_id: str
    analysis_id: str
    scenario_id: str | None
    candidate_id: str
    input_version: int
    created_at: AwareDatetime
    observation_id: str
    # Snapshots are preserved verbatim, including future model-specific fields.
    candidate_snapshot: dict[str, Any]
    input_snapshot: dict[str, Any]
    analysis_snapshot: dict[str, Any]
    scenario_snapshot: dict[str, Any] | None
    observation_snapshot: dict[str, Any]
