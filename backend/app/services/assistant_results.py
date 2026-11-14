"""Format supplied analytical results without scoring, forecasting, or lookup."""

import math
from collections.abc import Mapping


WATER_FIELDS = (
    ("demand_mm", "demand"),
    ("rainfall_mm", "rainfall"),
    ("effective_rainfall_mm", "effective rainfall"),
    ("irrigation_supply_mm", "irrigation supply"),
    ("deficit_mm", "deficit"),
)


def _record(value):
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("Analytical records must be mappings or None.")
    return value


def _text(value):
    return "unknown" if value is None else str(value)


def _number(value, unit=""):
    # Reject booleans, numeric strings, NaN, and infinity as measurements.
    if type(value) not in (int, float) or not math.isfinite(value):
        return "unknown"
    return f"{value}{unit}"


def _items(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError("Analytical collections must be lists or None.")
    return value


def _notes(value):
    entries = _items(value)
    if any(not isinstance(entry, str) for entry in entries):
        raise TypeError("Notes and source references must be lists of strings.")
    return "; ".join(entries) if entries else "unknown (none supplied)"


def _provenance(record):
    labels = {
        "synthetic": "Synthetic test data, not actual NASA observations or validated agronomic advice.",
        "modeled": "Model estimates, not measured NASA observations.",
        "observed": "Observed data as labeled by the supplied context; NASA origin is not independently verified.",
        "mixed": "Mixed data; individual values cannot be classified without their own provenance.",
    }
    return labels.get(record.get("data_kind"), "Data kind is unknown; NASA origin cannot be established.")


def _metadata(record):
    return (
        f"Source references (supplied IDs only): {_notes(record.get('source_refs'))}. "
        f"Assumptions: {_notes(record.get('assumptions'))}. "
        f"Limitations: {_notes(record.get('limitations'))}."
    )


def _water(budget, delta=False):
    budget = _record(budget)
    prefix = "Supplied water-budget differences (scenario minus baseline)" if delta else "Water budget"
    values = "; ".join(
        f"{label}: {_number(budget.get(key), ' mm')}" for key, label in WATER_FIELDS
    )
    if delta:
        return f"{prefix}: {values}."
    period = _record(budget.get("period"))
    return (
        f"{prefix} period: {_text(period.get('start'))} to {_text(period.get('end'))}; {values}. "
        f"Effective rainfall assumption: {_text(budget.get('effective_rainfall_assumption'))}."
    )


def _candidates(record, selected):
    candidates = record.get("candidates")
    if candidates is None:
        return "Candidates and their rankings, scores, and water budgets are unknown."
    candidates = [_record(item) for item in _items(candidates)]
    if not candidates:
        return f"No feasible candidates were supplied. Supplied reasons: {_notes(record.get('reasons'))}."
    if selected is not None:
        candidates = [item for item in candidates if item.get("candidate_id") == selected]
        if not candidates:
            return f"Candidate {_text(selected)} is unknown in these results."

    answers = []
    for candidate in candidates:
        sequence = [
            f"season {_text(step.get('season_index'))}: crop ID {_text(step.get('crop_id'))}"
            for step in map(_record, _items(candidate.get("sequence")))
        ]
        components = [
            f"{name}: value {_number(_record(component).get('value'))}, "
            f"weight {_number(_record(component).get('weight'))}, "
            f"direction {_text(_record(component).get('direction'))}"
            for name, component in _record(candidate.get("score_components")).items()
        ]
        answers.extend([
            f"Candidate {_text(candidate.get('candidate_id'))}: "
            f"supplied rank {_number(candidate.get('rank'))}; "
            f"supplied score {_number(candidate.get('score'))} (scale not inferred).",
            "Supplied crop sequence: " + ("; ".join(sequence) or "unknown") + ".",
            "Score components: " + ("; ".join(components) or "unknown") + ".",
            f"Supplied reasons: {_notes(candidate.get('reasons'))}.",
            _water(candidate.get("water_budget")),
        ])
    answers.append("Ranks are not inferred from list order or scores; no new crop recommendation is generated.")
    return " ".join(answers)


def _differences(scenario, selected):
    differences = scenario.get("differences")
    if differences is None:
        return "Baseline differences are unknown; this service does not calculate them."
    records = [_record(item) for item in _items(differences)]
    if selected is not None:
        records = [item for item in records if item.get("candidate_id") == selected]
    if not records:
        return "Baseline differences are unknown (none supplied for the selected results)."
    return " ".join(
        f"Candidate {_text(item.get('candidate_id'))}: supplied score difference "
        f"(scenario minus baseline): {_number(item.get('score_delta'))}. "
        + _water(item.get("water_budget"), delta=True)
        for item in records
    )


def explain_results(context, words):
    """Return analytical text, or None to leave the original farm handler active."""
    if words & {"recommend", "recommendation", "recommendations", "should", "best",
                "predict", "prediction", "yield", "fertilizer", "forecast"}:
        return None
    topics = {
        "rotation", "rotations", "candidate", "candidates", "rank", "ranked",
        "ranking", "rankings", "score", "scores", "budget", "budgets", "scenario",
        "scenarios", "baseline", "rainfall", "observation", "observations", "nasa",
        "source", "sources", "reference", "references", "citation", "citations",
        "compare", "comparison", "synthetic", "provenance",
    }
    if not words & topics or not any(key in context for key in ("analysis", "scenario", "observations")):
        return None

    analysis = _record(context.get("analysis"))
    scenario = _record(context.get("scenario"))
    observations = _record(context.get("observations"))
    selected = context.get("candidate_id")
    baseline_id = analysis.get("analysis_id")
    scenario_baseline = scenario.get("baseline_analysis_id")
    if baseline_id is not None and scenario_baseline is not None and baseline_id != scenario_baseline:
        raise ValueError("Scenario baseline_analysis_id does not match analysis_id.")
    for key in ("farm_id", "observation_id"):
        left, right = analysis.get(key), observations.get(key)
        if left is not None and right is not None and left != right:
            raise ValueError(f"Analysis and observations have conflicting {key} values.")

    answers = []
    if "analysis" in context or words & {"rotation", "rotations", "rank", "ranking", "score", "baseline"}:
        answers.extend([
            f"Baseline analysis {_text(baseline_id)}. {_provenance(analysis)} "
            "Rotation scores and water budgets are supplied model outputs, not field measurements.",
            f"Catalog version: {_text(analysis.get('catalog_version'))}; "
            f"model version: {_text(analysis.get('model_version'))}.",
            _candidates(analysis, selected),
            _metadata(analysis),
        ])
    if "scenario" in context or words & {"scenario", "scenarios"}:
        parameters = _record(scenario.get("parameters"))
        linked = baseline_id is not None and baseline_id == scenario_baseline
        answers.extend([
            f"Hypothetical scenario {_text(scenario.get('scenario_id'))}; "
            f"baseline analysis ID: {_text(scenario_baseline)}. {_provenance(scenario)}",
            "Supplied rainfall change: " + _number(parameters.get("rainfall_change_pct"), "%")
            + ". This is a hypothetical input change, not a rainfall observation or forecast.",
            _candidates(scenario, selected),
            _differences(scenario, selected) if linked else
            "Baseline comparison is unknown: matching baseline IDs and baseline results are required.",
            _metadata(scenario),
        ])
    if "observations" in context or words & {"rainfall", "observation", "observations", "nasa"}:
        period = _record(observations.get("period"))
        summary = _record(observations.get("summary"))
        answers.extend([
            f"Observation record {_text(observations.get('observation_id'))}. {_provenance(observations)}",
            f"Observation period: {_text(period.get('start'))} to {_text(period.get('end'))}; "
            f"rainfall: {_number(summary.get('rainfall_mm'), ' mm')}; "
            f"mean temperature: {_number(summary.get('mean_temperature_c'), ' Celsius')}. "
            f"Retrieved at: {_text(observations.get('retrieved_at'))}.",
            _metadata(observations),
        ])
    if not answers:
        answers.append("Requested analytical information and source references are unknown (no results supplied).")
    return " ".join(answers)
