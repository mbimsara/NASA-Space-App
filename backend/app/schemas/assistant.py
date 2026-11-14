"""Confirmed frontend assistant request and response contract."""
from typing import Literal

from pydantic import Field

from app.schemas.farm import StrictSchema


class AssistantRequest(StrictSchema):
    farm_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    scenario_id: str | None = Field(default=None, min_length=1)
    candidate_id: str | None = Field(default=None, min_length=1)
    language: Literal["en"]
    message: str = Field(min_length=1, max_length=2000)


class AssistantContextMetadata(StrictSchema):
    farm_id: str
    analysis_id: str | None
    scenario_id: str | None
    candidate_id: str | None


class AssistantResponse(StrictSchema):
    role: Literal["assistant"]
    content: str
    source_ids: list[str]
    limitations: list[str]
    status: str | None = None
    language: Literal["en"] = "en"
    assumptions: list[str] = Field(default_factory=list)
    context: AssistantContextMetadata | None = None
