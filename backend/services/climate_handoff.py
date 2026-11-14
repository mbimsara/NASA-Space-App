"""Stable climate payloads for backend, charts, and assistant integration."""
from copy import deepcopy
from datetime import date, datetime
from backend.services.climate import checked_rows, historical_indicators, rainfall_scenario
from backend.services.temperature_exposure import temperature_exposure

MODEL_VERSION = "climate-descriptive-0.1"


def season_inputs(observations, start, end):
    """Extract a complete requested date window without inventing crop demand."""
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if start != first.isoformat() or end != last.isoformat() or first > last:
        raise ValueError("Use ordered season dates in YYYY-MM-DD format")
    rows = checked_rows(observations)
    selected = [row for row in rows if start <= row["date"] <= end]
    expected = (last - first).days + 1
    if len(selected) != expected:
        raise ValueError("Season extends outside available history; retrieve the full period first")
    rain = [row["precipitation_mm_per_day"] for row in selected if row["precipitation_mm_per_day"] is not None]
    temps = [row["temperature_c"] for row in selected if row["temperature_c"] is not None]
    source_refs = observations.get("source_refs", observations.get("sources"))
    if not isinstance(source_refs, list) or not source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in source_refs):
        raise ValueError("Season inputs require nonempty source references")
    source_refs = list(dict.fromkeys(source_refs))
    source_url = observations.get("source_url")
    if source_url is not None:
        if (not isinstance(source_url, str) or not source_url.startswith("https://")
                or observations.get("data_kind") != "synthetic" and not source_url.startswith("https://power.larc.nasa.gov/")):
            raise ValueError("Unexpected POWER source URL")
        if source_url not in source_refs:
            source_refs.append(source_url)
    retrieved_at = observations.get("retrieved_at")
    if retrieved_at is not None:
        timestamp = datetime.fromisoformat(retrieved_at)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Retrieval timestamp must include a timezone")
    data_kind = observations["data_kind"]
    if data_kind not in ("modeled", "synthetic", "observed", "mixed"):
        raise ValueError("Unsupported source data kind")
    limitations = list(observations.get("limitations", []))
    limitations.append("Gridded source estimate; not an on-farm rain gauge or exact field water availability.")
    if retrieved_at is None:
        limitations.append("Original provider retrieval time is unknown; no access timestamp has been invented.")
    if len(rain) != expected:
        limitations.append("Incomplete seasonal rainfall coverage: total is unknown; partial rainfall sums must not replace it.")
    if len(temps) != expected:
        limitations.append("Incomplete seasonal temperature coverage: the mean uses available days only.")
    if data_kind == "synthetic":
        limitations.append("Synthetic development inputs, not actual NASA observations or farm advice.")
    return {
        "start": start, "end": end, "expected_days": expected,
        "rain_valid_days": len(rain), "temperature_valid_days": len(temps),
        "rainfall_total_mm": sum(rain) if len(rain) == expected else None,
        "mean_temperature_c": sum(temps) / len(temps) if temps else None,
        "source_refs": source_refs, "source_url": source_url, "retrieved_at": retrieved_at,
        "data_kind": data_kind, "limitations": limitations,
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
