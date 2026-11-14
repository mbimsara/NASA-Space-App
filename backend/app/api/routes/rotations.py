"""Crop-rotation analysis endpoint backed by immutable snapshots."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.schemas.rotation import RotationAnalysisResponse, RotationRequest
from app.services.observation_cache import (
    ObservationContextConflict, ObservationNotFound,
    require_observation_for_analysis, snapshot_response,
)
from app.services.rotations import AnalysisVersionConflict, CatalogVersionConflict, build_analysis, persist_analysis
from app.services.observations import (
    ObservationAdapter, ObservationServiceUnavailable, get_observation_adapter,
)
from app.services.season_inputs import (
    SeasonPeriod, SeasonPeriodInvalid, calendar_periods, retrieve_season_inputs, validate_periods,
)
from datetime import datetime, timezone


router = APIRouter(prefix="/farms", tags=["Rotations"])


def error(status_code: int, code: str, message: str):
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@router.post(
    "/{farm_id}/rotations", response_model=RotationAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rotation_analysis(
    farm_id: str, request: RotationRequest, db: Session = Depends(get_db),
    adapter: ObservationAdapter | None = Depends(get_observation_adapter),
):
    try:
        farm = db.get(Farm, farm_id)
        if farm is None:
            return error(404, "NOT_FOUND", "Farm not found.")
        if farm.input_version != request.input_version:
            return error(409, "VERSION_CONFLICT", "Farm version is outdated. Retrieve the latest version and try again.")
        snapshot = require_observation_for_analysis(
            db, request.observation_id, farm_id=farm_id, input_version=request.input_version,
        )
        observation = snapshot_response(snapshot)
        season_inputs = None
        if request.season_periods is not None:
            season_inputs = _season_inputs(db, farm, request, adapter)
        payload = build_analysis(
            farm=farm, observation=observation, request=request, season_inputs=season_inputs,
        )
        # Persistence atomically rechecks the version and holds the writer lock.
        return persist_analysis(db, payload)
    except SeasonPeriodInvalid as exc:
        return error(422, "SEASON_PERIODS_INVALID", str(exc))
    except ObservationServiceUnavailable:
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Season rainfall could not be retrieved. Try again later.")
    except AnalysisVersionConflict as exc:
        db.rollback()
        return error(409, "VERSION_CONFLICT", str(exc))
    except ObservationNotFound:
        return error(404, "NOT_FOUND", "Observation not found.")
    except ObservationContextConflict:
        return error(409, "CONTEXT_MISMATCH", "Observation does not match the current farm input version.")
    except CatalogVersionConflict as exc:
        return error(409, "CATALOG_VERSION_CONFLICT", str(exc))
    except (OSError, ValueError, KeyError) as exc:
        db.rollback()
        return error(422, "ANALYSIS_INPUT_INVALID", str(exc))
    except SQLAlchemyError:
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Rotation analysis storage is currently unavailable.")


def _season_inputs(db: Session, farm: Farm, request: RotationRequest, adapter) -> list[dict]:
    """Define one dated period per planned season and retrieve its rainfall separately."""
    today = datetime.now(timezone.utc).date()
    labels = list(request.season_labels)
    if request.season_periods == "calendar":
        periods, source = calendar_periods(labels, today=today), "season_calendar"
    else:
        periods = [SeasonPeriod(item.start, item.end) for item in request.season_periods]
        source = "request"
    validate_periods(periods, seasons=request.seasons, today=today)
    return retrieve_season_inputs(
        db, farm, labels=labels, periods=periods, adapter=adapter, period_source=source,
    )
