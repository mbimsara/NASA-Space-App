import json

import pytest

from agrosphere_rotation import (
    ClimateInput,
    Crop,
    RepeatPolicy,
    generate_candidates,
    load_catalog,
)


def crop(crop_id: str, family: str, seasons: set[str], status: str = "approved") -> Crop:
    return Crop(
        id=crop_id,
        name=crop_id.title(),
        family=family,
        suitable_seasons=frozenset(seasons),
        source_urls=("https://example.org/source",),
        review_status=status,
    )


def test_generates_only_approved_season_eligible_non_excluded_crops() -> None:
    crops = (
        crop("rice", "poaceae", {"maha"}),
        crop("mung-bean", "fabaceae", {"yala"}),
        crop("draft-crop", "other", {"maha", "yala"}, "draft"),
    )

    result = generate_candidates(crops, ("maha", "yala", "maha"))

    assert [candidate.crop_ids for candidate in result.candidates] == [
        ("rice", "mung-bean", "rice")
    ]


def test_repeat_family_policy_can_leave_no_feasible_sequence() -> None:
    crops = (crop("rice", "poaceae", {"maha", "yala"}),)

    result = generate_candidates(
        crops,
        ("maha", "yala", "maha"),
        repeat_policy=RepeatPolicy(forbid_consecutive_family=True),
    )

    assert result.candidates == ()
    assert "repeat policy" in result.reasons[0]


def test_research_pending_shared_catalog_returns_an_explanation() -> None:
    _, crops = load_catalog("data/catalogs/crops.json")

    result = generate_candidates(crops, ("maha", "yala", "maha"))

    assert result.candidates == ()
    assert len(result.reasons) == 3


def test_catalog_loader_matches_shared_contract(tmp_path) -> None:
    catalog = {
        "schema_version": "0.1",
        "catalog_version": "test-v1",
        "status": "reviewed",
        "crops": [
            {
                "id": "mung-bean",
                "name": "Mung bean",
                "family": "Fabaceae",
                "season_labels": ["yala"],
                "water_demand_mm_per_cycle": None,
                "sources": [
                    {
                        "url": "https://example.org/mung",
                        "accessed_on": "2026-11-14",
                        "notes": "Test source",
                    }
                ],
                "review_status": "approved",
            }
        ],
    }
    path = tmp_path / "crops.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")

    version, crops = load_catalog(path)

    assert version == "test-v1"
    assert crops[0].water_demand_mm is None


def test_research_pending_catalog_cannot_enable_approved_record(tmp_path) -> None:
    catalog = {
        "schema_version": "0.1",
        "catalog_version": "test-v1",
        "status": "research_pending",
        "crops": [
            {
                "id": "rice",
                "name": "Rice",
                "family": "Poaceae",
                "season_labels": ["maha"],
                "water_demand_mm_per_cycle": 1000,
                "sources": [
                    {
                        "url": "https://example.org/rice",
                        "accessed_on": "2026-11-14",
                        "notes": "Test source",
                    }
                ],
                "review_status": "approved",
            }
        ],
    }
    path = tmp_path / "pending.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")

    _, crops = load_catalog(path)

    assert crops[0].review_status == "draft"
    result = generate_candidates(crops, ("maha", "maha", "maha"))
    assert result.candidates == ()


def test_nasa_power_incomplete_rainfall_is_not_used() -> None:
    normalized = {
        "provider": "NASA POWER",
        "summary": {
            "start": "2025-01-01",
            "end": "2025-01-31",
            "rainfall_total_mm": None,
            "rainfall_available_days_mm": 200,
        },
    }

    with pytest.raises(ValueError, match="complete-period"):
        ClimateInput.from_nasa_power(normalized)


def test_climate_input_accepts_complete_matheesha_season_handoff() -> None:
    season = {
        "start": "2025-01-01",
        "end": "2025-01-31",
        "expected_days": 31,
        "rain_valid_days": 31,
        "temperature_valid_days": 30,
        "rainfall_total_mm": 221.69,
        "mean_temperature_c": 24.4,
        "effective_rainfall_mm": None,
        "crop_water_demand_mm": None,
        "irrigation_deficit_mm": None,
    }

    result = ClimateInput.from_season_inputs(
        season,
        irrigation_mm=50,
        rainfall_change_percent=-20,
    )

    assert result.rainfall_mm == pytest.approx(221.69)
    assert result.irrigation_mm == 50
    assert result.rainfall_change_percent == -20


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("rain_valid_days", 30, "complete seasonal rainfall"),
        ("effective_rainfall_mm", 180, "Bhagya's approved model"),
        ("crop_water_demand_mm", 400, "Bhagya's approved catalog"),
        ("irrigation_deficit_mm", 100, "rotation engine"),
    ],
)
def test_season_handoff_rejects_incomplete_or_precomputed_agronomy(
    field: str, value: float, message: str
) -> None:
    season = {
        "start": "2025-01-01",
        "end": "2025-01-31",
        "expected_days": 31,
        "rain_valid_days": 31,
        "rainfall_total_mm": 221.69,
        "effective_rainfall_mm": None,
        "crop_water_demand_mm": None,
        "irrigation_deficit_mm": None,
    }
    season[field] = value

    with pytest.raises(ValueError, match=message):
        ClimateInput.from_season_inputs(season)
