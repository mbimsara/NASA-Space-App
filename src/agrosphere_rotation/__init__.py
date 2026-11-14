"""AgroSphere crop-rotation and agronomy engine."""

from .catalog import load_catalog
from .models import ClimateInput, Crop, Season, WaterBudget
from .rotation import (
    CandidateGenerationResult,
    RepeatPolicy,
    RotationCandidate,
    generate_candidates,
)
from .water import calculate_water_budget

__all__ = [
    "ClimateInput",
    "Crop",
    "CandidateGenerationResult",
    "RepeatPolicy",
    "RotationCandidate",
    "Season",
    "WaterBudget",
    "calculate_water_budget",
    "generate_candidates",
    "load_catalog",
]
