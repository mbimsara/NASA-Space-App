"""Competition-listed NASA POWER daily adapter; standard library only."""
import json
import math
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
DOCS = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"
CHALLENGE = "https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/?tab=resources"


def request_url(latitude, longitude, start, end, include_extremes=False):
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (latitude, longitude)):
        raise ValueError("Coordinates must be finite numbers")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates out of range")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or first < date(1981, 1, 1) or last >= datetime.now(timezone.utc).date():
        raise ValueError("Use historical dates from 1981, with start <= end")
    return ENDPOINT + "?" + urlencode({
        "parameters": "T2M,PRECTOTCORR,T2M_MAX,T2M_MIN" if include_extremes else "T2M,PRECTOTCORR", "community": "AG",
        "latitude": latitude, "longitude": longitude,
        "start": first.strftime("%Y%m%d"), "end": last.strftime("%Y%m%d"),
        "format": "JSON", "time-standard": "UTC",
    })


def fetch(latitude, longitude, start, end, include_extremes=False):
    """One request, no repeated retries. Caller controls caching."""
    url = request_url(latitude, longitude, start, end, include_extremes)
    with urlopen(url, timeout=60) as response:
        raw = json.load(response)
    return raw, datetime.now(timezone.utc).isoformat(), url


def normalize(raw, start, end, retrieved_at=None, source_url=None):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        raise ValueError("Start must not follow end")
    header = raw["header"]
    if header["start"] != first.strftime("%Y%m%d") or header["end"] != last.strftime("%Y%m%d"):
        raise ValueError("Response period does not match request")
    if header["time_standard"] != "UTC":
        raise ValueError("Expected UTC daily data")
    metadata = raw["parameters"]
    if metadata["T2M"]["units"] != "C" or metadata["PRECTOTCORR"]["units"] != "mm/day":
        raise ValueError("Unexpected provider units; review conversion before use")
    values = raw["properties"]["parameter"]
    for parameter in ("T2M_MAX", "T2M_MIN"):
        if parameter in values and metadata[parameter]["units"] != "C":
            raise ValueError("Unexpected extreme-temperature units")
    fill = header["fill_value"]

    def clean(value, precipitation=False):
        if value is None or value == fill:
            return None
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Invalid numeric observation")
        if precipitation and value < 0:
            raise ValueError("Negative precipitation is not a valid observation")
        return value

    rows = []
    day = first
    while day <= last:
        key = day.strftime("%Y%m%d")
        rows.append({"date": day.isoformat(),
                     "temperature_c": clean(values["T2M"].get(key)),
                     "precipitation_mm_per_day": clean(values["PRECTOTCORR"].get(key), True)})
        for parameter, field in (("T2M_MAX", "temperature_max_c"), ("T2M_MIN", "temperature_min_c")):
            rows[-1][field] = clean(values.get(parameter, {}).get(key))
        low, mean, high = rows[-1]["temperature_min_c"], rows[-1]["temperature_c"], rows[-1]["temperature_max_c"]
        if (low is not None and high is not None and low > high
                or low is not None and mean is not None and low > mean
                or high is not None and mean is not None and mean > high):
            raise ValueError("Inconsistent minimum, mean and maximum temperature")
        day += timedelta(days=1)

    def summarize(group):
        temps = [r["temperature_c"] for r in group if r["temperature_c"] is not None]
        rain = [r["precipitation_mm_per_day"] for r in group if r["precipitation_mm_per_day"] is not None]
        maxima = [r["temperature_max_c"] for r in group if r["temperature_max_c"] is not None]
        minima = [r["temperature_min_c"] for r in group if r["temperature_min_c"] is not None]
        return {
            "start": group[0]["date"], "end": group[-1]["date"],
            "expected_days": len(group), "temperature_valid_days": len(temps),
            "precipitation_valid_days": len(rain),
            "mean_temperature_c": round(sum(temps) / len(temps), 4) if temps else None,
            "rainfall_total_mm": round(sum(rain), 4) if len(rain) == len(group) else None,
            "rainfall_available_days_mm": round(sum(rain), 4) if rain else None,
            "maximum_temperature_valid_days": len(maxima), "minimum_temperature_valid_days": len(minima),
            "highest_available_daily_max_c": max(maxima) if maxima else None,
            "lowest_available_daily_min_c": min(minima) if minima else None,
        }

    months = {}
    for row in rows:
        months.setdefault(row["date"][:7], []).append(row)
    return {
        "schema_version": "0.1", "data_kind": "modeled",
        "provider": "NASA POWER", "sources": header["sources"],
        "api": header["api"], "time_standard": "UTC",
        "coordinates": raw["geometry"]["coordinates"],
        "retrieved_at": retrieved_at, "source_url": source_url,
        "documentation_url": DOCS, "competition_resource_url": CHALLENGE,
        "parameter_metadata": metadata, "provider_fill_value": fill,
        "spatial_resolution": {
            "latitude_degrees": 0.5, "longitude_degrees": 0.625,
            "source": "https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/",
        } if header["sources"] == ["MERRA2"] else None,
        "summary": summarize(rows),
        "monthly": [{"month": month, **summarize(group)} for month, group in months.items()],
        "daily": rows,
        "limitations": [
            "Gridded environmental estimates, not measurements of this individual field.",
            "Meteorological grid resolution is regional; farm coordinates do not imply field-scale precision.",
            "Temperature means use valid days; check coverage before comparisons.",
            "Rain totals integrate daily rates over one-day intervals; incomplete periods have null totals.",
            "Monthly entries cover requested dates only, which may be partial calendar months.",
            "Imported files may have unknown original retrieval dates.",
        ],
    }
