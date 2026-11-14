"""Stable climate payloads for backend, charts, and assistant integration."""
from copy import deepcopy
from datetime import date
from backend.services.climate import checked_rows, historical_indicators, rainfall_scenario
from backend.services.temperature_exposure import temperature_exposure

MODEL_VERSION = "climate-descriptive-0.1"


def season_inputs(observations, start, end):
    """Extract a complete requested date window without inventing crop demand."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        raise ValueError("Season start must not follow end")
    rows = checked_rows(observations)
    selected = [row for row in rows if start <= row["date"] <= end]
    expected = (last - first).days + 1
    if len(selected) != expected:
        raise ValueError("Season extends outside available history; retrieve the full period first")
    rain = [row["precipitation_mm_per_day"] for row in selected if row["precipitation_mm_per_day"] is not None]
    temps = [row["temperature_c"] for row in selected if row["temperature_c"] is not None]
    return {
        "start": start, "end": end, "expected_days": expected,
        "rain_valid_days": len(rain), "temperature_valid_days": len(temps),
        "rainfall_total_mm": sum(rain) if len(rain) == expected else None,
        "mean_temperature_c": sum(temps) / len(temps) if temps else None,
        "effective_rainfall_mm": None, "crop_water_demand_mm": None, "irrigation_deficit_mm": None,
        "assumptions": ["Historical rainfall depth over the requested inclusive UTC period.",
                        "Effective rainfall, crop demand, and irrigation deficit require Bhagya's approved model.",
                        "Temperature mean uses available days; inspect coverage."],
    }


def observation_envelope(observations, farm_id, observation_id, input_version):
    """Caller allocates IDs/version; no database, HTTP, or authorization here."""
    if not all(isinstance(value, str) and value.strip() for value in (farm_id, observation_id)):
        raise ValueError("Nonempty farm and observation IDs are required")
    if type(input_version) is not int or input_version < 1:
        raise ValueError("Input version must be a positive integer")
    checked_rows(observations)
    summary = observations["summary"]
    # Deep-copy caller-owned structures so later UI/scenario edits cannot mutate the baseline.
    return deepcopy({
        "schema_version": "0.1", "model_version": MODEL_VERSION,
        "farm_id": farm_id, "observation_id": observation_id, "input_version": input_version,
        "data_kind": observations["data_kind"], "provider": observations["provider"],
        "period": {"start": summary["start"], "end": summary["end"]},
        "retrieved_at": observations.get("retrieved_at"), "source_url": observations.get("source_url"),
        "source_refs": observations["sources"], "api": observations["api"],
        "spatial_resolution": observations["spatial_resolution"], "time_standard": observations["time_standard"],
        "coordinates": observations["coordinates"],
        "coverage": {"expected_days": summary["expected_days"],
                     "temperature_valid_days": summary["temperature_valid_days"],
                     "precipitation_valid_days": summary["precipitation_valid_days"]},
        "summary": summary, "daily": observations["daily"], "monthly": observations["monthly"],
        "limitations": observations["limitations"],
    })


def climate_bundle(observations, farm_id, observation_id, input_version, rainfall_change_pct=-30):
    return {
        "observation": observation_envelope(observations, farm_id, observation_id, input_version),
        "historical": historical_indicators(observations),
        "rainfall_scenario": rainfall_scenario(observations, rainfall_change_pct),
        "temperature_exposure": temperature_exposure(observations),
    }
