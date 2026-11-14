"""Reproduce supported baseline calculations without inferring seasonal climate.

Current rotation analyses have no approved alignment of observation dates with
crop seasons. Until that boundary exists, the rainfall parameter is preserved
but cannot be applied to water budgets. In particular, a historical rainfall
total must not be copied across each future season.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from app.schemas.farm import FarmProfile, PriorityWeights
from app.schemas.rotation import RotationRequest
from app.services.rotations import ENGINE_COMMIT, RotationService
from agrosphere_rotation.scoring import MODEL_VERSION

SCENARIO_VERSION = "climate-scenario-0.1"
WATER_LIMITATION = (
    "The hypothetical rainfall adjustment cannot be applied: the saved rotation "
    "has no approved crop-season climate alignment. Water budgets, rainfall-driven "
    "scores and their differences remain unavailable; no zero change is inferred."
)


def candidate_key(candidate):
    return tuple((step["season_index"], step["crop_id"]) for step in candidate["sequence"])


def build_scenario(baseline, inputs, observation, parameters):
    """Only replay the known engine revision against saved, approved inputs.

    Unsupported saved water models must fail explicitly rather than lose their
    numerical results or be silently converted to our current null-water model.
    """
    if inputs["engine_commit"] != ENGINE_COMMIT or baseline["model_version"] != MODEL_VERSION:
        raise ValueError("Unsupported baseline engine version")
    request = RotationRequest.model_validate(inputs["request"])
    # These were already normalized when the baseline was saved. Validation
    # above checks their domain; preserve the exact values for reproducibility
    # instead of normalizing floating-point values a second time.
    weights = inputs["request"]["priority_weights"]
    if not math.isclose(sum(weights.values()), 1, abs_tol=1e-12):
        raise ValueError("Saved priority weights are not normalized")
    request.priority_weights = PriorityWeights.model_construct(**weights)
    FarmProfile.model_validate(inputs["farm_profile"])
    if (request.input_version != baseline["input_version"]
            or request.observation_id != baseline["observation_id"]
            or request.catalog_version != baseline["catalog_version"]):
        raise ValueError("Stored request does not match baseline")
    with TemporaryDirectory() as directory:
        path = Path(directory) / "catalog.json"
        path.write_text(json.dumps(inputs["catalog"]), encoding="utf-8")
        replay, _ = RotationService(path).analyze(request, inputs["farm_profile"], observation)

    # Validate that this baseline can actually be reproduced by this adapter.
    # Candidate IDs belong to the baseline; never replace them with replay IDs.
    original = {candidate_key(item): item for item in baseline["candidates"]}
    regenerated = {candidate_key(item): item for item in replay["candidates"]}
    if (len(original) != len(baseline["candidates"]) or original.keys() != regenerated.keys()
            or len({item["candidate_id"] for item in original.values()}) != len(original)):
        raise ValueError("Baseline candidates cannot be reproduced")
    candidates = []
    differences = {}
    for key, candidate in regenerated.items():
        saved = original[key]
        # Refuse unsupported metrics instead of quietly discarding saved water
        # calculations. The current rotation adapter emits only unknown water.
        if (saved["water_budget"] != candidate["water_budget"]
                or saved["water_budget_range"] != candidate["water_budget_range"]
                or saved["score_components"] != candidate["score_components"]
                or saved["score"] != candidate["score"]
                or saved["constraint_checks"] != candidate["constraint_checks"]):
            raise ValueError("Baseline calculations cannot be reproduced")
        candidate["candidate_id"] = saved["candidate_id"]
        candidate["reasons"].append(WATER_LIMITATION)
        candidates.append(candidate)
        differences[saved["candidate_id"]] = {
            "score_delta": None if candidate["score"] is None else candidate["score"] - saved["score"],
            "water_budget_delta": None,
            "water_budget_range_delta": None,
        }
    return {
        "scenario_id": str(uuid4()),
        "baseline_analysis_id": baseline["analysis_id"],
        "farm_id": baseline["farm_id"], "input_version": baseline["input_version"],
        "observation_id": baseline["observation_id"],
        "parameters": parameters.model_dump(),
        "hypothetical": True,
        "data_kind": "synthetic" if baseline["data_kind"] == "synthetic" else "modeled",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "catalog_version": baseline["catalog_version"],
        "model_version": baseline["model_version"],
        "scenario_model_version": SCENARIO_VERSION,
        "candidates": candidates,
        "baseline_differences": differences,
        "reasons": deepcopy(replay["reasons"]),
        "assumptions": deepcopy(replay["assumptions"]) + [
            "Hypothetical scenario, not a weather forecast or an updated NASA observation.",
            "Uses original farm inputs and catalog; later farm or catalog edits do not alter this baseline.",
            "Crop diversity is independent of rainfall; its computed score difference can be zero even when water effects are unknown.",
        ],
        "source_refs": deepcopy(replay["source_refs"]),
        "limitations": list(dict.fromkeys(baseline["limitations"] + replay["limitations"] + [WATER_LIMITATION])),
    }
