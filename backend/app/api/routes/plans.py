"""Immutable saved plans for the existing frontend and offline/report clients."""
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.models.plan import SavedPlanSnapshot
from app.schemas.plan import PlanCreated, PlanCreateRequest, PlanRequest, PlanResponse
from app.services.plans import save_plan, stored_plan
from app.services.snapshot_context import SelectionError

router = APIRouter(tags=["Plans"])


def error(status_code, code, message):
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}},
                        headers={"Cache-Control": "no-store"})


def create(db, farm_id, request):
    try:
        return save_plan(db, farm_id, request)
    except SelectionError as exc:
        db.rollback()
        return error(exc.status, exc.code, exc.message)
    except (SQLAlchemyError, ValueError, TypeError, KeyError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Saved plan context or storage is unavailable.")


@router.post("/farms/{farm_id}/plans", response_model=PlanCreated, status_code=status.HTTP_201_CREATED)
def create_farm_plan(farm_id: str, request: PlanRequest, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return create(db, farm_id, request)


@router.post("/plans", response_model=PlanCreated, status_code=status.HTTP_201_CREATED)
def create_plan(request: PlanCreateRequest, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return create(db, request.farm_id, request)


@router.get("/plans", response_model=list[PlanResponse])
def list_plans(response: Response, farm_id: str = Query(min_length=1),
               limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0),
               db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    try:
        if db.get(Farm, farm_id) is None:
            return error(404, "NOT_FOUND", "Farm not found.")
        rows = db.scalars(select(SavedPlanSnapshot).where(
            SavedPlanSnapshot.farm_id == farm_id).order_by(
                SavedPlanSnapshot.created_at.desc(), SavedPlanSnapshot.id).limit(limit).offset(offset)).all()
        return [stored_plan(row) for row in rows]
    except (SQLAlchemyError, ValueError, TypeError, KeyError, SelectionError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Saved plans are unavailable or inconsistent.")


@router.get("/plans/{plan_id}", response_model=PlanResponse)
def read_plan(plan_id: str, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    try:
        row = db.get(SavedPlanSnapshot, plan_id)
        if row is None:
            return error(404, "NOT_FOUND", "Saved plan not found.")
        return stored_plan(row)
    except (SQLAlchemyError, ValueError, TypeError, KeyError, SelectionError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Saved plan is unavailable or inconsistent.")
