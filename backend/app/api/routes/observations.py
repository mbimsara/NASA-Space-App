from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.schemas.observation import ObservationQuery, ObservationResponse
from app.services.observation_cache import get_or_fetch_snapshot, snapshot_response
from app.services.observations import (
    ObservationAdapter, ObservationServiceUnavailable,
    get_observation_adapter,
)


router = APIRouter(prefix="/farms", tags=["Observations"])
snapshot_router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get(
    "/{farm_id}/observations", response_model=ObservationResponse,
    responses={404: {"description": "Farm not found"},
               503: {"description": "Observation service unavailable"}},
)
def get_observations(
    farm_id: str,
    period: Annotated[ObservationQuery, Query()],
    response: Response,
    db: Session = Depends(get_db),
    adapter: ObservationAdapter | None = Depends(get_observation_adapter),
):
    try:
        farm = db.get(Farm, farm_id)
        if farm is None:
            return JSONResponse(status_code=404, content={"error": {
                "code": "NOT_FOUND", "message": "Farm not found.",
            }})
        snapshot, cache_hit = get_or_fetch_snapshot(
            db, farm, start=period.start, end=period.end, adapter=adapter,
        )
        response.headers["X-Observation-Cache"] = "HIT" if cache_hit else "MISS"
        response.headers["X-Observation-Expires-At"] = datetime.fromtimestamp(
            snapshot.expires_at, timezone.utc,
        ).isoformat()
        response.headers["Cache-Control"] = "no-store"
        return snapshot_response(snapshot)
    except (ObservationServiceUnavailable, OSError, ValueError, KeyError, TypeError):
        return JSONResponse(status_code=503, content={"error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Climate observation service is currently unavailable. Try again later.",
        }})
    except SQLAlchemyError:
        db.rollback()
        return storage_unavailable()


def storage_unavailable():
    return JSONResponse(status_code=503, content={"error": {
        "code": "SERVICE_UNAVAILABLE",
        "message": "Observation storage is currently unavailable. Try again later.",
    }})


@snapshot_router.get(
    "/{observation_id}", response_model=ObservationResponse,
    responses={404: {"description": "Observation not found"},
               503: {"description": "Observation storage unavailable"}},
)
def get_observation_snapshot(
    observation_id: str, response: Response, db: Session = Depends(get_db),
):
    """Read the original immutable snapshot, including historical farm versions."""
    try:
        snapshot = db.get(ObservationSnapshot, observation_id)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"error": {
                "code": "NOT_FOUND", "message": "Observation not found.",
            }})
        response.headers["Cache-Control"] = "no-store"
        return snapshot_response(snapshot)
    except (SQLAlchemyError, ValueError, KeyError, TypeError):
        db.rollback()
        return storage_unavailable()
