"""Rotation requests keep season identity explicit rather than inferring a calendar."""
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.farm import PriorityWeights, StrictSchema


class RotationRequest(StrictSchema):
    input_version: int = Field(ge=1, strict=True)
    observation_id: str = Field(min_length=1)
    seasons: int = Field(ge=3, le=5, strict=True)
    catalog_version: str = Field(min_length=1)
    priority_weights: PriorityWeights
    season_labels: list[Literal["maha", "yala", "inter-season"]] | None = None

    @model_validator(mode="after")
    def matching_seasons(self):
        if self.season_labels is not None and len(self.season_labels) != self.seasons:
            raise ValueError("season_labels must contain exactly seasons entries")
        return self
