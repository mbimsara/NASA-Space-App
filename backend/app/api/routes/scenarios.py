"""Hypothetical climate scenarios linked to an immutable rotation analysis."""

from fastapi import APIRouter, Body, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.schemas.scenario import AnalysisScenarioRequest, AnalysisScenarioResponse
from app.services.scenarios import (
    AnalysisNotFound, ScenarioNotFound, build_scenario, get_analysis, get_scenario, persist_scenario,
)


router = APIRouter(tags=["Scenarios"])


def error(status_code: int, code: str, message: str):
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@router.post(
    "/analyses/{analysis_id}/scenarios", response_model=AnalysisScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"description": "Analysis not found"},
               503: {"description": "Stored analysis or observation unavailable"}},
)
def create_analysis_scenario(
    analysis_id: str,
    request: AnalysisScenarioRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Recalculate a saved analysis under a rainfall change and persist the scenario snapshot."""
    try:
        analysis = get_analysis(db, analysis_id)
        observation = db.get(ObservationSnapshot, analysis.observation_id)
        if observation is None:
            return error(503, "SERVICE_UNAVAILABLE", "The analysis observation snapshot is unavailable.")
        payload = build_scenario(
            analysis=analysis, observation=observation,
            farm=db.get(Farm, analysis.farm_id), change_pct=request.rainfall_change_pct,
        )
        return persist_scenario(db, payload)
    except AnalysisNotFound:
        return error(404, "NOT_FOUND", "Analysis not found.")
    except (ValueError, KeyError, TypeError) as exc:
        db.rollback()
        return error(422, "SCENARIO_INPUT_INVALID", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Scenario storage is currently unavailable.")


@router.get(
    "/scenarios/{scenario_id}", response_model=AnalysisScenarioResponse,
    responses={404: {"description": "Scenario not found"}},
)
def read_analysis_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Reopen a persisted scenario snapshot exactly as it was calculated."""
    try:
        return get_scenario(db, scenario_id)
    except ScenarioNotFound:
        return error(404, "NOT_FOUND", "Scenario not found.")
    except SQLAlchemyError:
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Scenario storage is currently unavailable.")
