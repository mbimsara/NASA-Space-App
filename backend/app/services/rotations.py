"""Adapter from persisted farm/observation inputs to Bhagya's rotation engine."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from time import time
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.orm import Session

from agrosphere_rotation import generate_candidates, load_catalog, rank_candidates
from agrosphere_rotation.scoring import MODEL_VERSION

from app.models.farm import Farm
from app.models.rotation import RotationAnalysisSnapshot
from app.schemas.observation import ObservationResponse
from app.schemas.rotation import RotationAnalysisResponse, RotationRequest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = REPOSITORY_ROOT / "data" / "catalogs" / "crops.json"


class CatalogVersionConflict(ValueError):
    pass


class AnalysisVersionConflict(ValueError):
    """Farm inputs changed before the analysis could be saved."""


def _candidate_id(crop_ids: tuple[str, ...]) -> str:
    digest = hashlib.sha256("\x1f".join(crop_ids).encode()).hexdigest()[:12]
    return f"candidate-{digest}"


def _unavailable_components(weights: dict[str, float], crop_ids: tuple[str, ...]) -> list[dict]:
    diversity = len(set(crop_ids)) / len(crop_ids) * 100
    soil_weight = weights["soil"]
    effective = 1.0 if soil_weight > 0 else 0.0
    return [
        {"name": "water_sufficiency", "requested_weight": weights["water"], "effective_weight": 0, "value": None, "direction": "higher_is_better"},
        {"name": "crop_diversity", "requested_weight": soil_weight, "effective_weight": effective, "value": diversity, "direction": "higher_is_better"},
        {"name": "scenario_resilience", "requested_weight": weights["climate"], "effective_weight": 0, "value": None, "direction": "higher_is_better"},
    ]


def build_analysis(
    *, farm: Farm, observation: ObservationResponse, request: RotationRequest,
    season_inputs: list[dict] | None = None,
) -> dict:
    """``season_inputs`` (one dated rainfall input per season) enables water screening."""
    if season_inputs is not None:
        return _build_seasonal_analysis(
            farm=farm, observation=observation, request=request, season_inputs=season_inputs,
        )
    catalog_version, crops = load_catalog(CATALOG_PATH)
    if request.catalog_version != catalog_version:
        raise CatalogVersionConflict(
            f"Requested catalog '{request.catalog_version}' does not match server catalog '{catalog_version}'."
        )

    history = sorted(farm.profile.get("crop_history", []), key=lambda item: item["planted_on"])
    previous_crop = history[-1]["crop_id"] if history else None
    generated = generate_candidates(
        crops,
        tuple(request.season_labels),
        excluded_crop_ids=frozenset(farm.profile.get("excluded_crop_ids", [])),
        previous_crop_id=previous_crop,
    )
    weights = request.priority_weights.model_dump()
    crop_by_id = {crop.id: crop for crop in crops}
    candidates = []
    for candidate in generated.candidates:
        # One historical observation window cannot be relabeled as several future
        # seasons. Water remains unknown until dated season inputs are contracted.
        budgets = tuple(None for _ in candidate.crop_ids)
        try:
            scored = rank_candidates(((candidate, budgets),), weights)[0]
            score = scored.score
            components = [
                {
                    "name": component.name,
                    "requested_weight": component.requested_weight,
                    "effective_weight": component.effective_weight,
                    "value": component.value,
                    "direction": component.direction,
                }
                for component in scored.score_components
            ]
            score_reasons = list(scored.reasons)
        except ValueError:
            score = None
            components = _unavailable_components(weights, candidate.crop_ids)
            score_reasons = ["No positively weighted component is available from the supplied inputs."]

        per_season = [
            {
                "season_index": index,
                "season_label": label,
                "crop_id": crop_id,
                "demand_low_mm": None, "demand_nominal_mm": None, "demand_high_mm": None,
                "baseline_rainfall_mm": None, "scenario_rainfall_mm": None,
                "irrigation_mm": farm.profile.get("irrigation_supply_mm_per_season"),
                "baseline_available_water_mm": None,
                "baseline_coverage_low_percent": None, "baseline_coverage_high_percent": None,
                "available_water_mm": None, "balance_low_mm": None, "balance_high_mm": None,
                "coverage_low_percent": None, "coverage_high_percent": None,
                "demand_basis": None, "model_version": None, "source_url": None,
                "assumptions": [],
                "limitations": ["A dated observation period for this future season was not supplied; water screening is unavailable."],
            }
            for index, (label, crop_id) in enumerate(zip(request.season_labels, candidate.crop_ids), 1)
        ]
        candidates.append({
            "candidate_id": _candidate_id(candidate.crop_ids),
            "sequence": [
                {"season_index": index, "crop_id": crop_id, "crop_name": crop_by_id[crop_id].name}
                for index, crop_id in enumerate(candidate.crop_ids, 1)
            ],
            "score": score,
            "score_components": components,
            "water_budget": {
                "period": "season-specific periods unavailable", "demand_mm": None,
                "rainfall_mm": None, "rainfall_total_mm": None, "effective_rainfall_mm": None,
                "irrigation_supply_mm": farm.profile.get("irrigation_supply_mm_per_season"),
                "deficit_mm": None, "unit": "mm",
                "assumptions": ["No effective-rainfall method is approved."],
            },
            "water_budget_range": per_season,
            "reasons": list(candidate.reasons) + score_reasons,
            "constraint_checks": [asdict(check) for check in candidate.constraint_checks],
        })
    candidates.sort(key=lambda value: (value["score"] is None, -(value["score"] or 0), value["candidate_id"]))

    now = datetime.now(timezone.utc)
    return {
        "analysis_id": str(uuid4()), "farm_id": farm.id,
        "input_version": farm.input_version, "observation_id": observation.observation_id,
        "catalog_version": catalog_version, "model_version": MODEL_VERSION,
        "data_kind": observation.data_kind, "created_at": now.isoformat(),
        "candidates": candidates, "reasons": list(generated.reasons),
        "assumptions": [
            "Only reviewed/approved catalog crops are eligible.",
            "Crop diversity is a rotation-structure proxy, not measured soil improvement.",
            "The historical observation window is retained as provenance and is not duplicated across future seasons.",
        ],
        "source_refs": [observation.observation_id, *observation.source_refs],
        "limitations": [
            "Heuristic comparison only; not a yield prediction or crop-success guarantee.",
            "Season-specific water screening requires dated rainfall inputs for each planned season.",
            *observation.limitations,
        ],
    }


def _build_seasonal_analysis(
    *, farm: Farm, observation: ObservationResponse, request: RotationRequest,
    season_inputs: list[dict],
) -> dict:
    """Same candidates and scoring as above, with one dated rainfall input per season."""
    from app.services.season_inputs import load_demands, season_water_row

    catalog_version, crops = load_catalog(CATALOG_PATH)
    if request.catalog_version != catalog_version:
        raise CatalogVersionConflict(
            f"Requested catalog '{request.catalog_version}' does not match server catalog '{catalog_version}'."
        )
    if len(season_inputs) != len(request.season_labels):
        raise ValueError("One season input is required per planned season.")
    water_model_version, demands = load_demands()

    history = sorted(farm.profile.get("crop_history", []), key=lambda item: item["planted_on"])
    previous_crop = history[-1]["crop_id"] if history else None
    generated = generate_candidates(
        crops,
        tuple(request.season_labels),
        excluded_crop_ids=frozenset(farm.profile.get("excluded_crop_ids", [])),
        previous_crop_id=previous_crop,
    )
    weights = request.priority_weights.model_dump()
    irrigation = farm.profile.get("irrigation_supply_mm_per_season")
    crop_by_id = {crop.id: crop for crop in crops}
    candidates = []
    for candidate in generated.candidates:
        per_season, budgets = [], []
        for season, crop_id in zip(season_inputs, candidate.crop_ids):
            row, budget = season_water_row(season, crop_id, irrigation_mm=irrigation, demands=demands)
            per_season.append(row)
            budgets.append(budget)
        try:
            scored = rank_candidates(((candidate, tuple(budgets)),), weights)[0]
            score = scored.score
            components = [
                {
                    "name": component.name,
                    "requested_weight": component.requested_weight,
                    "effective_weight": component.effective_weight,
                    "value": component.value,
                    "direction": component.direction,
                }
                for component in scored.score_components
            ]
            score_reasons = list(scored.reasons)
        except ValueError:
            score = None
            components = _unavailable_components(weights, candidate.crop_ids)
            score_reasons = ["No positively weighted component is available from the supplied inputs."]

        candidates.append({
            "candidate_id": _candidate_id(candidate.crop_ids),
            "sequence": [
                {"season_index": index, "crop_id": crop_id, "crop_name": crop_by_id[crop_id].name}
                for index, crop_id in enumerate(candidate.crop_ids, 1)
            ],
            "score": score,
            "score_components": components,
            "water_budget": {
                "period": "season-specific periods; see water_budget_range", "demand_mm": None,
                "rainfall_mm": None, "rainfall_total_mm": None, "effective_rainfall_mm": None,
                "irrigation_supply_mm": irrigation,
                "deficit_mm": None, "unit": "mm",
                "assumptions": ["No effective-rainfall method is approved.",
                                "Each season uses its own dated rainfall period; no plan-level total is formed."],
            },
            "water_budget_range": per_season,
            "reasons": list(candidate.reasons) + score_reasons,
            "constraint_checks": [asdict(check) for check in candidate.constraint_checks],
        })
    candidates.sort(key=lambda value: (value["score"] is None, -(value["score"] or 0), value["candidate_id"]))

    kinds = {observation.data_kind, *(season["data_kind"] for season in season_inputs)}
    source_refs = [observation.observation_id]
    for season in season_inputs:
        source_refs += [season["observation_id"], *season["source_refs"]]
    source_refs += list(observation.source_refs)
    limitations = [
        "Heuristic comparison only; not a yield prediction or crop-success guarantee.",
        "Season rainfall comes from historical reference periods, not forecasts of the planned seasons.",
        "Total rainfall is provisionally treated as available; effective rainfall is not modeled.",
    ]
    if irrigation is None:
        limitations.append("Irrigation is unknown, so water sufficiency and scenario resilience are unavailable.")
    now = datetime.now(timezone.utc)
    return {
        "analysis_id": str(uuid4()), "farm_id": farm.id,
        "input_version": farm.input_version, "observation_id": observation.observation_id,
        "catalog_version": catalog_version, "model_version": MODEL_VERSION,
        "data_kind": kinds.pop() if len(kinds) == 1 else "mixed",
        "created_at": now.isoformat(),
        "candidates": candidates, "reasons": list(generated.reasons),
        "assumptions": [
            "Only reviewed/approved catalog crops are eligible.",
            "Crop diversity is a rotation-structure proxy, not measured soil improvement.",
            "Each planned season uses rainfall from its own dated historical period; "
            "one rainfall total is never reused for several seasons.",
            f"Crop-water demand ranges use {water_model_version} (seasonal ETc basis).",
        ],
        "source_refs": list(dict.fromkeys(source_refs)),
        "limitations": limitations + list(observation.limitations),
        "season_inputs": season_inputs,
    }


def persist_analysis(db: Session, payload: dict) -> RotationAnalysisResponse:
    validated = RotationAnalysisResponse.model_validate(payload)
    stored = validated.model_dump(mode="json")
    # End the read transaction, then acquire the SQLite writer lock while
    # atomically validating the original input version. A prior SELECT/refresh
    # alone leaves a race between the last version check and the INSERT.
    db.rollback()
    result = db.execute(update(Farm).where(
        Farm.id == validated.farm_id, Farm.input_version == validated.input_version,
    ).values(input_version=Farm.input_version))
    if result.rowcount != 1:
        db.rollback()
        raise AnalysisVersionConflict("Farm changed while the analysis was running. Try again.")
    db.add(RotationAnalysisSnapshot(
        id=validated.analysis_id, farm_id=validated.farm_id,
        input_version=validated.input_version, observation_id=validated.observation_id,
        created_at=time(), payload=stored,
    ))
    db.commit()
    return validated
