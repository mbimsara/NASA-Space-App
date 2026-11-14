from copy import deepcopy

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.models.rotation import RotationAnalysis
from app.schemas.rotation import RotationRequest
from app.services.observation_cache import (
    require_observation_for_analysis, ObservationNotFound, ObservationContextConflict,
)
from app.services.rotations import get_rotation_service, CatalogVersionError, ENGINE_COMMIT

router = APIRouter(tags=["Rotations"])


def error(status, code, message):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@router.post("/farms/{farm_id}/rotations")
def create_rotation(farm_id: str, request: RotationRequest, db: Session = Depends(get_db),
                    service=Depends(get_rotation_service)):
    try:
        farm = db.get(Farm, farm_id)
        if farm is None:
            return error(404, "NOT_FOUND", "Farm not found.")
        if farm.input_version != request.input_version:
            return error(409, "VERSION_CONFLICT", "Farm input version has changed.")
        snapshot = require_observation_for_analysis(db, request.observation_id,
            farm_id=farm_id, input_version=request.input_version)
        profile, observation = deepcopy(farm.profile), deepcopy(snapshot.payload)
        db.rollback()
        payload, catalog = service.analyze(request, profile, observation)
        # A conditional write acquires the SQLite writer lock and rechecks the
        # version atomically. It changes no farm values and protects the INSERT.
        guard = db.execute(update(Farm).where(Farm.id == farm_id,
            Farm.input_version == request.input_version).values(input_version=Farm.input_version))
        if guard.rowcount != 1:
            db.rollback()
            return error(409, "VERSION_CONFLICT", "Farm input version changed during analysis.")
        db.add(RotationAnalysis(id=payload["analysis_id"], farm_id=farm_id,
            input_version=request.input_version, observation_id=request.observation_id,
            inputs={"farm_profile": profile, "request": request.model_dump(mode="json"),
                "catalog": catalog, "engine_commit": ENGINE_COMMIT}, payload=payload))
        db.commit()
        return payload
    except ObservationNotFound:
        return error(404, "NOT_FOUND", "Observation not found.")
    except ObservationContextConflict:
        return error(409, "CONTEXT_CONFLICT", "Observation does not match the current farm input version.")
    except CatalogVersionError as exc:
        return error(422, "VALIDATION_ERROR", str(exc))
    except (SQLAlchemyError, OSError, ValueError, KeyError, TypeError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Rotation analysis or storage is unavailable.")
