"""Create durable hypothetical scenarios from saved rotation snapshots."""
from copy import deepcopy

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.rotations import error
from app.database.connection import get_db
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from app.schemas.scenario import ScenarioRequest
from app.services.observation_cache import snapshot_response
from app.services.scenarios import build_scenario

router = APIRouter(tags=["Climate scenarios"])


@router.post("/analyses/{analysis_id}/scenarios", responses={
    404: {"description": "Analysis not found"},
    409: {"description": "Stored baseline context is inconsistent"},
    422: {"description": "Invalid rainfall adjustment"},
    503: {"description": "Baseline data, engine or storage unavailable"},
})
def create_scenario(analysis_id: str, request: ScenarioRequest, db: Session = Depends(get_db)):
    try:
        analysis = db.get(RotationAnalysis, analysis_id)
        if analysis is None:
            return error(404, "NOT_FOUND", "Rotation analysis not found.")
        baseline, inputs = deepcopy(analysis.payload), deepcopy(analysis.inputs)
        if (baseline["analysis_id"] != analysis.id or baseline["farm_id"] != analysis.farm_id
                or baseline["input_version"] != analysis.input_version
                or baseline["observation_id"] != analysis.observation_id):
            return error(409, "CONTEXT_CONFLICT", "Stored analysis context is inconsistent.")
        snapshot = db.get(ObservationSnapshot, analysis.observation_id)
        if snapshot is None:
            return error(503, "SERVICE_UNAVAILABLE", "Baseline observation snapshot is unavailable.")
        if (snapshot.farm_id != analysis.farm_id or snapshot.input_version != analysis.input_version
                or snapshot.farm_profile != inputs["farm_profile"]):
            return error(409, "CONTEXT_CONFLICT", "Baseline observation does not match the saved analysis.")
        observation = snapshot_response(snapshot).model_dump(mode="json")
        db.rollback()
        payload = build_scenario(baseline, inputs, observation, request)
        db.add(ClimateScenario(id=payload["scenario_id"], baseline_analysis_id=analysis_id,
            parameters=request.model_dump(),
            inputs={"baseline": baseline, "rotation_inputs": inputs, "observation": observation},
            payload=payload))
        db.commit()
        return payload
    except (SQLAlchemyError, OSError, ValueError, KeyError, TypeError, AttributeError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE",
            "Scenario could not be computed or saved from the supported baseline inputs.")
