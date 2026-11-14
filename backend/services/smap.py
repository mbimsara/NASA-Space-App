"""Public SMAP metadata discovery and documented V006 retrieval-quality gate.

This module does not download or extract authenticated HDF5 science data.
"""
import json
import math
from datetime import date, timedelta, datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen

PRODUCT = "SPL3SMP_E"
VERSION = "006"
DOI = "https://doi.org/10.5067/M20OXIZHY3RJ"
GUIDE = "https://nsidc.org/sites/default/files/documents/user-guide/spl3smp_e-v006-userguide.pdf"


def search_url(latitude, longitude, start, end, page=1):
    if not all(type(v) in (int, float) and math.isfinite(v) for v in (latitude, longitude)):
        raise ValueError("Coordinates must be finite numbers")
    if not -85.044 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates outside product coverage")
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first < date(2015, 3, 31) or first > last or last >= datetime.now(timezone.utc).date():
        raise ValueError("Use past dates within the SMAP record and start <= end")
    if type(page) is not int or page < 1:
        raise ValueError("Page must be a positive integer")
    return "https://cmr.earthdata.nasa.gov/search/granules.json?" + urlencode({
        "short_name": PRODUCT, "version": VERSION,
        "point": f"{longitude},{latitude}",
        "temporal": f"{start}T00:00:00Z,{(last + timedelta(days=1)).isoformat()}T00:00:00Z",
        "page_size": 100, "page_num": page, "sort_key": "start_date",
    })


def discover(latitude, longitude, start, end):
    """Small sample discovery; full-date granules may include next-midnight boundary hits."""
    if (date.fromisoformat(end) - date.fromisoformat(start)).days > 30:
        raise ValueError("Initial discovery is limited to 31 days; choose a small sample")
    url = search_url(latitude, longitude, start, end)
    with urlopen(url, timeout=60) as response:
        raw = json.load(response)
        hits = int(response.headers.get("CMR-Hits", 0))
    granules = []
    for entry in raw["feed"]["entry"]:
        # Avoid inclusivity boundary hits starting after the requested last day.
        if entry.get("time_start", "")[:10] > end:
            continue
        links = [link["href"] for link in entry.get("links", [])
                 if link.get("rel", "").endswith("/data#") and not link.get("inherited", False)
                 and link.get("href", "").startswith("https://")]
        granules.append({"concept_id": entry["id"], "producer_granule_id": entry.get("producer_granule_id"),
                         "start": entry.get("time_start"), "end": entry.get("time_end"), "data_links": links})
    return {"kind": "granule_metadata_only", "product": PRODUCT, "version": VERSION, "doi": DOI,
            "query_url": url, "requested_point": {"latitude": latitude, "longitude": longitude},
            "requested_period": {"start": start, "end": end},
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "cmr_hits_before_boundary_filter": hits,
            "truncated": hits > 100, "granules": granules,
            "limitations": ["Metadata discovery does not establish valid science retrievals at the requested point.",
                            "Data links require Earthdata access; no data download was attempted.",
                            "Granules may be global; subset before retrieval to avoid unrelated regions."]}


def quality_filter(value, retrieval_quality_flag, fill_value=-9999.0):
    """Apply V006 guide's recommended-quality flags 0 or 8; retain raw context.

    Input is one extracted pixel with m3/m3 units already checked by a future reader.
    A physical broad bound is not a replacement for product valid_max/porosity checks.
    """
    reason = None
    if value is None or value == fill_value:
        reason = "missing_value"
    elif type(value) not in (int, float) or not math.isfinite(value) or not 0.02 <= value <= 1:
        reason = "outside_broad_physical_bounds"
    elif type(retrieval_quality_flag) is not int or retrieval_quality_flag not in (0, 8):
        reason = "quality_not_recommended"
    return {"soil_moisture_m3_m3": value if reason is None else None,
            "retrieval_quality_flag": retrieval_quality_flag,
            "accepted": reason is None, "rejection_reason": reason}
