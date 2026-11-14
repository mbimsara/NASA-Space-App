"""Combine extracted SMAP passes without interpolating or averaging gaps."""
from copy import deepcopy
from datetime import date, timedelta
import math


def build_series(records, start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last or not records:
        raise ValueError("Provide extracted records and an ordered date period")
    point = records[0]["requested_point"]
    max_distance = records[0]["max_distance_km"]
    if type(max_distance) not in (int, float) or not math.isfinite(max_distance) or max_distance <= 0:
        raise ValueError("Distance policy must be finite and positive")
    by_date = {}
    provenance = []
    for record in records:
        if record["product"] != "SPL3SMP_E" or record["version"] != "006":
            raise ValueError("Do not mix products or versions")
        if record.get("data_kind") != "satellite_retrieval" or record["requested_point"] != point:
            raise ValueError("All records must represent the same requested point and data kind")
        if record["max_distance_km"] != max_distance:
            raise ValueError("Use the same distance policy for every record")
        day = date.fromisoformat(record["file_date_label"])
        if not first <= day <= last:
            raise ValueError("Input record is outside requested period")
        if day in by_date:
            raise ValueError("Duplicate granule date; resolve reprocessing versions explicitly")
        passes = {}
        for sample in record["passes"]:
            orbit = sample["pass"]
            if orbit not in ("AM", "PM") or orbit in passes:
                raise ValueError("Passes must be unique AM/PM entries")
            value = sample["soil_moisture_m3_m3"]
            if type(sample["accepted"]) is not bool:
                raise ValueError("Acceptance must be boolean")
            if sample["accepted"]:
                if (type(value) not in (int, float) or not math.isfinite(value) or not 0.02 <= value <= 1
                        or type(sample["retrieval_quality_flag"]) is not int or sample["retrieval_quality_flag"] not in (0, 8)
                        or not math.isfinite(sample["distance_km"]) or not 0 <= sample["distance_km"] <= max_distance):
                    raise ValueError("Accepted sample has invalid value, quality or distance")
            elif value is not None:
                raise ValueError("Rejected sample must carry null filtered moisture")
            passes[orbit] = deepcopy(sample)
        for orbit in ("AM", "PM"):
            passes.setdefault(orbit, {"pass": orbit, "accepted": False, "soil_moisture_m3_m3": None,
                                      "rejection_reason": "pass_absent_from_record"})
        by_date[day] = passes
        provenance.append({key: record[key] for key in ("file_name", "sha256", "file_date_label", "product_version_basis")})
    daily = []
    day = first
    while day <= last:
        passes = by_date.get(day)
        if passes is None:
            passes = {orbit: {"pass": orbit, "accepted": False, "soil_moisture_m3_m3": None,
                              "rejection_reason": "granule_not_supplied"} for orbit in ("AM", "PM")}
        daily.append({"date": day.isoformat(), "granule_supplied": day in by_date, "AM": passes["AM"], "PM": passes["PM"]})
        day += timedelta(days=1)
    return {
        "schema_version": "0.1", "kind": "smap_surface_soil_moisture_series", "data_kind": "satellite_retrieval",
        "product": "SPL3SMP_E", "version": "006", "units": "m3/m3", "requested_point": deepcopy(point),
        "period": {"start": start, "end": end}, "max_distance_km": max_distance,
        "coverage": {"expected_days": len(daily), "supplied_granule_days": len(by_date),
                     "accepted_AM": sum(row["AM"]["accepted"] for row in daily),
                     "accepted_PM": sum(row["PM"]["accepted"] for row in daily)},
        "daily": daily, "provenance": sorted(provenance, key=lambda p: p["file_date_label"]),
        "limitations": ["AM/PM remain separate; missing/rejected samples are null and are never interpolated or averaged.",
                        "File dates label composites; use raw acquisition times for actual sample timing.",
                        "Supplied files do not imply valid retrieval coverage for every pass or day.",
                        "Three days demonstrate integration, not drought status or crop suitability."],
    }
