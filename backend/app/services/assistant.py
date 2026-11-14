"""Small, deterministic explanations of supplied farm and analysis facts.

No model, network, file access, or agricultural calculations are used here.
"""

import re
from collections.abc import Mapping

from .assistant_results import explain_results


def _display(value):
    """Preserve recorded zero values; missing values are never treated as zero."""
    return "unknown" if value is None else str(value)


def _unavailable(context):
    """Decline requests outside the recorded-fact contract before routing."""
    records = [context, context.get("profile"), context.get("analysis"),
               context.get("scenario"), context.get("observations")]
    synthetic = any(isinstance(record, Mapping) and record.get("data_kind") == "synthetic"
                    for record in records)
    label = "The supplied context contains synthetic demonstration inputs. " if synthetic else ""
    return (label + "That information is unknown or unavailable from the supplied context. "
            "This service cannot provide crop recommendations, forecasts, newly inferred rankings, "
            "unit conversions, edited records, invented measurements, or invented source references.")


def _explain(context, question, language="en", *, trace=None):
    """Return an English string explaining supported farm-profile facts.

    ``context`` is a farm profile, or the API's ``{"profile": {...}}`` envelope.
    It should follow data/schemas/farm.schema.json; this function is not a
    replacement for API schema validation. Missing fields are supported.

    Questions use simple keyword matching, not general language understanding.
    Supported topics: irrigation supply, soil measurements, farm name, area,
    location, crop history, priority weights, excluded crops, and data kind.
    Multiple supported topics can be answered together. Soil answers list all
    recorded measurements, without inferring any unrecorded measurement.

    Optional ``analysis``, ``scenario``, and ``observations`` mappings enable
    rotation, water-budget, scenario, and source explanations. ``candidate_id``
    selects a candidate by exact ID. See backend/tests/fixtures/README.md for
    the local nested data shapes; these are not new API contracts. Recorded
    ranks/differences are reported, never computed. Conflicting context IDs
    raise ValueError rather than combining unrelated results.

    Analytical questions select focused water, ranking/candidate, scenario,
    observation, or source views. "show full analysis" requests all sections.
    Water questions default to baseline results; comparison/scenario questions
    include the supplied hypothetical results. Farm questions keep their own
    profile context, including unknown irrigation and soil measurements.

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
    # The service is a read-only explainer. Questions cannot supply new facts.
    blocked = words & {
        "recommend", "recommendation", "recommendations", "should", "best",
        "predict", "prediction", "forecast", "forecasts", "yield", "fertilizer",
        "tomorrow", "tomorrows", "future", "lowest", "highest", "smallest", "largest",
        "invent", "fabricate", "pretend", "ignore", "override",
        "set", "update", "delete", "acres", "acre", "liters", "litres",
    }
    future = re.search(r"\bnext\s+(?:day|week|month|year|season)\b", question.casefold())
    make_up = re.search(r"\bmake\s+up\b", question.casefold())
    if blocked or future or make_up or any(ord(char) < 32 and not char.isspace() for char in question):
        if trace is not None:
            trace.unsupported()
        return _unavailable(context)
    result = explain_results(context, words, question, trace=trace)
    if result is not None:
        return result
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
            if trace is not None and supply is None:
                trace.missing()
            answers.append(
                "Irrigation supply is unknown."
                if supply is None
                else f"Recorded irrigation supply is {supply} mm per season."
            )

        if words & {"soil", "ph", "nutrient", "nutrients"}:
            measurements = profile.get("soil_tests")
            if not measurements:
                if trace is not None:
                    trace.missing()
                answers.append("Soil measurements are unknown; no soil tests are recorded.")
            else:
                if trace is not None and any(test.get("value") is None for test in measurements):
                    trace.missing()
                records = [
                    f"{_display(test.get('metric'))}: {_display(test.get('value'))} "
                    f"(unit: {_display(test.get('unit'))}; "
                    f"sampled on: {_display(test.get('sampled_on'))})"
                    for test in measurements
                ]
                answers.append("Recorded soil measurements: " + "; ".join(records) + ".")
                answers.append("Any soil measurement not listed here is unknown.")

        if "name" in words or {"farm", "called"} <= words:
            if trace is not None and profile.get("name") is None:
                trace.missing()
            answers.append(f"Farm name: {_display(profile.get('name'))}.")

        if words & {"area", "size", "hectare", "hectares"}:
            area = profile.get("area_ha")
            if trace is not None and area is None:
                trace.missing()
            answers.append(
                "Farm area is unknown." if area is None
                else f"Recorded farm area is {area} hectares."
            )

        if words & {"location", "located", "coordinates", "latitude", "longitude"} or {"where", "farm"} <= words:
            location = profile.get("location") or {}
            if trace is not None and any(location.get(key) is None for key in ("latitude", "longitude")):
                trace.missing()
            answers.append(
                f"Recorded location (WGS84): latitude {_display(location.get('latitude'))}, "
                f"longitude {_display(location.get('longitude'))}."
            )

        if words & {"history", "previous", "previously", "planted", "grown", "grow"}:
            history = profile.get("crop_history")
            if not history:
                if trace is not None:
                    trace.missing()
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
            if trace is not None and any(weights.get(key) is None for key in ("water", "soil", "climate")):
                trace.missing()
            answers.append(
                "Recorded priority weights: "
                + ", ".join(f"{key}: {_display(weights.get(key))}"
                            for key in ("water", "soil", "climate"))
                + ". These are input weights, not measurements or rotation scores."
            )

        if words & {"excluded", "exclusions"}:
            excluded = profile.get("excluded_crop_ids")
            if excluded is None:
                if trace is not None:
                    trace.missing()
                answers.append("Excluded crop IDs are unknown.")
            elif not excluded:
                answers.append("No excluded crop IDs are recorded; this does not establish crop suitability.")
            else:
                answers.append("Recorded excluded crop IDs: " + ", ".join(excluded) + ".")

        if words & {"synthetic", "real", "kind", "provenance", "nasa"}:
            if trace is not None and profile.get("data_kind") is None:
                trace.missing()
            answers.append(f"Recorded data kind: {_display(profile.get('data_kind'))}.")

    if not answers:
        if trace is not None:
            trace.unsupported()
        answers.append(
            "That information is unknown from the supported farm-profile facts. "
            "This service cannot provide crop recommendations, predictions, "
            "or source references."
        )

    elif trace is not None:
        trace.add(profile)
    if profile.get("data_kind") == "synthetic":
        answers.insert(0, "This profile contains synthetic demonstration inputs, not real farm observations.")
    elif profile.get("data_kind") == "farmer_input":
        answers.insert(0, "These are farmer-entered values, not NASA measurements.")
    return " ".join(answers)


def explain(context, question, language="en"):
    """Return deterministic English text; the original public interface.

    For teammate dataclasses and richer provenance, first use normalize_context()
    or call assistant_response.respond() for a structured result. No model,
    network, database, scoring, or scientific recalculation is performed.
    """
    return _explain(context, question, language)
