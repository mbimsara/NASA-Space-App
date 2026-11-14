"""Cross-owner contracts, without live provider calls or approving draft crops."""
from pathlib import Path
import pytest

from app.services.assistant import explain
from backend.services.climate_handoff import season_inputs
from agrosphere_rotation import ClimateInput, calculate_water_budget, load_catalog, generate_candidates
from observation_fixtures import DATES


def test_http_snapshot_to_season_engine_and_assistant(client, adapter, farm):
    response = client.get(f"/api/v1/farms/{farm['id']}/observations", params=DATES)
    assert response.status_code == 200
    observation = response.json()
    # The seasonal helper accepts the HTTP envelope's source_refs as well as raw sources.
    season = season_inputs(observation, DATES["start"], DATES["end"])
    climate = ClimateInput.from_season_inputs(season)
    assert climate.rainfall_mm == observation["summary"]["rainfall_mm"]
    assert climate.source_refs == tuple(season["source_refs"])
    with pytest.raises(ValueError, match="irrigation is unknown"):
        calculate_water_budget(300, climate)
    confirmed_zero = ClimateInput.from_season_inputs(season, irrigation_mm=0, irrigation_basis="field_applied_depth")
    assert calculate_water_budget(300, confirmed_zero).irrigation_mm == 0
    context = {**farm, "observations": observation}
    answer = explain(context, "What is the recorded farm area?")
    assert str(farm["profile"]["area_ha"]) in answer
    cached = client.get(f"/api/v1/observations/{observation['observation_id']}")
    assert cached.json() == observation


def test_real_catalog_is_not_silently_approved_for_demo():
    path = Path(__file__).resolve().parents[2] / "data/catalogs/crops.json"
    _, crops = load_catalog(path)
    assert len(crops) == 8
    result = generate_candidates(crops, ("maha", "yala", "maha"))
    assert result.candidates == ()
    assert result.reasons
