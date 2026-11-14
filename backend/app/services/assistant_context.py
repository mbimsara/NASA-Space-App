"""Resolve trusted persisted context and adapt shapes without scientific math."""
from copy import deepcopy

from app.models.farm import Farm
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from app.models.observation import ObservationSnapshot
from app.schemas.farm import FarmProfile
from app.services.observation_cache import snapshot_response
from app.services.assistant_response import respond

AKASH_COMMIT = "9e13c4c8cb9bbb5dfb56089b0ca436ac00ce598d"


class AssistantContextError(ValueError):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code = status, code


def conflict(message):
    raise AssistantContextError(409, "CONTEXT_CONFLICT", message)


def required(db, model, identifier, label):
    row = db.get(model, identifier)
    if row is None:
        raise AssistantContextError(404, "NOT_FOUND", f"{label} not found.")
    return row


def adapt_result(payload):
    result = deepcopy(payload)
    for candidate in result.get("candidates") or []:
        # Map an existing effective weight; do not recompute or infer rankings.
        for component in candidate.get("score_components") or []:
            if "effective_weight" in component:
                component["weight"] = component["effective_weight"]
        if result.get("model_version") == "rotation-score-0.1":
            candidate["score_kind"] = "heuristic"
        budget = candidate.get("water_budget")
        if budget is not None and isinstance(budget.get("period"), str):
            candidate.setdefault("limitations", []).append(
                "The saved water period is descriptive text, not approved crop-cycle dates; dates remain unknown."
            )
            budget["period"] = None
        ranges = candidate.get("water_budget_range")
        if ranges is not None:
            candidate["water_budgets"] = deepcopy(ranges if isinstance(ranges, list) else [ranges])
    if "baseline_differences" in result:
        result["differences"] = [
            {"candidate_id": identifier, "score_delta": delta["score_delta"],
             "water_budget": deepcopy(delta.get("water_budget_delta"))}
            for identifier, delta in result["baseline_differences"].items()
        ]
    return result


def resolve_context(db, request):
    farm = required(db, Farm, request.farm_id, "Farm")
    analysis = required(db, RotationAnalysis, request.analysis_id, "Rotation analysis")
    if analysis.farm_id != farm.id:
        conflict("Analysis does not belong to the requested farm.")
    if analysis.input_version != farm.input_version:
        raise AssistantContextError(409, "VERSION_CONFLICT",
            "Analysis uses an outdated farm version. Generate a current analysis.")
    baseline, inputs = deepcopy(analysis.payload), deepcopy(analysis.inputs)
    if (baseline["analysis_id"] != analysis.id or baseline["farm_id"] != farm.id
            or baseline["input_version"] != analysis.input_version
            or baseline["observation_id"] != analysis.observation_id
            or inputs["request"]["catalog_version"] != baseline["catalog_version"]
            or inputs["request"]["observation_id"] != analysis.observation_id
            or inputs["request"]["input_version"] != analysis.input_version):
        conflict("Stored analysis context is inconsistent.")
    profile = inputs["farm_profile"]
    FarmProfile.model_validate(profile)
    if profile != farm.profile:
        conflict("Analysis farm inputs do not match the current version.")
    observation = db.get(ObservationSnapshot, analysis.observation_id)
    if observation is None:
        raise ValueError("Saved observation is unavailable")
    if (observation.farm_id != farm.id or observation.input_version != analysis.input_version
            or observation.farm_profile != profile):
        conflict("Observation does not match the analysis context.")
    observed = snapshot_response(observation).model_dump(mode="json")
    context = {"id": farm.id, "input_version": analysis.input_version,
        "profile": deepcopy(profile), "analysis": adapt_result(baseline), "observations": observed}
    selected = baseline
    if request.scenario_id is not None:
        scenario = required(db, ClimateScenario, request.scenario_id, "Climate scenario")
        if scenario.baseline_analysis_id != analysis.id:
            conflict("Scenario does not belong to the selected analysis.")
        selected = deepcopy(scenario.payload)
        if (selected["scenario_id"] != scenario.id or selected["baseline_analysis_id"] != analysis.id
                or selected["farm_id"] != farm.id or selected["input_version"] != analysis.input_version
                or selected["observation_id"] != analysis.observation_id
                or selected["parameters"] != scenario.parameters or selected["hypothetical"] is not True
                or selected["model_version"] != baseline["model_version"]
                or selected["catalog_version"] != baseline["catalog_version"]
                or scenario.inputs["baseline"] != baseline
                or scenario.inputs["rotation_inputs"] != inputs
                or scenario.inputs["observation"] != observed):
            conflict("Stored scenario context is inconsistent.")
        context["scenario"] = adapt_result(selected)
    if request.candidate_id is not None:
        matches = [item for item in selected.get("candidates") or [] if item["candidate_id"] == request.candidate_id]
        if not matches:
            raise AssistantContextError(404, "NOT_FOUND", "Candidate not found in the selected result.")
        if len(matches) != 1:
            raise ValueError("Ambiguous stored candidate IDs")
        if request.scenario_id is not None:
            originals = [item for item in baseline["candidates"] if item["candidate_id"] == request.candidate_id]
            if len(originals) != 1 or originals[0]["sequence"] != matches[0]["sequence"]:
                conflict("Scenario candidate does not match its baseline sequence.")
        context["candidate_id"] = request.candidate_id
    return context


def explain_context(context, request):
    # respond invokes Akash's unchanged normalization and explanation functions.
    result = respond(context, request.message, language=request.language)
    disclosures = []
    if any(context[key].get("data_kind") == "synthetic" for key in
           ("profile", "analysis", "observations", "scenario") if key in context):
        disclosures.append("Context includes synthetic demonstration data, not actual NASA observations or validated agronomic advice.")
    if "scenario" in context:
        disclosures.append("The selected scenario is hypothetical, not a forecast or an updated NASA observation.")
    if disclosures:
        result["content"] = " ".join(disclosures) + " " + result["content"]
        result["limitations"] = list(dict.fromkeys(result["limitations"] + disclosures))
    return result
