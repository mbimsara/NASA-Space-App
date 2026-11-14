"""Reuse the standalone POWER adapter without reimplementing its calculations."""

from datetime import date, timedelta
from http.client import HTTPException
from typing import Protocol
from uuid import uuid4

from services import nasa_power

from app.config import settings
from app.schemas.observation import ObservationResponse


# Bump this namespace if endpoint, parameter selection, community/time standard,
# or normalization/HTTP semantics change. Never reuse it for synthetic adapters.
POWER_CACHE_NAMESPACE = "nasa-power-daily:T2M,PRECTOTCORR:AG:UTC:c580b4f:http-v1"


class ObservationServiceUnavailable(Exception):
    """The provider could not supply a usable observation response."""


class ObservationAdapter(Protocol):
    cache_namespace: str

    def observe(self, *, latitude: float, longitude: float, start: date, end: date) -> dict:
        """Return normalized observations; raise ObservationServiceUnavailable on failure."""
        ...


class NASAPowerObservationAdapter:
    cache_namespace = POWER_CACHE_NAMESPACE

    def observe(self, *, latitude: float, longitude: float, start: date, end: date) -> dict:
        try:
            raw, retrieved_at, source_url = nasa_power.fetch(
                latitude, longitude, start.isoformat(), end.isoformat()
            )
            return nasa_power.normalize(
                raw, start.isoformat(), end.isoformat(), retrieved_at, source_url
            )
        except (HTTPException, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            # Do not expose provider responses, URLs, or credentials to clients.
            raise ObservationServiceUnavailable from exc


def get_observation_adapter() -> ObservationAdapter | None:
    return NASAPowerObservationAdapter() if settings.nasa_power_enabled else None


def observation_response(
    normalized: dict, *, farm_id: str, input_version: int,
    latitude: float, longitude: float, start: date, end: date,
) -> ObservationResponse:
    """Add the farm envelope, preserving provider summaries and missing values."""
    summary = normalized["summary"]
    expected = (end - start).days + 1
    if summary["start"] != start.isoformat() or summary["end"] != end.isoformat():
        raise ValueError("Provider returned a different period.")
    rows = normalized["daily"]
    if [row["date"] for row in rows] != [
        (start + timedelta(days=index)).isoformat() for index in range(expected)
    ]:
        raise ValueError("Daily rows must cover every requested date, including nulls.")
    temperature_missing = [row["date"] for row in rows if row["temperature_c"] is None]
    rain_missing = [row["date"] for row in rows if row["precipitation_mm_per_day"] is None]
    if (
        summary["expected_days"] != expected
        or summary["temperature_valid_days"] != expected - len(temperature_missing)
        or summary["precipitation_valid_days"] != expected - len(rain_missing)
        or (rain_missing and summary["rainfall_total_mm"] is not None)
        or (len(temperature_missing) == expected and summary["mean_temperature_c"] is not None)
    ):
        raise ValueError("Provider summary and coverage disagree.")
    limitations = list(normalized["limitations"])
    if temperature_missing or rain_missing:
        limitations.append(
            "Incomplete coverage: missing dates are listed per variable. "
            "Rainfall totals are null if any rainfall day is missing; "
            "temperature means use available days only."
        )
    if normalized["spatial_resolution"] is None:
        limitations.append("Spatial resolution is unknown for this provider response.")
    if normalized["retrieved_at"] is None:
        limitations.append("Original provider retrieval time is unknown.")
    limitations.append(
        "Source product identifiers and API metadata are preserved; "
        "an API version is not a source dataset release version."
    )
    return ObservationResponse(
        schema_version=normalized["schema_version"],
        observation_id=str(uuid4()), farm_id=farm_id, input_version=input_version,
        data_kind=normalized["data_kind"], provider=normalized["provider"],
        period={"start": start, "end": end},
        retrieved_at=normalized["retrieved_at"], source_refs=normalized["sources"],
        source_url=normalized["source_url"], documentation_url=normalized["documentation_url"],
        api=normalized["api"], parameter_metadata=normalized["parameter_metadata"],
        spatial_resolution=normalized["spatial_resolution"], time_standard=normalized["time_standard"],
        requested_location={"latitude": latitude, "longitude": longitude},
        coordinates=normalized["coordinates"],
        coverage={
            "expected_days": expected,
            "available_days": sum(
                row["temperature_c"] is not None and row["precipitation_mm_per_day"] is not None
                for row in rows
            ),
            "temperature_valid_days": summary["temperature_valid_days"],
            "precipitation_valid_days": summary["precipitation_valid_days"],
        },
        summary={**summary, "rainfall_mm": summary["rainfall_total_mm"]},
        daily=rows, monthly=normalized["monthly"],
        units={"rainfall_mm": "mm", "rainfall_total_mm": "mm",
               "rainfall_available_days_mm": "mm", "mean_temperature_c": "C",
               "temperature_c": "C", "temperature_max_c": "C", "temperature_min_c": "C",
               "precipitation_mm_per_day": "mm/day"},
        aggregation_method={
            "rainfall_mm": "Sum daily rates over one-day intervals; null unless every day is valid.",
            "mean_temperature_c": "Arithmetic mean of valid daily means; null if no valid days.",
            "rainfall_available_days_mm": "Partial sum of valid days, not a full-period total.",
        },
        missing_data={"temperature_missing_dates": temperature_missing,
                      "precipitation_missing_dates": rain_missing},
        limitations=limitations,
    )
