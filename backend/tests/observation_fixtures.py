"""Explicitly synthetic test data; never a runtime provider fallback."""

from services import nasa_power


DATES = {"start": "2024-02-28", "end": "2024-03-01"}
RETRIEVED_AT = "2024-03-02T00:00:00+00:00"
SYNTHETIC_URL = "https://example.invalid/synthetic-nasa-power-response"


def synthetic_observations(raw, start=DATES["start"], end=DATES["end"]):
    result = nasa_power.normalize(raw, start, end, retrieved_at=RETRIEVED_AT, source_url=SYNTHETIC_URL)
    result["data_kind"] = "synthetic"
    result["limitations"].append("Invented test inputs; not NASA observations.")
    return result
