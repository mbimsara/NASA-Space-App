"""Resolve canonical persisted snapshots without rewriting scientific payloads.

No provider calls, catalog reads, scientific calculations, or legacy tables.
"""
from copy import deepcopy

from sqlalchemy.orm import Session

from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysisSnapshot
from app.models.scenario import RotationScenarioSnapshot
from app.schemas.farm import FarmProfile
from app.schemas.observation import ObservationResponse
from app.services.assistant_normalization import normalize_context
from app.schemas.rotation import RotationAnalysisResponse
from app.schemas.scenario import AnalysisScenarioResponse
from app.services.observation_cache import snapshot_response


class SelectionError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def candidate(payload, candidate_id):
    matches = [item for item in payload["candidates"] if item["candidate_id"] == candidate_id]
    if len(matches) != 1:
        raise SelectionError(404, "NOT_FOUND", "Candidate not found in the selected result.")
    return matches[0]


def validate_payloads(context):
    """Validate copies; retain the original JSON, including nulls and source order."""
    analysis = context["analysis"]
    RotationAnalysisResponse.model_validate(deepcopy(analysis))
    FarmProfile.model_validate(deepcopy(context["profile"]))
    require(context["id"] == analysis["farm_id"], "Analysis farm mismatch.")
    require(context["input_version"] == analysis["input_version"], "Analysis version mismatch.")
    obs = context["observations"]
    ObservationResponse.model_validate(deepcopy(obs))
    require(obs["requested_location"] == context["profile"]["location"], "Observation location mismatch.")
    require(analysis["data_kind"] == obs["data_kind"], "Analysis provenance mismatch.")
    require(obs["observation_id"] == analysis["observation_id"], "Observation identity mismatch.")
    require(obs["farm_id"] == context["id"] and obs["input_version"] == context["input_version"],
            "Observation farm/version mismatch.")
    ids = [item["candidate_id"] for item in analysis["candidates"]]
    require(len(ids) == len(set(ids)), "Duplicate candidate identity.")
    scenario = context.get("scenario")
    if scenario is not None:
        AnalysisScenarioResponse.model_validate(deepcopy(scenario))
        for key in ("farm_id", "input_version", "observation_id", "catalog_version", "model_version", "data_kind"):
            require(scenario[key] == analysis[key], f"Scenario {key} mismatch.")
        require(scenario["baseline_analysis_id"] == analysis["analysis_id"], "Scenario baseline mismatch.")
        scenario_ids = [item["candidate_id"] for item in scenario["candidates"]]
        require(len(scenario_ids) == len(set(scenario_ids)) and set(scenario_ids) == set(ids),
                "Scenario candidate identities mismatch.")
        baseline = {item["candidate_id"]: item for item in analysis["candidates"]}
        for item in scenario["candidates"]:
            require(item["sequence"] == baseline[item["candidate_id"]]["sequence"],
                    "Scenario candidate sequence mismatch.")
        require(set(scenario["baseline_differences"]) <= set(ids), "Unknown difference candidate.")
        comparison = scenario["observation_rainfall"]
        for key, expected in (
            ("period_start", obs["period"]["start"]), ("period_end", obs["period"]["end"]),
            ("expected_days", obs["coverage"]["expected_days"]),
            ("valid_days", obs["coverage"]["precipitation_valid_days"]),
            ("baseline_rainfall_mm", obs["summary"]["rainfall_total_mm"]),
        ):
            require(comparison[key] == expected, f"Scenario observation comparison {key} mismatch.")
    # Validate assistant-compatible types, ranges, units and identities on copies.
    # This does not modify or replace any of the persisted scientific records.
    normalize_context(context)


def resolve_context(db: Session, *, farm_id, analysis_id, scenario_id=None, candidate_id=None):
    farm = db.get(Farm, farm_id)
    analysis = db.get(RotationAnalysisSnapshot, analysis_id)
    if farm is None or analysis is None:
        raise SelectionError(404, "NOT_FOUND", "Farm or analysis not found.")
    if analysis.farm_id != farm_id:
        raise SelectionError(409, "CONTEXT_MISMATCH", "Analysis belongs to a different farm.")
    if farm.input_version != analysis.input_version:
        raise SelectionError(409, "VERSION_CONFLICT", "Analysis uses an outdated farm version.")
    observation = db.get(ObservationSnapshot, analysis.observation_id)
    require(observation is not None, "Analysis observation snapshot is unavailable.")
    # Uses main's canonical integrity checks, without refreshing expired observations.
    snapshot_response(observation)
    require(observation.farm_id == farm_id and observation.input_version == analysis.input_version,
            "Stored observation does not match analysis.")
    require(observation.farm_profile == farm.profile, "Stored farm input snapshot is inconsistent.")
    payload = deepcopy(analysis.payload)
    for key, expected in (("analysis_id", analysis.id), ("farm_id", analysis.farm_id),
                          ("input_version", analysis.input_version), ("observation_id", analysis.observation_id)):
        require(payload[key] == expected, f"Stored analysis {key} mismatch.")
    context = {
        "id": farm_id, "input_version": analysis.input_version,
        "profile": deepcopy(observation.farm_profile), "analysis": payload,
        "observations": deepcopy(observation.payload),
    }
    if scenario_id is not None:
        scenario = db.get(RotationScenarioSnapshot, scenario_id)
        if scenario is None:
            raise SelectionError(404, "NOT_FOUND", "Scenario not found.")
        if (scenario.analysis_id != analysis_id or scenario.farm_id != farm_id or
                scenario.input_version != analysis.input_version or
                scenario.observation_id != analysis.observation_id):
            raise SelectionError(409, "CONTEXT_MISMATCH", "Scenario does not match the selected analysis.")
        result = deepcopy(scenario.payload)
        require(result["scenario_id"] == scenario.id, "Stored scenario identity mismatch.")
        require(result["parameters"]["rainfall_change_pct"] == scenario.rainfall_change_pct,
                "Stored scenario parameter mismatch.")
        context["scenario"] = result
    validate_payloads(context)
    if candidate_id is not None:
        candidate(payload, candidate_id)
        if "scenario" in context:
            candidate(context["scenario"], candidate_id)
    return context
