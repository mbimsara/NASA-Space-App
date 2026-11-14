"""Explainable heuristic scoring for feasible rotation candidates."""

from .models import ScoreComponent, ScoredRotation, WaterBudgetRange
from .rotation import RotationCandidate

MODEL_VERSION = "rotation-score-0.1"


def _bounded_percent(value: float) -> float:
    return max(0.0, min(100.0, value))


def score_candidate(
    candidate: RotationCandidate,
    water_budgets: tuple[WaterBudgetRange | None, ...],
    priority_weights: dict[str, float],
) -> ScoredRotation:
    """Score one candidate without treating the score as a yield prediction."""

    if len(water_budgets) != len(candidate.crop_ids):
        raise ValueError("one water-budget slot is required per season/crop")
    requested = {name: float(priority_weights.get(name, 0)) for name in ("water", "soil", "climate")}
    if any(weight < 0 for weight in requested.values()) or sum(requested.values()) <= 0:
        raise ValueError("priority weights must be nonnegative with a positive total")

    known = tuple(budget for budget in water_budgets if budget is not None)
    water_raw = (
        sum(budget.baseline_coverage_low_percent for budget in known) / len(known)
        if len(known) == len(water_budgets)
        else None
    )
    diversity_raw = len(set(candidate.crop_ids)) / len(candidate.crop_ids)
    scenario_present = bool(known) and any(
        budget.scenario_rainfall_mm != budget.baseline_rainfall_mm for budget in known
    )
    climate_raw = (
        sum(budget.coverage_low_percent for budget in known) / len(known)
        if scenario_present and len(known) == len(water_budgets)
        else None
    )
    values = {
        "water": None if water_raw is None else _bounded_percent(water_raw),
        "soil": diversity_raw * 100,
        "climate": None if climate_raw is None else _bounded_percent(climate_raw),
    }
    available_weight = sum(requested[name] for name, value in values.items() if value is not None)
    if available_weight <= 0:
        raise ValueError("no weighted score component is available")

    definitions = {
        "water": ("water_sufficiency", water_raw, "higher_is_better", "Mean conservative baseline water coverage."),
        "soil": ("crop_diversity", diversity_raw, "higher_is_better", "Unique crops divided by sequence length; a soil-diversity proxy."),
        "climate": ("scenario_resilience", climate_raw, "higher_is_better", "Mean conservative water coverage under the hypothetical rainfall scenario."),
    }
    components = []
    total = 0.0
    for key in ("water", "soil", "climate"):
        name, raw, direction, note = definitions[key]
        effective = requested[key] / available_weight if values[key] is not None else 0.0
        component = ScoreComponent(
            name=name,
            value=values[key],
            raw_value=raw,
            requested_weight=requested[key],
            effective_weight=effective,
            direction=direction,
            note=note if values[key] is not None else f"Unavailable: {note}",
        )
        components.append(component)
        if component.value is not None:
            total += component.value * component.effective_weight

    reasons = (
        f"Water sufficiency uses conservative coverage from {len(known)} season(s).",
        f"Crop diversity is {len(set(candidate.crop_ids))}/{len(candidate.crop_ids)}.",
        "This heuristic score is not a yield prediction or crop-success guarantee.",
    )
    return ScoredRotation(
        crop_ids=candidate.crop_ids,
        score=total,
        score_components=tuple(components),
        reasons=reasons,
        model_version=MODEL_VERSION,
    )


def rank_candidates(
    candidates: tuple[tuple[RotationCandidate, tuple[WaterBudgetRange | None, ...]], ...],
    priority_weights: dict[str, float],
) -> tuple[ScoredRotation, ...]:
    scored = [score_candidate(candidate, budgets, priority_weights) for candidate, budgets in candidates]

    def tie_break(result: ScoredRotation) -> tuple:
        water = next(c for c in result.score_components if c.name == "water_sufficiency")
        diversity = next(c for c in result.score_components if c.name == "crop_diversity")
        return (
            -result.score,
            -(water.raw_value if water.raw_value is not None else -1),
            -(diversity.raw_value if diversity.raw_value is not None else -1),
            result.crop_ids,
        )

    return tuple(sorted(scored, key=tie_break))
