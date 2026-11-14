"""AgroSphere crop-rotation and agronomy engine."""

from .catalog import load_catalog
from .models import (
    ClimateInput,
    Crop,
    Season,
    WaterBudget,
    WaterBudgetRange,
    WaterDemandRange,
)
from .rotation import (
    CandidateGenerationResult,
    RepeatPolicy,
    RotationCandidate,
    generate_candidates,
)
from .water import calculate_water_budget, calculate_water_budget_range
from .water_requirements import load_water_requirements

__all__ = [
    "ClimateInput",
    "Crop",
    "CandidateGenerationResult",
    "RepeatPolicy",
    "RotationCandidate",
    "Season",
    "WaterBudget",
    "WaterBudgetRange",
    "WaterDemandRange",
    "calculate_water_budget",
    "calculate_water_budget_range",
    "generate_candidates",
    "load_catalog",
    "load_water_requirements",
]
