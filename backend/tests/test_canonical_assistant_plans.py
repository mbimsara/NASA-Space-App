"""Canonical SQLite/HTTP regression tests. All inputs are synthetic.

The existing main fixtures prohibit NASA access. Expected facts come from saved
producer payloads, never from assistant prose. No agricultural model is replaced.
"""
import json
import re
from copy import deepcopy

import pytest
from sqlalchemy import select

from app.database.connection import get_db
from app.main import app
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.models.rotation import RotationAnalysisSnapshot
from app.models.scenario import RotationScenarioSnapshot
from app.models.plan import SavedPlanSnapshot
from app.services import plans, rotations
from app.services.snapshot_context import resolve_context
from test_analysis_scenarios import APPROVED_CATALOG, create_analysis, with_known_season_water


@pytest.fixture
def journey(client, adapter, farm, tmp_path, monkeypatch):
    path = tmp_path / "synthetic-approved-catalog.json"
    path.write_text(json.dumps(APPROVED_CATALOG), encoding="utf-8")
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)
    observation, analysis = create_analysis(client, farm)
    response = client.post(f"/api/v1/analyses/{analysis['analysis_id']}/scenarios",
                           json={"rainfall_change_pct": -30})
    assert response.status_code == 201, response.text
    scenario = response.json()
    return {"farm": farm, "observation": observation, "analysis": analysis,
            "scenario": scenario, "candidate": analysis["candidates"][0]["candidate_id"]}


def body(journey, *, scenario=False, **changes):
    result = {
        "farm_id": journey["farm"]["id"], "analysis_id": journey["analysis"]["analysis_id"],
        "candidate_id": journey["candidate"], "language": "en", "message": "Explain water budgets",
    }
    if scenario:
        result["scenario_id"] = journey["scenario"]["scenario_id"]
    result.update(changes)
    return result


def plan_body(journey, *, scenario=False, **changes):
    result = {"analysis_id": journey["analysis"]["analysis_id"], "candidate_id": journey["candidate"],
              "expected_input_version": journey["farm"]["input_version"]}
    if scenario:
        result["scenario_id"] = journey["scenario"]["scenario_id"]
    result.update(changes)
    return result


def save(client, journey, **kwargs):
    return client.post(f"/api/v1/farms/{journey['farm']['id']}/plans", json=plan_body(journey, **kwargs))


def database():
    return next(app.dependency_overrides[get_db]())


def mutate(model, identifier, change):
    with database() as db:
        row = db.get(model, identifier)
        change(row)
        db.commit()


def replace_payload(row, key, value):
    payload = deepcopy(row.payload)
    payload[key] = value
    row.payload = payload


def read_saved(client, result):
    assert result.status_code == 201, result.text
    response = client.get(f"/api/v1/plans/{result.json()['plan_id']}")
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("scenario", [False, True])
@pytest.mark.parametrize("question", ["Explain water budgets", "Explain score components",
                                    "Explain constraints", "What is the farm name?",
                                    "Show full analysis", "What happens if rainfall decreases?"])
def test_assistant_selected_canonical_records(client, journey, scenario, question):
    response = client.post("/api/v1/assistant/messages", json=body(journey, scenario=scenario, message=question))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["role"] == "assistant"
    assert isinstance(result["content"], str) and result["content"]
    assert isinstance(result["source_ids"], list) and isinstance(result["limitations"], list)
    assert result["language"] == "en"
    assert "synthetic" in result["content"].lower()
    assert result["context"] == {
        "farm_id": journey["farm"]["id"], "analysis_id": journey["analysis"]["analysis_id"],
        "scenario_id": journey["scenario"]["scenario_id"] if scenario else None,
        "candidate_id": journey["candidate"],
    }
    allowed = set(journey["analysis"]["source_refs"] + journey["scenario"]["source_refs"])
    allowed.update(journey["observation"]["source_refs"])
    if journey["observation"].get("source_url"):
        allowed.add(journey["observation"]["source_url"])
    for record in journey["analysis"]["candidates"] + journey["scenario"]["candidates"]:
        allowed.update(row["source_url"] for row in record["water_budget_range"] if row["source_url"])
    assert set(result["source_ids"]) <= allowed
    assert response.headers["cache-control"] == "no-store"


def test_resolver_preserves_original_payloads_and_descriptive_period(client, journey):
    with database() as db:
        context = resolve_context(db, farm_id=journey["farm"]["id"], analysis_id=journey["analysis"]["analysis_id"],
                                  scenario_id=journey["scenario"]["scenario_id"], candidate_id=journey["candidate"])
        assert context["analysis"] == journey["analysis"]
        assert context["scenario"] == journey["scenario"]
        assert context["observations"] == journey["observation"]
        assert context["profile"] == journey["farm"]["profile"]
    scalar = journey["analysis"]["candidates"][0]["water_budget"]
    assert scalar["period"] == "season-specific periods unavailable"
    answer = client.post("/api/v1/assistant/messages", json=body(journey, message="Show full analysis")).json()
    from app.services.assistant_normalization import normalize_water_budget
    period = normalize_water_budget(scalar)["period"]
    assert period == {"label": scalar["period"], "start": None, "end": None}
    # Seasonal ranges take precedence over the optional aggregate (original contract).
    assert "Supplied crop/season budget" in answer["content"]


def test_observation_period_comparison_and_candidate_score_change(client, journey):
    comparison = journey["scenario"]["observation_rainfall"]
    response = client.post("/api/v1/assistant/messages", json=body(
        journey, scenario=True, message="What happens if rainfall decreases?"))
    assert response.status_code == 200, response.text
    text = response.json()["content"]
    for key, label in (("baseline_rainfall_mm", "baseline rainfall"),
                       ("scenario_rainfall_mm", "hypothetical rainfall"),
                       ("difference_mm", "supplied difference (scenario minus baseline)")):
        assert any(float(value) == pytest.approx(comparison[key]) for value in
                   re.findall(re.escape(label) + r": (-?\d+(?:\.\d+)?) mm", text))
    for key in ("period_start", "period_end"):
        assert comparison[key] in text
    assert f"{comparison['valid_days']} of {comparison['expected_days']} days" in text
    difference = journey["scenario"]["baseline_differences"][journey["candidate"]]
    match = re.search(re.escape(f"Candidate {journey['candidate']}: supplied score difference (scenario minus baseline): ") + r"(-?\d+(?:\.\d+)?)", text)
    assert match and float(match.group(1)) == pytest.approx(difference["score_change"])
    assert "not a measurement or forecast" in text
    # Observation-period totals never become season rainfall or effective rainfall.
    assert all(row["scenario_rainfall_mm"] is None for row in journey["scenario"]["candidates"][0]["water_budget_range"])
    assert "effective rainfall: unknown" in text.lower()


def test_requested_and_effective_weights_stay_separate(client, journey):
    def change(row):
        payload = deepcopy(row.payload)
        payload["candidates"][0]["score_components"][0].update(requested_weight=0.7, effective_weight=0.2)
        row.payload = payload
    mutate(RotationAnalysisSnapshot, journey["analysis"]["analysis_id"], change)
    result = client.post("/api/v1/assistant/messages", json=body(journey, message="Explain score components"))
    assert result.status_code == 200, result.text
    assert "requested weight 0.7" in result.json()["content"]
    assert "effective weight 0.2" in result.json()["content"]


def test_season_water_ranges_signed_balances_sources_and_unknown_ranks(client, journey):
    baseline = with_known_season_water(journey["analysis"]["analysis_id"])
    result = client.post("/api/v1/assistant/messages", json=body(journey))
    assert result.status_code == 200, result.text
    content = result.json()["content"]
    row = baseline["candidates"][0]["water_budget_range"][0]
    for field, label in (("demand_low_mm", "demand lower bound"), ("demand_high_mm", "demand upper bound"),
                         ("balance_low_mm", "signed balance lower bound"),
                         ("balance_high_mm", "signed balance upper bound"), ("irrigation_mm", "irrigation supply")):
        assert f"{label}: {row[field]:g} mm" in content
    assert row["source_url"] in result.json()["source_ids"]
    assert "no conversion to deficit" in content
    assert "season index 1" in content
    rank_result = client.post("/api/v1/assistant/messages", json=body(journey, message="Explain crop rankings")).json()
    assert "supplied rank unknown" in rank_result["content"]
    assert any("neither is inferred" in item for item in rank_result["limitations"])


@pytest.mark.parametrize("language", ["si", "ta", "fr"])
def test_unsupported_language_controlled_422(client, journey, language):
    response = client.post("/api/v1/assistant/messages", json=body(journey, language=language))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_LANGUAGE"


@pytest.mark.parametrize("changes", [{"message": ""}, {"message": "x" * 2001},
                                    {"message": None}, {"context": {"score": 100}}, {"candidate_id": ""}])
def test_request_validation(client, journey, changes):
    response = client.post("/api/v1/assistant/messages", json=body(journey, **changes))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("field", ["farm_id", "analysis_id", "scenario_id", "candidate_id"])
def test_missing_selected_record_404(client, journey, field):
    response = client.post("/api/v1/assistant/messages", json=body(journey, **{field: "missing"}))
    assert response.status_code == 404, response.text


@pytest.mark.parametrize("target", ["analysis", "scenario"])
def test_cross_farm_relationship_409(client, journey, target):
    other = client.post("/api/v1/farms", json=journey["farm"]["profile"]).json()
    if target == "analysis":
        request = body(journey, farm_id=other["id"])
    else:
        mutate(RotationScenarioSnapshot, journey["scenario"]["scenario_id"],
               lambda row: setattr(row, "farm_id", other["id"]))
        request = body(journey, scenario=True)
    result = client.post("/api/v1/assistant/messages", json=request)
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "CONTEXT_MISMATCH"


@pytest.mark.parametrize("table", ["analysis", "scenario", "observation"])
def test_corrupt_context_safe_503(client, journey, table):
    model, identifier, key = {
        "analysis": (RotationAnalysisSnapshot, journey["analysis"]["analysis_id"], "observation_id"),
        "scenario": (RotationScenarioSnapshot, journey["scenario"]["scenario_id"], "baseline_analysis_id"),
        "observation": (ObservationSnapshot, journey["observation"]["observation_id"], "farm_id"),
    }[table]
    mutate(model, identifier, lambda row: replace_payload(row, key, "corrupt"))
    response = client.post("/api/v1/assistant/messages", json=body(journey, scenario=True))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "corrupt" not in response.text
    assert save(client, journey, scenario=True).status_code == 503


@pytest.mark.parametrize("scenario", [False, True])
def test_save_and_retrieve_exact_immutable_snapshots(client, journey, scenario):
    plan = read_saved(client, save(client, journey, scenario=scenario))
    selected = journey["scenario"] if scenario else journey["analysis"]
    assert plan["input_snapshot"] == journey["farm"]["profile"]
    assert plan["analysis_result_snapshot"] == journey["analysis"]
    assert plan["scenario_snapshot"] == (journey["scenario"] if scenario else None)
    assert plan["observation_snapshot"] == journey["observation"]
    assert plan["candidate_snapshot"] == selected["candidates"][0]
    assert plan["analysis_snapshot"]["analysis_created_at"] == journey["analysis"]["created_at"]
    for key in ("source_refs", "assumptions", "data_kind", "catalog_version", "model_version"):
        assert plan["analysis_snapshot"][key] == selected[key]
    assert plan["analysis_snapshot"]["limitations"][:len(selected["limitations"])] == selected["limitations"]
    profile = deepcopy(journey["farm"]["profile"])
    profile["name"] = "Edited later"
    profile["irrigation_supply_mm_per_season"] = 0
    result = client.patch(f"/api/v1/farms/{journey['farm']['id']}", json={
        "expected_input_version": journey["farm"]["input_version"], "profile": profile})
    assert result.status_code == 200, result.text
    assert client.get(f"/api/v1/plans/{plan['plan_id']}").json() == plan
    assert save(client, journey, scenario=scenario).status_code == 409
    assert client.post("/api/v1/assistant/messages", json=body(journey)).status_code == 409


def test_saved_retrieval_does_not_refresh_or_depend_on_upstream_payloads(client, journey, adapter):
    plan = read_saved(client, save(client, journey, scenario=True))
    for model, identifier in ((RotationAnalysisSnapshot, journey["analysis"]["analysis_id"]),
                              (RotationScenarioSnapshot, journey["scenario"]["scenario_id"]),
                              (ObservationSnapshot, journey["observation"]["observation_id"])):
        mutate(model, identifier, lambda row: setattr(row, "payload", {}))
    adapter.observe.side_effect = AssertionError("Retrieval must not fetch observations.")
    assert client.get(f"/api/v1/plans/{plan['plan_id']}").json() == plan


def test_saved_candidate_tampering_safe_503(client, journey):
    plan = read_saved(client, save(client, journey))
    mutate(SavedPlanSnapshot, plan["plan_id"], lambda row: replace_payload(row, "candidate_snapshot", {}))
    assert client.get(f"/api/v1/plans/{plan['plan_id']}").status_code == 503


@pytest.mark.parametrize("changes,status", [
    ({"candidate_id": "missing"}, 404), ({"analysis_id": "missing"}, 404),
    ({"scenario_id": "missing"}, 404), ({"expected_input_version": 100}, 409),
    ({"expected_input_version": 0}, 422), ({"expected_input_version": True}, 422),
    ({"candidate_snapshot": {}}, 422),
])
def test_invalid_plan_is_never_inserted(client, journey, changes, status):
    response = save(client, journey, **changes)
    assert response.status_code == status, response.text
    with database() as db:
        assert db.scalars(select(SavedPlanSnapshot)).all() == []


def test_plan_cross_farm_rejected(client, journey):
    other = client.post("/api/v1/farms", json=journey["farm"]["profile"]).json()
    result = client.post(f"/api/v1/farms/{other['id']}/plans", json=plan_body(journey))
    assert result.status_code == 409


def test_plan_scenario_analysis_mismatch_rejected(client, journey):
    _, other = create_analysis(client, journey["farm"])
    result = save(client, journey, scenario=True, analysis_id=other["analysis_id"])
    assert result.status_code == 409


def test_plan_atomic_version_recheck(client, journey, monkeypatch):
    original = plans.resolve_context
    def edited_after_read(db, **kwargs):
        context = original(db, **kwargs)
        # Commit an edit before save_plan obtains its atomic writer lock.
        row = db.get(Farm, kwargs["farm_id"])
        row.input_version += 1
        db.commit()
        return context
    monkeypatch.setattr(plans, "resolve_context", edited_after_read)
    assert save(client, journey).status_code == 409
    with database() as db:
        assert db.scalars(select(SavedPlanSnapshot)).all() == []


def test_root_create_and_paginated_farm_scoped_listing(client, journey):
    first = read_saved(client, save(client, journey))
    second = read_saved(client, client.post("/api/v1/plans", json={
        "farm_id": journey["farm"]["id"], **plan_body(journey, scenario=True)}))
    response = client.get("/api/v1/plans", params={"farm_id": journey["farm"]["id"]})
    assert response.status_code == 200
    assert response.json() == [second, first]
    assert client.get("/api/v1/plans", params={
        "farm_id": journey["farm"]["id"], "limit": 1, "offset": 1}).json() == [first]
    other = client.post("/api/v1/farms", json=journey["farm"]["profile"]).json()
    assert client.get("/api/v1/plans", params={"farm_id": other["id"]}).json() == []
    assert client.get("/api/v1/plans", params={"farm_id": "missing"}).status_code == 404
    assert client.get("/api/v1/plans").status_code == 422
    assert client.get("/api/v1/plans/missing").status_code == 404


def test_no_feasible_candidates_remains_grounded(client, journey):
    mutate(RotationAnalysisSnapshot, journey["analysis"]["analysis_id"],
           lambda row: replace_payload(row, "candidates", []))
    result = client.post("/api/v1/assistant/messages", json=body(
        journey, candidate_id=None, message="Explain crop rotations"))
    assert result.status_code == 200
    assert "No feasible candidates" in result.json()["content"]
    assert save(client, journey).status_code == 404


def test_zero_and_missing_farm_inputs_preserved(client, journey):
    profile = deepcopy(journey["farm"]["profile"])
    profile["irrigation_supply_mm_per_season"] = 0
    # A controlled persisted synthetic fixture with a matching farm snapshot.
    mutate(Farm, journey["farm"]["id"], lambda row: setattr(row, "profile", deepcopy(profile)))
    mutate(ObservationSnapshot, journey["observation"]["observation_id"],
           lambda row: setattr(row, "farm_profile", deepcopy(profile)))
    result = client.post("/api/v1/assistant/messages", json=body(
        journey, message="What is the farm irrigation supply?"))
    assert result.status_code == 200
    assert "0 mm" in result.json()["content"]
    plan = read_saved(client, save(client, journey))
    assert plan["input_snapshot"]["irrigation_supply_mm_per_season"] == 0
    assert any(row["scenario_rainfall_mm"] is None for row in plan["candidate_snapshot"]["water_budget_range"])


@pytest.mark.allow_hosts(["127.0.0.1", "::1"])
def test_real_loopback_http_journey(client, adapter, tmp_path, monkeypatch):
    """Exercise real TCP HTTP, not just TestClient or separately passing modules."""
    import socket
    import threading
    import time
    from pathlib import Path

    import httpx
    import uvicorn

    path = tmp_path / "synthetic-catalog.json"
    path.write_text(json.dumps(APPROVED_CATALOG), encoding="utf-8")
    monkeypatch.setattr(rotations, "CATALOG_PATH", path)
    profile = json.loads((Path(__file__).resolve().parents[2] /
                          "data/fixtures/farm.synthetic.json").read_text(encoding="utf-8"))
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen()
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off", loop="asyncio", http="h11"))
    worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            assert worker.is_alive() and time.monotonic() < deadline, "Local HTTP server failed to start"
            time.sleep(0.01)
        with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1", trust_env=False, timeout=10) as http:
            def post(url, payload, expected=201):
                response = http.post(url, json=payload)
                assert response.status_code == expected, response.text
                return response.json()
            farm = post("/farms", profile)
            observation = http.get(f"/farms/{farm['id']}/observations",
                                   params={"start": "2024-02-28", "end": "2024-03-01"})
            assert observation.status_code == 200, observation.text
            observation = observation.json()
            analysis = post(f"/farms/{farm['id']}/rotations", {
                "input_version": farm["input_version"], "observation_id": observation["observation_id"],
                "seasons": 3, "season_labels": ["maha", "yala", "maha"],
                "catalog_version": APPROVED_CATALOG["catalog_version"],
                "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2},
            })
            scenario = post(f"/analyses/{analysis['analysis_id']}/scenarios", {"rainfall_change_pct": -30})
            candidate = scenario["candidates"][0]
            request = {"farm_id": farm["id"], "analysis_id": analysis["analysis_id"],
                       "scenario_id": scenario["scenario_id"], "candidate_id": candidate["candidate_id"],
                       "language": "en", "message": "What happens if rainfall decreases?"}
            answer = post("/assistant/messages", request, 200)
            assert {"role", "content", "source_ids", "limitations"} <= answer.keys()
            assert "hypothetical" in answer["content"].lower() and "synthetic" in answer["content"].lower()
            assert set(answer["source_ids"]) <= set(analysis["source_refs"] + scenario["source_refs"])
            for language in ("si", "ta"):
                error = post("/assistant/messages", {**request, "language": language}, 422)
                assert error["error"]["code"] == "UNSUPPORTED_LANGUAGE"
            saved = post(f"/farms/{farm['id']}/plans", {
                "analysis_id": analysis["analysis_id"], "scenario_id": scenario["scenario_id"],
                "candidate_id": candidate["candidate_id"], "expected_input_version": farm["input_version"],
            })
            retrieval = http.get(f"/plans/{saved['plan_id']}")
            assert retrieval.status_code == 200
            plan = retrieval.json()
            assert plan["analysis_result_snapshot"] == analysis
            assert plan["scenario_snapshot"] == scenario
            assert plan["candidate_snapshot"] == candidate
            assert plan["observation_snapshot"] == observation
            edited = deepcopy(farm["profile"])
            edited["name"] = "Later farm edit"
            update = http.patch(f"/farms/{farm['id']}", json={
                "expected_input_version": farm["input_version"], "profile": edited})
            assert update.status_code == 200
            assert http.get(f"/plans/{saved['plan_id']}").json() == plan
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        sock.close()
    assert not worker.is_alive(), "Local HTTP server did not stop"


def test_incomplete_scenario_totals_not_replaced_with_partial_sum(client, journey):
    def change_observation(row):
        value = deepcopy(row.payload)
        # Keep a schema-valid partial-coverage synthetic observation envelope.
        value["summary"]["rainfall_total_mm"] = None
        if "rainfall_mm" in value["summary"]:
            value["summary"]["rainfall_mm"] = None
        value["coverage"]["precipitation_valid_days"] = 2
        if "precipitation_valid_days" in value["summary"]:
            value["summary"]["precipitation_valid_days"] = 2
        row.payload = value
    mutate(ObservationSnapshot, journey["observation"]["observation_id"], change_observation)
    def change_scenario(row):
        value = deepcopy(row.payload)
        value["observation_rainfall"].update(
            valid_days=2, baseline_rainfall_mm=None, scenario_rainfall_mm=None, difference_mm=None)
        row.payload = value
    mutate(RotationScenarioSnapshot, journey["scenario"]["scenario_id"], change_scenario)
    result = client.post("/api/v1/assistant/messages", json=body(journey, scenario=True,
                         message="What happens if rainfall decreases?"))
    assert result.status_code == 200, result.text
    content = result.json()["content"]
    comparison = content.split("Whole observation-period rainfall comparison", 1)[1]
    assert "baseline rainfall: unknown" in comparison
    assert "hypothetical rainfall: unknown" in comparison
    assert "coverage: 2 of 3 days" in comparison
    assert any("totals are unknown" in item for item in result.json()["limitations"])


@pytest.mark.parametrize("target", ["period", "coverage", "provenance", "sequence"])
def test_mismatched_snapshot_facts_rejected(client, journey, target):
    def corrupt(row):
        value = deepcopy(row.payload)
        if target == "period":
            value["observation_rainfall"]["period_start"] = "2024-02-27"
        elif target == "coverage":
            value["observation_rainfall"]["expected_days"] = 4
        elif target == "provenance":
            value["data_kind"] = "modeled"
        else:
            value["candidates"][0]["sequence"][0]["crop_id"] = "different-crop"
        row.payload = value
    mutate(RotationScenarioSnapshot, journey["scenario"]["scenario_id"], corrupt)
    assert client.post("/api/v1/assistant/messages", json=body(journey, scenario=True)).status_code == 503
    assert save(client, journey, scenario=True).status_code == 503


def test_celsius_degree_symbol_remains_supported(journey):
    from app.services.assistant_normalization import normalize_observation
    observation = deepcopy(journey["observation"])
    observation["units"]["mean_temperature_c"] = "\u00b0C"
    assert normalize_observation(observation)["units"]["mean_temperature_c"] == "\u00b0C"
