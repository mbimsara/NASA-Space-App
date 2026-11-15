"""Normalize quality-screened NASA HLS vegetation-index point/field exports."""

from datetime import date
from math import isfinite


def normalize_observations(rows, *, latitude, longitude, source_refs, retrieved_at=None):
    if not rows or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Provide observations and a valid point")
    normalized, seen = [], set()
    for row in sorted(rows, key=lambda item: item["date"]):
        day = date.fromisoformat(row["date"])
        product = row["product"]
        if (day, product) in seen or product not in {"HLSL30", "HLSS30"}:
            raise ValueError("HLS observations require unique date/product pairs")
        seen.add((day, product))
        ndvi, cloud = row.get("ndvi"), row.get("cloud_percent")
        if ndvi is not None and (type(ndvi) not in (int, float) or not isfinite(ndvi) or not -1 <= ndvi <= 1):
            raise ValueError("NDVI must be within -1..1 or null")
        if type(cloud) not in (int, float) or not isfinite(cloud) or not 0 <= cloud <= 100:
            raise ValueError("Cloud percentage must be within 0..100")
        accepted = bool(row.get("quality_accepted"))
        if not accepted and ndvi is not None:
            raise ValueError("Quality-rejected HLS observations must keep NDVI null")
        normalized.append({"date": day.isoformat(), "product": product, "ndvi": ndvi,
                           "cloud_percent": float(cloud), "quality_accepted": accepted,
                           "rejection_reason": row.get("rejection_reason")})
    return {
        "schema_version": "0.1", "kind": "hls_vegetation_series",
        "data_kind": "satellite_retrieval", "products": ["HLSL30", "HLSS30"], "version": "2.0",
        "index": "NDVI", "requested_point": {"latitude": latitude, "longitude": longitude},
        "spatial_resolution_m": 30, "period": {"start": normalized[0]["date"], "end": normalized[-1]["date"]},
        "coverage": {"supplied_observations": len(normalized),
                     "accepted_observations": sum(item["quality_accepted"] for item in normalized)},
        "observations": normalized, "source_refs": list(dict.fromkeys(source_refs)),
        "retrieved_at": retrieved_at,
        "limitations": [
            "NDVI indicates surface greenness; it is not crop identity, yield, nutrient status or proof of crop health.",
            "Cloud, shadow, snow/water and other quality flags must be screened before acceptance.",
            "Landsat and Sentinel-2 observations retain their product identity and acquisition date.",
        ],
    }
