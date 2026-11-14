"""Select existing persisted results without running agronomy or NASA services."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from app.schemas.farm import FarmProfile
from app.schemas.plan import PlanRequest, PlanResponse
from app.services.observation_cache import snapshot_response


class PlanSelectionError(ValueError):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def conflict(message):
    raise PlanSelectionError(409, "CONTEXT_CONFLICT", message)


def select_candidate(payload, candidate_id):
    matches = [item for item in payload["candidates"] if item["candidate_id"] == candidate_id]
    if not matches:
        raise PlanSelectionError(404, "NOT_FOUND", "Candidate not found in the selected result.")
    if len(matches) != 1:
        raise ValueError("Stored candidate identifiers are ambiguous")
    return matches[0]


def prepare_plan(db: Session, farm_id: str, request: PlanRequest):
    farm = db.get(Farm, farm_id)
    if farm is None:
        raise PlanSelectionError(404, "NOT_FOUND", "Farm not found.")
    if farm.input_version != request.expected_input_version:
        raise PlanSelectionError(409, "VERSION_CONFLICT", "Farm input version has changed.")
    analysis = db.get(RotationAnalysis, request.analysis_id)
    if analysis is None:
        raise PlanSelectionError(404, "NOT_FOUND", "Rotation analysis not found.")
    if analysis.farm_id != farm_id:
        conflict("Analysis does not belong to the requested farm.")
    if analysis.input_version != request.expected_input_version:
        raise PlanSelectionError(409, "VERSION_CONFLICT", "Analysis uses an outdated farm version.")
    baseline = deepcopy(analysis.payload)
    inputs = deepcopy(analysis.inputs)
    if (baseline["analysis_id"] != analysis.id or baseline["farm_id"] != farm_id
            or baseline["input_version"] != analysis.input_version
            or baseline["observation_id"] != analysis.observation_id):
        conflict("Stored analysis context is inconsistent.")
    saved_request = inputs["request"]
    if (saved_request["input_version"] != analysis.input_version
            or saved_request["observation_id"] != analysis.observation_id
            or saved_request["catalog_version"] != baseline["catalog_version"]):
        conflict("Saved request does not match the analysis.")
    profile = inputs["farm_profile"]
    FarmProfile.model_validate(profile)
    if profile != farm.profile:
        conflict("Saved analysis inputs do not match the farm version.")
    observation = db.get(ObservationSnapshot, analysis.observation_id)
    if observation is None:
        raise ValueError("Baseline observation is unavailable")
    if (observation.farm_id != farm_id or observation.input_version != analysis.input_version
            or observation.farm_profile != profile):
        conflict("Observation does not match the saved analysis.")
    observation_payload = snapshot_response(observation).model_dump(mode="json")
    selected = baseline
    scenario_payload = None
    scenario_inputs = None
    if request.scenario_id is not None:
        scenario = db.get(ClimateScenario, request.scenario_id)
        if scenario is None:
            raise PlanSelectionError(404, "NOT_FOUND", "Climate scenario not found.")
        if scenario.baseline_analysis_id != analysis.id:
            conflict("Scenario does not belong to the selected analysis.")
        scenario_payload = deepcopy(scenario.payload)
        scenario_inputs = deepcopy(scenario.inputs)
        if (scenario_payload["scenario_id"] != scenario.id
                or scenario_payload["baseline_analysis_id"] != analysis.id
                or scenario_payload["farm_id"] != farm_id
                or scenario_payload["input_version"] != analysis.input_version
                or scenario_payload["observation_id"] != analysis.observation_id
                or scenario_payload["catalog_version"] != baseline["catalog_version"]
                or scenario_payload["model_version"] != baseline["model_version"]
                or scenario_payload["parameters"] != scenario.parameters
                or scenario_payload["hypothetical"] is not True
                or scenario_inputs["baseline"] != baseline
                or scenario_inputs["rotation_inputs"] != inputs
                or scenario_inputs["observation"] != observation_payload):
            conflict("Stored scenario context is inconsistent.")
        selected = scenario_payload
    candidate = deepcopy(select_candidate(selected, request.candidate_id))
    if scenario_payload is not None:
        # Current scenarios retain baseline candidate IDs and crop sequences.
        original = select_candidate(baseline, request.candidate_id)
        if original["sequence"] != candidate["sequence"]:
            conflict("Scenario candidate does not match the baseline sequence.")

    # Approval comes from the original catalog snapshot, never today's catalog.
    catalog = inputs["catalog"]
    if catalog["catalog_version"] != baseline["catalog_version"]:
        conflict("Saved catalog version does not match the analysis.")
    crops = {crop["id"]: crop for crop in catalog["crops"]}
    if len(crops) != len(catalog["crops"]):
        raise ValueError("Saved catalog has duplicate crop IDs")
    if catalog["status"] != "reviewed" or not candidate["sequence"]:
        conflict("The selected candidate has no approved catalog support.")
    labels = inputs["request"]["season_labels"]
    sequence = candidate["sequence"]
    if len(sequence) != inputs["request"]["seasons"] or labels is None:
        conflict("Candidate season context is inconsistent.")
    for index, step in enumerate(sequence, 1):
        crop = crops.get(step["crop_id"])
        if (step["season_index"] != index or crop is None or crop["review_status"] != "approved"
                or not crop["sources"] or step["crop_id"] in profile["excluded_crop_ids"]
                or labels[index - 1] not in crop["season_labels"]):
            conflict("Candidate does not match approved catalog eligibility.")
    metadata = {key: deepcopy(selected[key]) for key in (
        "catalog_version", "model_version", "data_kind", "source_refs", "assumptions", "limitations",
    )}
    metadata["analysis_created_at"] = baseline["created_at"]
    payload = {
        "plan_id": str(uuid4()), "farm_id": farm_id, "analysis_id": analysis.id,
        "scenario_id": request.scenario_id, "candidate_id": request.candidate_id,
        "input_version": analysis.input_version, "created_at": datetime.now(timezone.utc).isoformat(),
        "observation_id": analysis.observation_id, "candidate_snapshot": candidate,
        "input_snapshot": deepcopy(profile), "analysis_snapshot": metadata,
        "scenario_snapshot": scenario_payload, "observation_snapshot": observation_payload,
    }
    # Validate before writing so a successful POST always has a readable snapshot.
    PlanResponse.model_validate(payload)
    provenance = {"baseline": baseline, "rotation_inputs": inputs, "scenario_inputs": scenario_inputs}
    return payload, provenance
