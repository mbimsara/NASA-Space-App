"""Durable snapshots, expiring cache selection, and future analysis references."""

from copy import deepcopy
from datetime import date
import hashlib
import json
from time import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.farm import Farm
from app.models.observation import ObservationSnapshot
from app.schemas.observation import ObservationResponse
from app.services.observations import (
    ObservationAdapter, ObservationServiceUnavailable, POWER_CACHE_NAMESPACE,
    observation_response,
)


class ObservationNotFound(LookupError):
    """An observation ID does not exist (map to 404 in an API)."""


class ObservationContextConflict(ValueError):
    """The observation does not match the requested/current farm version (409)."""


def latest_snapshot(db: Session, cache_key: str) -> ObservationSnapshot | None:
    return db.scalar(
        select(ObservationSnapshot)
        .where(ObservationSnapshot.cache_key == cache_key)
        .order_by(ObservationSnapshot.generation.desc())
        .limit(1)
    )


def snapshot_response(snapshot: ObservationSnapshot) -> ObservationResponse:
    response = ObservationResponse.model_validate(deepcopy(snapshot.payload))
    if (
        response.observation_id != snapshot.id
        or response.farm_id != snapshot.farm_id
        or response.input_version != snapshot.input_version
        or response.requested_location.model_dump() != snapshot.farm_profile["location"]
    ):
        raise ValueError("Stored observation context is inconsistent.")
    return response


def get_or_fetch_snapshot(
    db: Session, farm: Farm, *, start: date, end: date,
    adapter: ObservationAdapter | None,
) -> tuple[ObservationSnapshot, bool]:
    """Use an endpoint-owned session; release its read transaction before network I/O."""
    farm_id, input_version = farm.id, farm.input_version
    profile = deepcopy(farm.profile)
    latitude, longitude = profile["location"]["latitude"], profile["location"]["longitude"]
    namespace = getattr(adapter, "cache_namespace", None) if adapter is not None else POWER_CACHE_NAMESPACE
    if not isinstance(namespace, str) or not namespace.strip():
        raise ObservationServiceUnavailable("Adapter must identify its cache namespace.")
    # Include the farm version even when a PATCH changes something other than location.
    # Provider/normalizer settings are captured in the adapter's versioned namespace.
    key = hashlib.sha256(json.dumps({
        "farm_id": farm_id, "input_version": input_version,
        "latitude": latitude, "longitude": longitude,
        "start": start.isoformat(), "end": end.isoformat(),
        "adapter": namespace,
    }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    cached = latest_snapshot(db, key)
    if cached is not None and cached.expires_at > time():
        snapshot_response(cached)
        return cached, True

    # End the SELECT transaction before the slow provider request so concurrent
    # farm edits and cache writers do not wait for network access.
    db.rollback()
    if adapter is None:
        raise ObservationServiceUnavailable
    normalized = adapter.observe(latitude=latitude, longitude=longitude, start=start, end=end)
    response = observation_response(
        normalized, farm_id=farm_id, input_version=input_version,
        latitude=latitude, longitude=longitude, start=start, end=end,
    )
    payload = response.model_dump(mode="json")
    # Concurrent workers can fetch in parallel. The unique key/generation picks
    # one committed winner, so successful identical requests reuse one stable ID.
    for _ in range(3):
        cached = latest_snapshot(db, key)
        now = time()
        if cached is not None and cached.expires_at > now:
            snapshot_response(cached)
            return cached, True
        snapshot = ObservationSnapshot(
            id=response.observation_id, cache_key=key,
            generation=1 if cached is None else cached.generation + 1,
            farm_id=farm_id, input_version=input_version, farm_profile=profile,
            cached_at=now, expires_at=now + settings.observation_cache_ttl_seconds,
            payload=payload,
        )
        db.add(snapshot)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # A cache race is recoverable only if another row won this key.
            winner = latest_snapshot(db, key)
            if winner is None:
                raise
            db.rollback()
            continue
        return snapshot, False
    raise ObservationServiceUnavailable("Concurrent cache writes did not settle; retry.")


def require_observation_for_analysis(
    db: Session, observation_id: str, *, farm_id: str, input_version: int,
) -> ObservationSnapshot:
    """Validate a persisted reference without implementing any crop analysis.

    Cache expiry does not invalidate a historical snapshot. Farm/version mismatch
    does invalidate using it for a new analysis of the current farm inputs.
    """
    snapshot = db.get(ObservationSnapshot, observation_id)
    if snapshot is None:
        raise ObservationNotFound("Observation not found.")
    current_version = db.scalar(select(Farm.input_version).where(Farm.id == farm_id))
    if (
        snapshot.farm_id != farm_id or snapshot.input_version != input_version
        or current_version != input_version
    ):
        raise ObservationContextConflict("Observation does not match the current farm input version.")
    snapshot_response(snapshot)
    return snapshot
