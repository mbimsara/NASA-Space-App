"""Climate exploration derived from immutable observation snapshots."""

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.observation import ObservationSnapshot
from app.schemas.climate import (
    ObservationRainfallScenarioResponse,
    RainfallScenarioRequest,
)
from app.services.observation_cache import snapshot_response
from services.climate import rainfall_scenario


router = APIRouter(prefix="/observations", tags=["climate"])


@router.post(
    "/{observation_id}/rainfall-scenarios",
    response_model=ObservationRainfallScenarioResponse,
    responses={404: {"description": "Observation not found"},
               503: {"description": "Stored observation unavailable"}},
)
def create_rainfall_scenario(
    observation_id: str,
    request: RainfallScenarioRequest = Body(...),
    db: Session = Depends(get_db),
):
    """Uniformly scale a stored historical rainfall series without mutating it."""
    try:
        snapshot = db.get(ObservationSnapshot, observation_id)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": {
                "code": "NOT_FOUND", "message": "Observation not found.",
            }})
        observation = snapshot_response(snapshot).model_dump(mode="json")
        scenario = rainfall_scenario(observation, request.rainfall_change_pct)
        return {
            "schema_version": "0.1",
            "kind": scenario["kind"],
            "observation_id": observation_id,
            "farm_id": observation["farm_id"],
            "input_version": observation["input_version"],
            "baseline_data_kind": observation["data_kind"],
            "parameters": {"rainfall_change_pct": request.rainfall_change_pct},
            "baseline_source_refs": observation["source_refs"],
            "baseline_source_url": scenario["baseline_source_url"],
            "baseline_retrieved_at": scenario["baseline_retrieved_at"],
            "summary": scenario["summary"],
            "monthly": scenario["monthly"],
            "daily": scenario["daily"],
            "assumptions": scenario["assumptions"],
            "limitations": [
                "Hypothetical sensitivity test, not a weather or yield forecast.",
                *observation["limitations"],
            ],
            "metadata": {"time_standard": observation["time_standard"]},
        }
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        db.rollback()
        return JSONResponse(status_code=503, content={"error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Stored climate observation is currently unavailable.",
        }})
