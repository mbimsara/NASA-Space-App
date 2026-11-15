"""Compare saved farms using immutable same-period NASA POWER snapshots."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.schemas.climate_twins import ClimateTwinsResponse
from app.services.observation_cache import snapshot_response
from services.climate_twins import rank_snapshot_twins


router = APIRouter(prefix="/farms", tags=["Climate twins"])


@router.get("/{farm_id}/climate-twins", response_model=ClimateTwinsResponse)
def get_climate_twins(farm_id: str, observation_id: str = Query(...), limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)):
    farm = db.get(Farm, farm_id)
    target_row = db.get(ObservationSnapshot, observation_id)
    if farm is None or target_row is None:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Farm or observation not found."}})
    target = snapshot_response(target_row).model_dump(mode="json")
    if target["farm_id"] != farm_id or target["input_version"] != farm.input_version:
        return JSONResponse(status_code=409, content={"error": {"code": "CONTEXT_CONFLICT", "message": "Observation does not match the current farm version."}})
    rows = db.scalars(select(ObservationSnapshot).order_by(ObservationSnapshot.cached_at.desc())).all()
    latest_by_farm = {}
    for row in rows:
        if row.farm_id not in latest_by_farm:
            current = db.get(Farm, row.farm_id)
            if current is not None and current.input_version == row.input_version:
                latest_by_farm[row.farm_id] = snapshot_response(row).model_dump(mode="json")
    try:
        twins, excluded = rank_snapshot_twins(target, latest_by_farm.values(), limit)
    except ValueError:
        return JSONResponse(status_code=422, content={"error": {"code": "INCOMPLETE_BASELINE", "message": "Climate twins require complete target rainfall and available temperature."}})
    return {
        "schema_version": "0.1", "kind": "historical_climate_twins", "farm_id": farm_id,
        "observation_id": observation_id, "period": target["period"], "twins": twins,
        "excluded": excluded, "source_refs": target["source_refs"],
        "assumptions": ["Similarity uses same-period mean temperature and total rainfall only.",
                        "A 2 C temperature difference and a 50% rainfall difference each equal one distance unit."],
        "limitations": ["Descriptive historical similarity, not proof of matching soils, crops, pests, markets or future climate.",
                        "Only current-version farms with an already saved NASA POWER snapshot for the identical period are eligible."],
    }
