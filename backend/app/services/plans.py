"""Save exact historical inputs/results; retrieval never consults mutable sources."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import update

from app.models.farm import Farm
from app.models.plan import SavedPlanSnapshot
from app.schemas.plan import PlanResponse
from app.schemas.observation import ObservationResponse
from app.services.snapshot_context import (
    SelectionError, candidate, require, resolve_context, validate_payloads,
)


def analysis_metadata(analysis, selected):
    metadata = {key: deepcopy(selected[key]) for key in (
        "catalog_version", "model_version", "data_kind", "source_refs", "assumptions", "limitations")}
    metadata["analysis_created_at"] = analysis["created_at"]
    metadata["limitations"].append(
        "The original analysis request and full catalog input bundle were not persisted by the analysis API; they have not been reconstructed.")
    return metadata


def save_plan(db, farm_id, request):
    context = resolve_context(
        db, farm_id=farm_id, analysis_id=request.analysis_id,
        scenario_id=request.scenario_id, candidate_id=request.candidate_id,
    )
    if context["input_version"] != request.expected_input_version:
        raise SelectionError(409, "VERSION_CONFLICT", "Farm input version is outdated.")
    analysis = context["analysis"]
    selected = context.get("scenario", analysis)
    now = datetime.now(timezone.utc)
    plan_id = str(uuid4())
    metadata = analysis_metadata(analysis, selected)
    payload = {
        "plan_id": plan_id, "farm_id": farm_id, "analysis_id": request.analysis_id,
        "scenario_id": request.scenario_id, "observation_id": analysis["observation_id"],
        "candidate_id": request.candidate_id, "input_version": context["input_version"],
        "created_at": now.isoformat(), "input_snapshot": context["profile"],
        "candidate_snapshot": deepcopy(candidate(selected, request.candidate_id)),
        "analysis_snapshot": metadata, "analysis_result_snapshot": analysis,
        "scenario_snapshot": context.get("scenario"), "observation_snapshot": context["observations"],
    }
    PlanResponse.model_validate(deepcopy(payload))
    # End the read transaction; acquire SQLite's writer lock and atomically
    # recheck the farm version before inserting. Never update a saved plan.
    db.rollback()
    result = db.execute(update(Farm).where(
        Farm.id == farm_id, Farm.input_version == request.expected_input_version,
    ).values(input_version=Farm.input_version))
    if result.rowcount != 1:
        db.rollback()
        raise SelectionError(409, "VERSION_CONFLICT", "Farm changed while the plan was being saved.")
    db.add(SavedPlanSnapshot(
        id=plan_id, farm_id=farm_id, analysis_id=request.analysis_id,
        scenario_id=request.scenario_id, observation_id=analysis["observation_id"],
        candidate_id=request.candidate_id, input_version=context["input_version"],
        created_at=now.timestamp(), payload=deepcopy(payload),
    ))
    db.commit()
    return {"plan_id": plan_id}


def stored_plan(row):
    """Validate only embedded records: later farm edits cannot change history."""
    payload = deepcopy(row.payload)
    PlanResponse.model_validate(deepcopy(payload))
    for key, value in (("plan_id", row.id), ("farm_id", row.farm_id),
                       ("analysis_id", row.analysis_id), ("scenario_id", row.scenario_id),
                       ("candidate_id", row.candidate_id), ("observation_id", row.observation_id),
                       ("input_version", row.input_version)):
        require(payload[key] == value, f"Saved plan {key} mismatch.")
    context = {
        "id": payload["farm_id"], "input_version": payload["input_version"],
        "profile": payload["input_snapshot"], "analysis": payload["analysis_result_snapshot"],
        "observations": payload["observation_snapshot"],
    }
    ObservationResponse.model_validate(deepcopy(context["observations"]))
    if payload["scenario_snapshot"] is not None:
        context["scenario"] = payload["scenario_snapshot"]
        require(context["scenario"]["scenario_id"] == payload["scenario_id"], "Saved scenario mismatch.")
    else:
        require(payload["scenario_id"] is None, "Saved scenario is missing.")
    validate_payloads(context)
    require(payload["analysis_snapshot"] == analysis_metadata(
        context["analysis"], context.get("scenario", context["analysis"])), "Saved analysis metadata mismatch.")
    require(context["analysis"]["analysis_id"] == payload["analysis_id"], "Saved analysis mismatch.")
    require(context["analysis"]["observation_id"] == payload["observation_id"], "Saved observation mismatch.")
    require(payload["candidate_snapshot"] == candidate(
        context.get("scenario", context["analysis"]), payload["candidate_id"]), "Saved candidate mismatch.")
    return payload
