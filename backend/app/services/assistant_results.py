"""Format supplied analytical results without scoring, forecasting, or lookup."""

import math
import re
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


def _water(budget, delta=False, deficit_only=False):
    budget = _record(budget)
    prefix = "Supplied water-budget differences (scenario minus baseline)" if delta else "Water budget"
    fields = (("deficit_mm", "deficit"),) if deficit_only else WATER_FIELDS
    values = "; ".join(
        f"{label}: {_number(budget.get(key), ' mm')}" for key, label in fields
    )
    if delta:
        return f"{prefix}: {values}."
    period = _record(budget.get("period"))
    return (
        f"{prefix} period: {_text(period.get('start'))} to {_text(period.get('end'))}; {values}. "
        f"Effective rainfall assumption: {_text(budget.get('effective_rainfall_assumption'))}."
    )


def _candidates(record, selected, views=None, deficit_only=False):
    """Render only requested candidate fields; the default is the full view."""
    if views is None:
        views = {"rank", "details", "water"}
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
        lines = [f"Candidate {_text(candidate.get('candidate_id'))}:"]
        if views & {"rank", "score"}:
            lines[0] += (
                f" supplied rank {_number(candidate.get('rank'))}; "
                f"supplied score {_number(candidate.get('score'))} (scale not inferred)."
            )
            if "rank" in views:
                lines.append(f"Supplied reasons: {_notes(candidate.get('reasons'))}.")
        if "details" in views:
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
            lines.extend([
                "Supplied crop sequence: " + ("; ".join(sequence) or "unknown") + ".",
                "Score components: " + ("; ".join(components) or "unknown") + ".",
            ])
        elif "rank" in views:
            # Incomplete contract records remain explainable. Report absent
            # required sections as limitations without dumping their contents.
            missing = []
            if "sequence" not in candidate:
                missing.append("Supplied crop sequence: unknown.")
            if "score_components" not in candidate:
                missing.append("Score components: unknown.")
            if "water_budget" not in candidate and "water" not in views:
                missing.append(_water(None))
            if missing:
                lines.append("Missing candidate information: " + " ".join(missing))
        if "water" in views:
            lines.append(_water(candidate.get("water_budget"), deficit_only=deficit_only))
        answers.append(" ".join(lines))
    if "rank" in views:
        answers.append("Ranks are not inferred from list order or scores; no new crop recommendation is generated.")
    return "\n".join(answers)


def _differences(scenario, selected, include_scores=True, include_water=True, deficit_only=False):
    differences = scenario.get("differences")
    if differences is None:
        return "Baseline differences are unknown; this service does not calculate them."
    records = [_record(item) for item in _items(differences)]
    if selected is not None:
        records = [item for item in records if item.get("candidate_id") == selected]
    if not records:
        return "Baseline differences are unknown (none supplied for the selected results)."
    answers = []
    for item in records:
        line = f"Candidate {_text(item.get('candidate_id'))}: "
        if include_scores:
            line += ("supplied score difference (scenario minus baseline): "
                     f"{_number(item.get('score_delta'))}. ")
        if include_water:
            line += _water(item.get("water_budget"), delta=True, deficit_only=deficit_only)
        answers.append(line)
    return "\n".join(answers)


def _question_views(words):
    """Explicit topic rules; loaded records alone never select an answer view."""
    full = {"full", "analysis"} <= words
    water = bool(words & {"budget", "budgets", "demand", "demands", "deficit", "deficits"})
    water |= "water" in words and bool(words & {
        "need", "needs", "needed", "require", "required", "requirement", "requirements",
        "use", "usage", "compare", "comparison",
    })
    water |= {"effective", "rainfall"} <= words
    water |= "irrigation" in words and bool(words & {
        "candidate", "candidates", "rotation", "rotations", "baseline", "scenario", "analysis",
    })
    rank = bool(words & {"rank", "ranks", "ranked", "ranking", "rankings", "score", "scores"})
    details = bool(words & {"sequence", "sequences", "components"})
    details |= bool(words & {"candidate", "candidates"}) and not water
    if words & {"rotation", "rotations"} and not (water or rank):
        details = True
    scenario = bool(words & {"scenario", "scenarios", "hypothetical"})
    scenario |= "rainfall" in words and bool(words & {
        "if", "decrease", "decreases", "decreased", "reduce", "reduces", "reduced",
        "reduction", "less", "increase", "increases", "increased", "change", "changes",
        "drop", "drops", "falls", "drier",
    })
    comparison = bool(words & {"compare", "comparison", "difference", "differences", "versus", "vs"})
    if comparison and (water or rank) and "baseline" not in words:
        scenario = True
    observations = bool(words & {"observation", "observations", "nasa"})
    if "rainfall" in words and not (scenario or water):
        observations = True
    sources = bool(words & {"source", "sources", "reference", "references", "citation",
                            "citations", "provenance", "synthetic"})
    # A scenario-only question includes the supplied rank/score change as well
    # as its water impacts. A water-specific question excludes ranking details.
    views = set()
    if water or (scenario and not rank):
        views.add("water")
    if rank or details:
        views.add("rank")
    elif scenario and not water:
        views.add("score")
    if details:
        views.add("details")
    deficit_only = bool(words & {"deficit", "deficits"}) and not bool(
        words & {"budget", "budgets", "demand", "demands", "rainfall", "irrigation"}
    )
    return full, views, scenario, observations, sources, deficit_only


def _question_candidate(analysis, scenario, question, selected):
    """Resolve exact IDs or unique ID-suffix aliases, never array positions."""
    identifiers = {
        item.get("candidate_id")
        for record in (analysis, scenario)
        for item in map(_record, _items(record.get("candidates")))
        if isinstance(item.get("candidate_id"), str)
    }
    known = {identifier.casefold(): identifier for identifier in identifiers}
    text = question.casefold()
    requested = set(re.findall(r"\bcandidate-[\w-]+\b", text))
    generic = {"all", "and", "or", "selected", "selection", "rank", "ranks", "ranking",
               "rankings", "score", "scores", "water", "budget", "budgets", "details",
               "sequence", "sequences", "information", "results", "baseline", "scenario",
               "reasons", "with", "in", "is", "has", "does", "need", "needs", "missing", "data"}
    requested.update(token for token in re.findall(r"\bcandidate(?:\s+id)?\s+([\w-]+)", text)
                     if token not in generic)
    for identifier in known:
        if re.search(r"(?<![\w-])" + re.escape(identifier) + r"(?![\w-])", text):
            requested.add(identifier)
    resolved = set()
    for token in requested:
        matches = [identifier for identifier in identifiers
                   if identifier.casefold() == token or
                   (len(token) == 1 and identifier.rsplit("-", 1)[-1].casefold() == token)]
        if len(matches) != 1:
            return selected, True, f"Candidate {token} is unknown or ambiguous; no result was selected."
        resolved.add(matches[0])
    if len(resolved) > 1:
        return selected, True, "Multiple explicit candidate selections are unsupported; select one ID or use all candidates."
    if resolved:
        requested_id = resolved.pop()
        if selected is not None and selected != requested_id:
            return selected, True, "Conflicting candidate selections are unavailable; reset the selection before changing candidates."
        return requested_id, True, None
    return selected, False, None


def explain_results(context, words, question=""):
    """Return analytical text, or None to leave the original farm handler active."""
    if words & {"recommend", "recommendation", "recommendations", "should", "best",
                "predict", "prediction", "yield", "fertilizer", "forecast"}:
        return None
    full, views, scenario_view, observation_view, sources, deficit_only = _question_views(words)
    if not (full or views or scenario_view or observation_view or sources):
        return None
    if not any(key in context for key in ("analysis", "scenario", "observations")):
        return None
    if full:
        views = {"rank", "details", "water"}
        scenario_view = "scenario" in context
        observation_view = "observations" in context
        deficit_only = False

    analysis = _record(context.get("analysis"))
    scenario = _record(context.get("scenario"))
    observations = _record(context.get("observations"))
    selected = context.get("candidate_id")
    selected, explicit_candidate, selection_error = _question_candidate(analysis, scenario, question, selected)
    contradictory = (re.search(r"\bonly\s+baseline\b", question.casefold()) and
                     re.search(r"\bonly\s+(?:hypothetical\s+)?scenario\b", question.casefold()))
    if selection_error or contradictory:
        return (_provenance(analysis) + " " + (selection_error or
                "Contradictory baseline-only and scenario-only requests are unsupported."))
    if explicit_candidate and not full and not words & {"sequence", "sequences", "components"}:
        views.discard("details")
    baseline_id = analysis.get("analysis_id")
    scenario_baseline = scenario.get("baseline_analysis_id")
    if baseline_id is not None and scenario_baseline is not None and baseline_id != scenario_baseline:
        raise ValueError("Scenario baseline_analysis_id does not match analysis_id.")
    for key in ("farm_id", "observation_id"):
        left, right = analysis.get(key), observations.get(key)
        if left is not None and right is not None and left != right:
            raise ValueError(f"Analysis and observations have conflicting {key} values.")

    answers = []
    sources_only = sources and not (full or views or scenario_view or observation_view)
    if views or (sources_only and "analysis" in context):
        answers.append(f"Baseline analysis {_text(baseline_id)}. {_provenance(analysis)}")
        if views:
            answers.append("Supplied model outputs, not field measurements.")
            if "rank" in views:
                answers.append(
                    f"Catalog version: {_text(analysis.get('catalog_version'))}; "
                    f"model version: {_text(analysis.get('model_version'))}."
                )
            answers.append(_candidates(analysis, selected, views, deficit_only))
        answers.append(_metadata(analysis))
    if scenario_view or (sources_only and "scenario" in context):
        parameters = _record(scenario.get("parameters"))
        linked = baseline_id is not None and baseline_id == scenario_baseline
        answers.append(
            f"Hypothetical scenario {_text(scenario.get('scenario_id'))}; "
            f"baseline analysis ID: {_text(scenario_baseline)}. {_provenance(scenario)}"
        )
        if scenario_view:
            answers.extend([
                "Supplied rainfall change: " + _number(parameters.get("rainfall_change_pct"), "%")
                + ". This is a hypothetical input change, not a rainfall observation or forecast. "
                "Only supplied results are shown; no new scenario is calculated.",
                _candidates(scenario, selected, views, deficit_only),
                _differences(scenario, selected, include_scores=bool(views & {"rank", "score"}),
                             include_water="water" in views, deficit_only=deficit_only) if linked else
                "Baseline comparison is unknown: matching baseline IDs and baseline results are required.",
            ])
        answers.append(_metadata(scenario))
    if observation_view or (sources_only and "observations" in context):
        period = _record(observations.get("period"))
        summary = _record(observations.get("summary"))
        answers.append(
            f"Observation record {_text(observations.get('observation_id'))}. {_provenance(observations)}"
        )
        if observation_view:
            answers.append(
                f"Observation period: {_text(period.get('start'))} to {_text(period.get('end'))}; "
                f"rainfall: {_number(summary.get('rainfall_mm'), ' mm')}; "
                f"mean temperature: {_number(summary.get('mean_temperature_c'), ' Celsius')}. "
                f"Retrieved at: {_text(observations.get('retrieved_at'))}."
            )
        answers.append(_metadata(observations))
    if not answers:
        answers.append("Requested analytical information and source references are unknown (no results supplied).")
    return "\n".join(answers)
