"""Combine source payloads without implying temporal or spatial equivalence."""
from copy import deepcopy
from datetime import date, timedelta
from backend.services.climate import checked_rows
from backend.services.climate_handoff import climate_bundle


def build_environment(power, farm_id, observation_id, input_version, smap=None):
    rows = checked_rows(power)
    summary = power["summary"]
    if (summary["start"] != rows[0]["date"] or summary["end"] != rows[-1]["date"]
            or summary["expected_days"] != len(rows)):
        raise ValueError("POWER period metadata disagrees with daily rows")
    for field, count in (("temperature_c", "temperature_valid_days"), ("precipitation_mm_per_day", "precipitation_valid_days")):
        if summary[count] != sum(row[field] is not None for row in rows):
            raise ValueError("POWER coverage metadata disagrees with daily rows")
    bundle = climate_bundle(power, farm_id, observation_id, input_version)
    point = {"latitude": power["coordinates"][1], "longitude": power["coordinates"][0]}
    moisture = {"status": "not_supplied", "result": None}
    overlap = None
    if smap is not None:
        if smap.get("kind") != "smap_surface_soil_moisture_series" or smap["product"] != "SPL3SMP_E" or smap["version"] != "006" or smap["units"] != "m3/m3":
            raise ValueError("Unsupported SMAP series contract")
        if any(abs(smap["requested_point"][key] - point[key]) > 0.0001 for key in point):
            raise ValueError("POWER and SMAP requested points differ")
        if (power["data_kind"] == "synthetic") != (smap["data_kind"] == "synthetic"):
            raise ValueError("Do not mix synthetic examples with provider-derived data")
        first, last = date.fromisoformat(smap["period"]["start"]), date.fromisoformat(smap["period"]["end"])
        expected = (last - first).days + 1
        if expected < 1 or len(smap["daily"]) != expected:
            raise ValueError("SMAP period length disagrees with daily rows")
        for index, row in enumerate(smap["daily"]):
            if row["date"] != (first + timedelta(days=index)).isoformat():
                raise ValueError("SMAP dates must cover the period once in order")
            for orbit in ("AM", "PM"):
                sample = row[orbit]
                if type(sample["accepted"]) is not bool or (sample["soil_moisture_m3_m3"] is None) == sample["accepted"]:
                    raise ValueError("SMAP pass acceptance/value mismatch")
        counts = {"expected_days": expected,
                  "supplied_granule_days": sum(row["granule_supplied"] for row in smap["daily"]),
                  "accepted_AM": sum(row["AM"]["accepted"] for row in smap["daily"]),
                  "accepted_PM": sum(row["PM"]["accepted"] for row in smap["daily"])}
        if counts != smap["coverage"]:
            raise ValueError("SMAP coverage metadata disagrees with daily rows")
        accepted = counts["accepted_AM"] + counts["accepted_PM"]
        status = "no_accepted_retrievals" if accepted == 0 else "complete" if accepted == expected * 2 else "partial"
        moisture = {"status": status, "result": deepcopy(smap)}
        overlap_start = max(summary["start"], first.isoformat())
        overlap_end = min(summary["end"], last.isoformat())
        if overlap_start <= overlap_end:
            overlap = {"start": overlap_start, "end": overlap_end}
    complete = summary["temperature_valid_days"] == len(rows) and summary["precipitation_valid_days"] == len(rows)
    return {
        "schema_version": "0.1", "kind": "farm_environment", "farm_id": farm_id,
        "observation_id": observation_id, "input_version": input_version,
        "data_kind": "synthetic" if power["data_kind"] == "synthetic" else "mixed" if smap else power["data_kind"],
        "requested_point": point, "climate": {"status": "complete" if complete else "partial", "result": bundle},
        "soil_moisture": moisture, "date_label_overlap": overlap,
        "limitations": ["Common requested coordinates do not imply common footprints or sampling times.",
                        "Calendar-label overlap is not acquisition-time alignment.",
                        "Each source retains its own period, coverage, provenance and quality rules.",
                        "No combined farm health score, drought diagnosis or agronomic recommendation is generated."],
    }
