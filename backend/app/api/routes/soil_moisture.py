"""Farm-scoped read-only access to locally verified SMAP context."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.schemas.soil_moisture import SoilMoistureResponse
from app.services.soil_moisture import SoilMoistureUnavailable, load_soil_moisture


router = APIRouter(prefix="/farms", tags=["Soil moisture"])


@router.get("/{farm_id}/soil-moisture", response_model=SoilMoistureResponse)
def get_soil_moisture(farm_id: str, db: Session = Depends(get_db)):
    farm = db.get(Farm, farm_id)
    if farm is None:
        return JSONResponse(status_code=404, content={"error": {
            "code": "NOT_FOUND", "message": "Farm not found.",
        }})
    try:
        return load_soil_moisture(farm)
    except (SoilMoistureUnavailable, ValueError, KeyError, TypeError):
        return JSONResponse(status_code=404, content={"error": {
            "code": "SMAP_CONTEXT_UNAVAILABLE",
            "message": "Verified SMAP surface-moisture context is unavailable for this farm.",
        }})
