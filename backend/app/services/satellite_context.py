"""Load verified local NASA context artifacts and prevent reuse at other farms."""

import json
from pathlib import Path

from app.schemas.satellite_context import GpmContext, HlsContext
from app.services.soil_moisture import distance_km


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_GPM_SERIES = REPOSITORY_ROOT / ".cache" / "gpm" / "series.json"
DEFAULT_HLS_SERIES = REPOSITORY_ROOT / ".cache" / "hls" / "series.json"


class SatelliteContextUnavailable(RuntimeError):
    pass


def _load(farm, path: Path, schema, max_distance_km: float):
    try:
        artifact = json.loads(path.read_text(encoding="utf-8-sig"))
        separation = distance_km(farm.profile["location"], artifact["requested_point"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SatelliteContextUnavailable("Verified satellite artifact is unavailable.") from exc
    if separation > max_distance_km:
        raise SatelliteContextUnavailable("The artifact does not cover this farm location.")
    artifact.update({
        "farm_id": farm.id,
        "input_version": farm.input_version,
        "farm_distance_km": separation,
    })
    try:
        return schema.model_validate(artifact)
    except ValueError as exc:
        raise SatelliteContextUnavailable("Satellite artifact failed its contract.") from exc


def load_gpm(farm, path: Path = DEFAULT_GPM_SERIES) -> GpmContext:
    # A 0.1-degree IMERG cell is roughly 11 km at the equator. This conservative
    # bound prevents a point export being presented as coverage for another area.
    return _load(farm, path, GpmContext, 8.0)


def load_hls(farm, path: Path = DEFAULT_HLS_SERIES) -> HlsContext:
    # Point/field HLS samples are local; never reuse the demonstration export.
    return _load(farm, path, HlsContext, 1.0)
