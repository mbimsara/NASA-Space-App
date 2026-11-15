"""Normalize explicit NASA GPM IMERG daily point exports without hiding gaps."""

from datetime import date, timedelta
from math import isfinite


def normalize_daily(rows, *, latitude, longitude, start, end, source_refs, retrieved_at=None):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid point or period")
    by_date = {}
    for row in rows:
        day = date.fromisoformat(row["date"])
        if day in by_date or not first <= day <= last:
            raise ValueError("GPM rows must be unique and inside the requested period")
        value = row.get("precipitation_mm")
        if value is not None and (type(value) not in (int, float) or not isfinite(value) or value < 0):
            raise ValueError("GPM daily precipitation must be finite, non-negative or null")
        by_date[day] = float(value) if value is not None else None
    daily, cursor = [], first
    while cursor <= last:
        daily.append({"date": cursor.isoformat(), "precipitation_mm": by_date.get(cursor)})
        cursor += timedelta(days=1)
    valid = sum(row["precipitation_mm"] is not None for row in daily)
    return {
        "schema_version": "0.1", "kind": "gpm_imerg_daily_series",
        "data_kind": "satellite_retrieval", "product": "GPM_3IMERGDF", "version": "07",
        "units": "mm/day", "requested_point": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start, "end": end}, "spatial_resolution_degrees": 0.1,
        "coverage": {"expected_days": len(daily), "valid_days": valid}, "daily": daily,
        "source_refs": list(dict.fromkeys(source_refs)), "retrieved_at": retrieved_at,
        "limitations": [
            "IMERG is a gridded satellite precipitation estimate, not an on-farm rain gauge.",
            "Missing days remain null and are not replaced with POWER or interpolated values.",
            "POWER and IMERG retain separate values, footprints and provenance.",
        ],
    }
