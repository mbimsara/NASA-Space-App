"""A hypothetical rainfall adjustment; it never edits observations."""
from pydantic import Field

from app.schemas.farm import StrictSchema


class ScenarioRequest(StrictSchema):
    rainfall_change_pct: float = Field(ge=-100, le=100, allow_inf_nan=False, strict=True)
