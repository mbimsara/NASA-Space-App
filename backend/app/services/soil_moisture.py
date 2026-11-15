"""Serve a verified local SMAP series without inventing global farm coverage."""

import json
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from app.schemas.soil_moisture import SoilMoistureResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SMAP_SERIES = REPOSITORY_ROOT / ".cache" / "smap" / "january-2025" / "series.json"
SMAP_SOURCE = "NASA NSIDC SPL3SMP_E V006; DOI:10.5067/M20OXIZHY3RJ"


class SoilMoistureUnavailable(RuntimeError):
    pass


def distance_km(first: dict, second: dict) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (
        first["latitude"], first["longitude"], second["latitude"], second["longitude"],
    ))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371.0088 * 2 * asin(sqrt(value))


def load_soil_moisture(farm, path: Path = DEFAULT_SMAP_SERIES) -> SoilMoistureResponse:
    try:
        series = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SoilMoistureUnavailable("Verified SMAP series is not available locally.") from exc

    farm_point = farm.profile["location"]
    separation = distance_km(farm_point, series["requested_point"])
    if separation > series["max_distance_km"]:
        raise SoilMoistureUnavailable(
            "The available SMAP demonstration series does not cover this farm location."
        )

    payload = {
        key: series[key] for key in (
            "schema_version", "kind", "data_kind", "product", "version", "units",
            "requested_point", "period", "max_distance_km", "coverage", "daily", "limitations",
        )
    }
    payload.update({
        "farm_id": farm.id,
        "input_version": farm.input_version,
        "farm_distance_km": separation,
        "source_refs": [SMAP_SOURCE],
        "limitations": [
            *(item for item in payload["limitations"] if "Three days demonstrate" not in item),
            f"Coverage contains {series['coverage']['accepted_AM']} accepted AM and {series['coverage']['accepted_PM']} accepted PM retrievals across {series['coverage']['expected_days']} requested days; missing or rejected passes remain null.",
            "Regional surface-moisture context only; not a field measurement, root-zone estimate, nutrient test, irrigation requirement, or soil-health score.",
            "This endpoint currently exposes only the verified January 2025 Sri Lankan demonstration subset.",
        ],
    })
    return SoilMoistureResponse.model_validate(payload)
