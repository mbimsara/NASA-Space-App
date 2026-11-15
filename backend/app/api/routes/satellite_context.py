"""Farm-scoped read-only access to verified GPM and HLS artifacts."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.schemas.satellite_context import GpmContext, HlsContext
from app.services.satellite_context import SatelliteContextUnavailable, load_gpm, load_hls


router = APIRouter(prefix="/farms", tags=["Satellite context"])


def _farm_or_error(farm_id: str, db: Session):
    farm = db.get(Farm, farm_id)
    if farm is None:
        return None, JSONResponse(status_code=404, content={"error": {
            "code": "NOT_FOUND", "message": "Farm not found.",
        }})
    return farm, None


@router.get("/{farm_id}/gpm-precipitation", response_model=GpmContext)
def get_gpm_precipitation(farm_id: str, db: Session = Depends(get_db)):
    farm, error = _farm_or_error(farm_id, db)
    if error:
        return error
    try:
        return load_gpm(farm)
    except SatelliteContextUnavailable:
        return JSONResponse(status_code=404, content={"error": {
            "code": "GPM_CONTEXT_UNAVAILABLE",
            "message": "Verified GPM IMERG context is unavailable for this farm.",
        }})


@router.get("/{farm_id}/hls-vegetation", response_model=HlsContext)
def get_hls_vegetation(farm_id: str, db: Session = Depends(get_db)):
    farm, error = _farm_or_error(farm_id, db)
    if error:
        return error
    try:
        return load_hls(farm)
    except SatelliteContextUnavailable:
        return JSONResponse(status_code=404, content={"error": {
            "code": "HLS_CONTEXT_UNAVAILABLE",
            "message": "Verified HLS vegetation context is unavailable for this farm.",
        }})
