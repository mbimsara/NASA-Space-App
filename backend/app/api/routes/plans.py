"""Save and reopen selected candidate snapshots without recomputation."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.rotations import error
from app.database.connection import get_db
from app.models.farm import Farm
from app.models.plan import SavedPlan
from app.schemas.plan import PlanCreated, PlanRequest, PlanResponse
from app.services.plans import PlanSelectionError, prepare_plan

router = APIRouter(tags=["Saved plans"])


def unavailable():
    return error(503, "SERVICE_UNAVAILABLE", "Saved plan data or storage is unavailable.")


@router.post("/farms/{farm_id}/plans", status_code=201, response_model=PlanCreated)
def create_plan(farm_id: str, request: PlanRequest, db: Session = Depends(get_db)):
    try:
        payload, provenance = prepare_plan(db, farm_id, request)
        db.rollback()
        # Acquire SQLite's writer lock and recheck the version in one operation.
        # No farm values change; a concurrent PATCH cannot slip past this guard.
        guard = db.execute(update(Farm).where(Farm.id == farm_id,
            Farm.input_version == request.expected_input_version).values(input_version=Farm.input_version))
        if guard.rowcount != 1:
            db.rollback()
            return error(409, "VERSION_CONFLICT", "Farm input version changed while saving the plan.")
        db.add(SavedPlan(id=payload["plan_id"], farm_id=farm_id, analysis_id=request.analysis_id,
            scenario_id=request.scenario_id, observation_id=payload["observation_id"],
            candidate_id=request.candidate_id, input_version=payload["input_version"],
            provenance=provenance, payload=payload))
        db.commit()
        return {"plan_id": payload["plan_id"]}
    except PlanSelectionError as exc:
        db.rollback()
        return error(exc.status, exc.code, str(exc))
    except (SQLAlchemyError, ValueError, KeyError, TypeError, IndexError):
        db.rollback()
        return unavailable()


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: str, response: Response, db: Session = Depends(get_db)):
    try:
        plan = db.get(SavedPlan, plan_id)
        if plan is None:
            return error(404, "NOT_FOUND", "Saved plan not found.")
        payload = PlanResponse.model_validate(plan.payload)
        if (payload.plan_id != plan.id or payload.farm_id != plan.farm_id
                or payload.analysis_id != plan.analysis_id or payload.scenario_id != plan.scenario_id
                or payload.observation_id != plan.observation_id or payload.candidate_id != plan.candidate_id
                or payload.input_version != plan.input_version):
            raise ValueError("Stored plan context is inconsistent")
        response.headers["Cache-Control"] = "no-store"
        return payload
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        db.rollback()
        return unavailable()
