"""Small, deterministic explanations of recorded farm-profile facts.

No model, network, file access, or agricultural calculations are used here.
"""

import re
from collections.abc import Mapping


def _display(value):
    """Preserve recorded zero values; missing values are never treated as zero."""
    return "unknown" if value is None else str(value)


def explain(context, question, language="en"):
    """Return an English string explaining supported farm-profile facts.

    ``context`` is a farm profile, or the API's ``{"profile": {...}}`` envelope.
    It should follow data/schemas/farm.schema.json; this function is not a
    replacement for API schema validation. Missing fields are supported.

    Questions use simple keyword matching, not general language understanding.
    Supported topics: irrigation supply, soil measurements, farm name, area,
    location, crop history, priority weights, excluded crops, and data kind.
    Multiple supported topics can be answered together. Soil answers list all
    recorded measurements, without inferring any unrecorded measurement.

    Only ``en`` is supported. Unsupported languages and blank questions raise
    ValueError; invalid context/question types raise TypeError. The input is
    never changed. This text return value is not an HTTP response contract.
    """
    if language != "en":
        raise ValueError("Only English ('en') is supported in this milestone.")
    if not isinstance(context, Mapping):
        raise TypeError("context must be a farm profile or profile envelope.")
    if not isinstance(question, str):
        raise TypeError("question must be a string.")
    if not question.strip():
        raise ValueError("question must not be blank.")

    profile = context.get("profile", context)
    if not isinstance(profile, Mapping):
        raise TypeError("profile must be a mapping.")

    words = set(re.findall(r"[a-z]+", question.casefold()))
    answers = []
    # These topics require information or decision-making beyond a farm profile.
    unsupported = words & {
        "recommend", "recommendation", "recommendations", "should", "best",
        "predict", "prediction", "yield", "rainfall", "weather", "temperature",
        "source", "sources", "citation", "citations", "fertilizer",
    }

    if not unsupported:
        if "irrigation" in words or {"water", "supply"} <= words:
            supply = profile.get("irrigation_supply_mm_per_season")
            answers.append(
                "Irrigation supply is unknown."
                if supply is None
                else f"Recorded irrigation supply is {supply} mm per season."
            )

        if words & {"soil", "ph", "nutrient", "nutrients"}:
            measurements = profile.get("soil_tests")
            if not measurements:
                answers.append("Soil measurements are unknown; no soil tests are recorded.")
            else:
                records = [
                    f"{_display(test.get('metric'))}: {_display(test.get('value'))} "
                    f"(unit: {_display(test.get('unit'))}; "
                    f"sampled on: {_display(test.get('sampled_on'))})"
                    for test in measurements
                ]
                answers.append("Recorded soil measurements: " + "; ".join(records) + ".")
                answers.append("Any soil measurement not listed here is unknown.")

        if "name" in words:
            answers.append(f"Farm name: {_display(profile.get('name'))}.")

        if words & {"area", "size", "hectare", "hectares"}:
            area = profile.get("area_ha")
            answers.append(
                "Farm area is unknown." if area is None
                else f"Recorded farm area is {area} hectares."
            )

        if words & {"location", "located", "coordinates", "latitude", "longitude"}:
            location = profile.get("location") or {}
            answers.append(
                f"Recorded location (WGS84): latitude {_display(location.get('latitude'))}, "
                f"longitude {_display(location.get('longitude'))}."
            )

        if words & {"history", "previous", "planted", "grown"}:
            history = profile.get("crop_history")
            if not history:
                answers.append("Crop history is unknown; no crop history is recorded.")
            else:
                records = [
                    f"crop ID {_display(entry.get('crop_id'))} "
                    f"(planted: {_display(entry.get('planted_on'))}; "
                    f"harvested: {_display(entry.get('harvested_on'))})"
                    for entry in history
                ]
                answers.append("Recorded crop history: " + "; ".join(records) + ".")

        if words & {"priority", "priorities", "weight", "weights"}:
            weights = profile.get("priority_weights") or {}
            answers.append(
                "Recorded priority weights: "
                + ", ".join(f"{key}: {_display(weights.get(key))}"
                            for key in ("water", "soil", "climate"))
                + ". These are input weights, not measurements or rotation scores."
            )

        if words & {"excluded", "exclusions"}:
            excluded = profile.get("excluded_crop_ids")
            if excluded is None:
                answers.append("Excluded crop IDs are unknown.")
            elif not excluded:
                answers.append("No excluded crop IDs are recorded; this does not establish crop suitability.")
            else:
                answers.append("Recorded excluded crop IDs: " + ", ".join(excluded) + ".")

        if words & {"synthetic", "real", "kind", "provenance", "nasa"}:
            answers.append(f"Recorded data kind: {_display(profile.get('data_kind'))}.")

    if not answers:
        answers.append(
            "That information is unknown from the supported farm-profile facts. "
            "This service cannot provide crop recommendations, predictions, "
            "or source references."
        )

    if profile.get("data_kind") == "synthetic":
        answers.insert(0, "This profile contains synthetic demonstration inputs, not real farm observations.")
    return " ".join(answers)
