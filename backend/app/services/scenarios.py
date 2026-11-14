"""Hypothetical rainfall scenarios recomputed from an immutable rotation analysis.

The saved analysis and its NASA observation snapshot are read-only inputs. A
scenario scales rainfall in memory, re-runs Bhagya's water-budget and scoring
functions, and is persisted as a new snapshot that references the baseline.
"""

from copy import deepcopy
from datetime import datetime, timezone
from time import time
from uuid import uuid4

from sqlalchemy.orm import Session

from agrosphere_rotation import (
    ClimateInput,
    ConstraintCheck,
    RotationCandidate,
    WaterDemandRange,
    calculate_water_budget_range,
    score_candidate,
)

from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysisSnapshot
from app.models.scenario import RotationScenarioSnapshot
from app.schemas.scenario import AnalysisScenarioResponse
from app.services.observation_cache import snapshot_response
from app.services.rotations import _unavailable_components
from services.climate import rainfall_scenario


WEIGHT_KEYS = {"water_sufficiency": "water", "crop_diversity": "soil", "scenario_resilience": "climate"}
SEASON_INPUTS = (
    "demand_low_mm", "demand_nominal_mm", "demand_high_mm", "baseline_rainfall_mm",
    "irrigation_mm", "demand_basis", "model_version", "source_url",
)
UNKNOWN_SEASON_NOTE = (
    "Scenario water screening is unavailable for this season because its baseline "
    "rainfall, irrigation or crop-demand input is unknown."
)


class AnalysisNotFound(LookupError):
    pass


class ScenarioNotFound(LookupError):
    pass


def _requested_weights(candidate: dict) -> dict[str, float]:
    weights = {"water": 0.0, "soil": 0.0, "climate": 0.0}
    for component in candidate["score_components"]:
        key = WEIGHT_KEYS.get(component["name"])
        if key is not None:
            weights[key] = float(component["requested_weight"])
    return weights


def _season_climate(row: dict, change_pct: float, period: dict, data_kind: str) -> ClimateInput:
    return ClimateInput(
        rainfall_mm=row["baseline_rainfall_mm"],
        irrigation_mm=row["irrigation_mm"],
        irrigation_basis="field_applied_depth",
        rainfall_change_percent=change_pct,
        source="Saved rotation analysis season input",
        observation_start=str(period["start"]),
        observation_end=str(period["end"]),
        data_kind=data_kind,
    )


def _recalculate_season(row: dict, change_pct: float, period: dict, data_kind: str):
    """Return (scenario row, engine budget or None). The baseline row is never mutated."""

    updated = deepcopy(row)
    if any(row.get(key) is None for key in SEASON_INPUTS):
        updated["scenario_rainfall_mm"] = None
        for key in ("available_water_mm", "balance_low_mm", "balance_high_mm",
                    "coverage_low_percent", "coverage_high_percent"):
            updated[key] = None
        if UNKNOWN_SEASON_NOTE not in updated["limitations"]:
            updated["limitations"].append(UNKNOWN_SEASON_NOTE)
        return updated, None

    demand = WaterDemandRange(
        crop_id=row["crop_id"], low_mm=row["demand_low_mm"], nominal_mm=row["demand_nominal_mm"],
        high_mm=row["demand_high_mm"], basis=row["demand_basis"],
        model_version=row["model_version"], source_url=row["source_url"],
    )
    budget = calculate_water_budget_range(demand, _season_climate(row, change_pct, period, data_kind))
    updated.update({
        "baseline_rainfall_mm": budget.baseline_rainfall_mm,
        "scenario_rainfall_mm": budget.scenario_rainfall_mm,
        "irrigation_mm": budget.irrigation_mm,
        "baseline_available_water_mm": budget.baseline_available_water_mm,
        "baseline_coverage_low_percent": budget.baseline_coverage_low_percent,
        "baseline_coverage_high_percent": budget.baseline_coverage_high_percent,
        "available_water_mm": budget.available_water_mm,
        "balance_low_mm": budget.balance_low_mm,
        "balance_high_mm": budget.balance_high_mm,
        "coverage_low_percent": budget.coverage_low_percent,
        "coverage_high_percent": budget.coverage_high_percent,
        "assumptions": list(budget.assumptions),
    })
    return updated, budget


def _recalculate_candidate(candidate: dict, change_pct: float, period: dict, data_kind: str) -> dict:
    rows, budgets = [], []
    for row in candidate["water_budget_range"]:
        updated, budget = _recalculate_season(row, change_pct, period, data_kind)
        rows.append(updated)
        budgets.append(budget)

    crop_ids = tuple(step["crop_id"] for step in candidate["sequence"])
    engine_candidate = RotationCandidate(
        crop_ids=crop_ids,
        reasons=(),
        constraint_checks=tuple(ConstraintCheck(**check) for check in candidate["constraint_checks"]),
    )
    weights = _requested_weights(candidate)
    try:
        scored = score_candidate(engine_candidate, tuple(budgets), weights)
        score = scored.score
        components = [
            {
                "name": component.name, "requested_weight": component.requested_weight,
                "effective_weight": component.effective_weight, "value": component.value,
                "direction": component.direction,
            }
            for component in scored.score_components
        ]
        score_reasons = list(scored.reasons)
    except ValueError:
        score = None
        components = _unavailable_components(weights, crop_ids)
        score_reasons = ["No positively weighted component is available from the supplied inputs."]

    # Keep the generator's feasibility reasons; replace only the score explanation.
    baseline_reasons = [
        reason for reason in candidate["reasons"]
        if not reason.startswith(("Water sufficiency uses", "Crop diversity is", "This heuristic score",
                                  "No positively weighted component"))
    ]
    return {
        **deepcopy(candidate),
        "score": score,
        "score_components": components,
        "water_budget_range": rows,
        "reasons": baseline_reasons + score_reasons
        + [f"Hypothetical rainfall change of {change_pct:+g}% applied to the baseline seasons."],
    }


def _component(candidate: dict, name: str) -> float | None:
    return next((c["value"] for c in candidate["score_components"] if c["name"] == name), None)


def build_scenario(
    *, analysis: RotationAnalysisSnapshot, observation: ObservationSnapshot,
    farm: Farm | None, change_pct: float,
) -> dict:
    baseline = deepcopy(analysis.payload)
    observed = snapshot_response(observation).model_dump(mode="json")
    rainfall = rainfall_scenario(observed, change_pct)
    period = observed["period"]

    candidates = [
        _recalculate_candidate(candidate, change_pct, period, baseline["data_kind"])
        for candidate in baseline["candidates"]
    ]
    candidates.sort(key=lambda value: (value["score"] is None, -(value["score"] or 0), value["candidate_id"]))

    baseline_rank = {c["candidate_id"]: index for index, c in enumerate(baseline["candidates"], 1)}
    baseline_by_id = {c["candidate_id"]: c for c in baseline["candidates"]}
    differences = {}
    for rank, candidate in enumerate(candidates, 1):
        before = baseline_by_id[candidate["candidate_id"]]
        known = candidate["score"] is not None and before["score"] is not None
        differences[candidate["candidate_id"]] = {
            "rank_baseline": baseline_rank[candidate["candidate_id"]],
            "rank_scenario": rank,
            "score_baseline": before["score"],
            "score_scenario": candidate["score"],
            "score_change": candidate["score"] - before["score"] if known else None,
            "water_sufficiency": _component(candidate, "water_sufficiency"),
            "scenario_resilience": _component(candidate, "scenario_resilience"),
        }

    outdated = farm is None or farm.input_version != baseline["input_version"]
    limitations = [
        f"Hypothetical scenario: rainfall {change_pct:+g}% relative to the baseline. "
        "Not a weather, yield or crop-success forecast.",
        "The saved analysis and the original NASA observation snapshot are unchanged.",
    ]
    if any(_component(c, "scenario_resilience") is None for c in candidates):
        limitations.append(
            "Scenario resilience is unknown where season water inputs are missing or the rainfall change is 0%; "
            "an unchanged score does not mean the scenario has no impact."
        )
    if outdated:
        limitations.append("The farm profile changed after the baseline analysis; this scenario uses the older inputs.")

    return {
        "schema_version": "0.1",
        "kind": "hypothetical_rotation_scenario",
        "scenario_id": str(uuid4()),
        "baseline_analysis_id": baseline["analysis_id"],
        "farm_id": baseline["farm_id"],
        "input_version": baseline["input_version"],
        "observation_id": baseline["observation_id"],
        "catalog_version": baseline["catalog_version"],
        "model_version": baseline["model_version"],
        "data_kind": baseline["data_kind"],
        "baseline_outdated": outdated,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": {"rainfall_change_pct": change_pct},
        "observation_rainfall": {
            "period_start": str(period["start"]), "period_end": str(period["end"]),
            **rainfall["summary"],
        },
        "candidates": candidates,
        "baseline_differences": differences,
        "assumptions": [
            *rainfall["assumptions"][:2],
            "Season water budgets are recomputed with the rotation engine from the saved baseline season inputs.",
            "Requested priority weights are reused from the baseline; effective weights are renormalized.",
        ],
        "source_refs": [baseline["analysis_id"], *baseline["source_refs"]],
        "limitations": limitations + list(baseline["limitations"]),
    }


def get_analysis(db: Session, analysis_id: str) -> RotationAnalysisSnapshot:
    analysis = db.get(RotationAnalysisSnapshot, analysis_id)
    if analysis is None:
        raise AnalysisNotFound(analysis_id)
    return analysis


def persist_scenario(db: Session, payload: dict) -> AnalysisScenarioResponse:
    validated = AnalysisScenarioResponse.model_validate(payload)
    db.add(RotationScenarioSnapshot(
        id=validated.scenario_id, analysis_id=validated.baseline_analysis_id,
        farm_id=validated.farm_id, input_version=validated.input_version,
        observation_id=validated.observation_id,
        rainfall_change_pct=validated.parameters.rainfall_change_pct,
        created_at=time(), payload=validated.model_dump(mode="json"),
    ))
    db.commit()
    return validated


def get_scenario(db: Session, scenario_id: str) -> AnalysisScenarioResponse:
    stored = db.get(RotationScenarioSnapshot, scenario_id)
    if stored is None:
        raise ScenarioNotFound(scenario_id)
    return AnalysisScenarioResponse.model_validate(stored.payload)
