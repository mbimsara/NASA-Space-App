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
from app.services.rotations import CatalogVersionConflict, build_analysis, persist_analysis


router = APIRouter(prefix="/farms", tags=["Rotations"])


def error(status_code: int, code: str, message: str):
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@router.post(
    "/{farm_id}/rotations", response_model=RotationAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rotation_analysis(
    farm_id: str, request: RotationRequest, db: Session = Depends(get_db),
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
        payload = build_analysis(
            farm=farm, observation=snapshot_response(snapshot), request=request,
        )
        # Farm edits between calculation and persistence invalidate the result.
        db.refresh(farm)
        if farm.input_version != request.input_version:
            return error(409, "VERSION_CONFLICT", "Farm changed while the analysis was running. Try again.")
        return persist_analysis(db, payload)
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
