"""Assistant endpoint tests with persisted synthetic results and no AI/provider I/O."""
from copy import deepcopy

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import main
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysis
from app.models.scenario import ClimateScenario
from app.services import assistant_context
from test_scenarios import baseline, approved_baseline


def ask(client, analysis, message="Show full analysis", **changes):
    return client.post("/api/v1/assistant/messages", json={
        "farm_id": analysis["farm_id"], "analysis_id": analysis["analysis_id"],
        "language": "en", "message": message, **changes})


def test_farm_explanation_uses_saved_profile(client, baseline, farm, adapter):
    calls = adapter.observe.call_count
    response = ask(client, baseline, "What is the farm area?")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["role"] == "assistant" and result["language"] == "en"
    assert str(farm["profile"]["area_ha"]) in result["content"]
    assert "synthetic" in result["content"].lower()
    assert result["source_ids"] == []  # Farm area is not attributed to NASA.
    assert response.headers["cache-control"] == "no-store"
    assert adapter.observe.call_count == calls


def test_empty_analysis_preserves_reasons_and_sources(client, baseline):
    response = ask(client, baseline)
    assert response.status_code == 200, response.text
    result = response.json()
    assert "No feasible candidates" in result["content"]
    assert "approved" in result["content"]
    assert set(baseline["source_refs"]) <= set(result["source_ids"])


def test_candidate_sequence_and_effective_weights(client, approved_baseline):
    analysis, _ = approved_baseline
    response = ask(client, analysis, "Show full analysis", candidate_id=analysis["candidates"][0]["candidate_id"])
    assert response.status_code == 200, response.text
    result = response.json()
    assert "test-crop" in result["content"]
    assert "weight 1.0" in result["content"]
    assert "unranked" in result["content"]
    assert "unknown" in result["content"]
    assert "heuristic" in result["content"]


def test_scenario_parameters_and_saved_differences(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    response = ask(client, analysis, "Show full analysis", scenario_id=scenario["scenario_id"],
        candidate_id=analysis["candidates"][0]["candidate_id"])
    assert response.status_code == 200, response.text
    result = response.json()
    assert "hypothetical" in result["content"].lower()
    assert "-20.0%" in result["content"]
    assert "supplied score difference (scenario minus baseline): 0.0" in result["content"]
    assert "not a forecast" in result["content"]


@pytest.mark.parametrize("field", ["farm_id", "analysis_id", "scenario_id", "candidate_id"])
def test_unknown_reference(client, baseline, field):
    assert ask(client, baseline, **{field: "missing"}).status_code == 404


def test_cross_farm_context(client, baseline, farm):
    other = client.post("/api/v1/farms", json=farm["profile"]).json()
    assert ask(client, baseline, farm_id=other["id"]).status_code == 409


def test_outdated_analysis(client, baseline, farm):
    client.patch(f"/api/v1/farms/{farm['id']}", json={"expected_input_version": 1, "profile": farm["profile"]})
    response = ask(client, baseline)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"


@pytest.mark.parametrize("changes", [
    {"language": "si"}, {"language": "ta"}, {"language": "fr"},
    {"message": " "}, {"message": None}, {"farm_id": ""},
    {"candidate_id": ""}, {"scenario_id": ""}, {"extra": "untrusted context"},
])
def test_invalid_request_and_unsupported_language(client, baseline, changes):
    response = ask(client, baseline, **changes)
    assert response.status_code == 422
    expected_code = "UNSUPPORTED_LANGUAGE" if "language" in changes else "VALIDATION_ERROR"
    assert response.json()["error"]["code"] == expected_code


def test_unsupported_recommendations_do_not_generate_advice(client, baseline):
    response = ask(client, baseline, "Recommend the best crop and predict next season yield")
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "unsupported_question"
    assert "cannot provide crop recommendations" in result["content"]
    assert result["source_ids"] == []


def test_missing_optional_sources_are_not_invented(client, baseline):
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, baseline["analysis_id"])
        row.payload = row.payload | {"source_refs": []}
        db.commit()
    response = ask(client, baseline, "Explain rotation candidates")
    assert response.status_code == 200, response.text
    assert response.json()["source_ids"] == []
    assert "unknown (none supplied)" in response.json()["content"]


def test_missing_observation_is_unavailable(client, baseline):
    with Session(main.engine) as db:
        db.delete(db.get(ObservationSnapshot, baseline["observation_id"]))
        db.commit()
    assert ask(client, baseline).status_code == 503


def test_inconsistent_observation_is_conflict(client, baseline):
    with Session(main.engine) as db:
        db.get(ObservationSnapshot, baseline["observation_id"]).input_version += 1
        db.commit()
    assert ask(client, baseline).status_code == 409


def test_input_snapshots_are_unchanged(client, approved_baseline):
    analysis, _ = approved_baseline
    with Session(main.engine) as db:
        row = db.get(RotationAnalysis, analysis["analysis_id"])
        original_inputs = deepcopy(row.inputs)
        observation = deepcopy(db.get(ObservationSnapshot, analysis["observation_id"]).payload)
    assert ask(client, analysis).status_code == 200
    with Session(main.engine) as db:
        assert db.get(RotationAnalysis, analysis["analysis_id"]).payload == analysis
        assert db.get(RotationAnalysis, analysis["analysis_id"]).inputs == original_inputs
        assert db.get(ObservationSnapshot, analysis["observation_id"]).payload == observation


def test_storage_failure_is_safe(client, baseline, monkeypatch):
    def fail(*args, **kwargs):
        raise OperationalError("private SQL", {}, Exception("private token"))
    monkeypatch.setattr(Session, "get", fail)
    result = ask(client, baseline)
    assert result.status_code == 503
    assert "private" not in result.text


def test_scenario_from_another_analysis_is_conflict(client, approved_baseline):
    analysis, _ = approved_baseline
    with Session(main.engine) as db:
        saved_request = deepcopy(db.get(RotationAnalysis, analysis["analysis_id"]).inputs["request"])
    other = client.post(f"/api/v1/farms/{analysis['farm_id']}/rotations", json=saved_request).json()
    scenario = client.post(f"/api/v1/analyses/{other['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    assert ask(client, analysis, scenario_id=scenario["scenario_id"]).status_code == 409


def test_candidate_must_exist_in_selected_scenario(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    with Session(main.engine) as db:
        row = db.get(ClimateScenario, scenario["scenario_id"])
        row.payload = row.payload | {"candidates": []}
        db.commit()
    assert ask(client, analysis, scenario_id=scenario["scenario_id"],
        candidate_id=analysis["candidates"][0]["candidate_id"]).status_code == 404


def test_calls_akash_wrapper(client, baseline, monkeypatch):
    original = assistant_context.respond
    calls = []
    def wrapped(context, *args, **kwargs):
        calls.append(context)
        return original(context, *args, **kwargs)
    monkeypatch.setattr(assistant_context, "respond", wrapped)
    assert ask(client, baseline).status_code == 200
    assert calls[0]["analysis"]["analysis_id"] == baseline["analysis_id"]


def test_observation_explanation_uses_original_snapshot_even_if_cache_expired(client, baseline):
    with Session(main.engine) as db:
        row = db.get(ObservationSnapshot, baseline["observation_id"])
        original = deepcopy(row.payload)
        row.expires_at = 0
        db.commit()
    response = ask(client, baseline, "Explain NASA observations")
    assert response.status_code == 200
    text = response.json()["content"]
    assert str(original["summary"]["rainfall_mm"]) + " mm" in text
    assert original["period"]["start"] in text
    assert set(original["source_refs"]) <= set(response.json()["source_ids"])


def test_normalization_failure_returns_safe_service_error(client, baseline, monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("private incompatible producer data")
    monkeypatch.setattr(assistant_context, "respond", fail)
    response = ask(client, baseline)
    assert response.status_code == 503
    assert "private" not in response.text


def test_hypothetical_disclosure_even_for_farm_question(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    response = ask(client, analysis, "What is the farm area?", scenario_id=scenario["scenario_id"])
    assert response.status_code == 200
    assert "hypothetical" in response.json()["content"]
    assert "not a forecast" in response.json()["limitations"][-1]


def test_corrupt_scenario_metadata_is_rejected(client, approved_baseline):
    analysis, _ = approved_baseline
    scenario = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
        json={"rainfall_change_pct": -20}).json()
    with Session(main.engine) as db:
        row = db.get(ClimateScenario, scenario["scenario_id"])
        row.payload = row.payload | {"input_version": 99}
        db.commit()
    assert ask(client, analysis, scenario_id=scenario["scenario_id"]).status_code == 409
