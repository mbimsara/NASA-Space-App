"""HTTP contracts for hypothetical climate scenarios of a saved rotation analysis."""

from typing import Literal

from pydantic import AwareDatetime, Field

from app.schemas.climate import RainfallScenarioRequest, RainfallScenarioTotals
from app.schemas.farm import StrictSchema
from app.schemas.rotation import RotationCandidateResponse


class AnalysisScenarioRequest(RainfallScenarioRequest):
    """`rainfall_change_pct` from -100 to 100; the same bounds as observation scenarios."""


class CandidateDifference(StrictSchema):
    rank_baseline: int = Field(ge=1)
    rank_scenario: int = Field(ge=1)
    score_baseline: float | None
    score_scenario: float | None
    score_change: float | None
    water_sufficiency: float | None
    scenario_resilience: float | None


class ObservationRainfallComparison(RainfallScenarioTotals):
    """Whole observation period: original NASA baseline vs uniformly scaled rainfall."""

    period_start: str
    period_end: str


class AnalysisScenarioResponse(StrictSchema):
    schema_version: Literal["0.1"]
    kind: Literal["hypothetical_rotation_scenario"]
    scenario_id: str
    baseline_analysis_id: str
    farm_id: str
    input_version: int = Field(ge=1)
    observation_id: str
    catalog_version: str
    model_version: str
    data_kind: Literal["observed", "modeled", "synthetic", "mixed"]
    baseline_outdated: bool
    created_at: AwareDatetime
    parameters: AnalysisScenarioRequest
    observation_rainfall: ObservationRainfallComparison
    candidates: list[RotationCandidateResponse]
    baseline_differences: dict[str, CandidateDifference]
    assumptions: list[str]
    source_refs: list[str]
    limitations: list[str]
