"""HTTP boundary for Akash's English-only recorded-fact explainer."""
from typing import Literal

from pydantic import Field

from app.schemas.farm import StrictSchema


class AssistantRequest(StrictSchema):
    farm_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    scenario_id: str | None = Field(default=None, min_length=1)
    candidate_id: str | None = Field(default=None, min_length=1)
    language: Literal["en"]
    message: str = Field(min_length=1)


class AssistantResponse(StrictSchema):
    role: Literal["assistant"]
    content: str
    source_ids: list[str]
    limitations: list[str]
    status: Literal["answered", "insufficient_context", "unsupported_question"]
    language: Literal["en"]
    assumptions: list[str]
