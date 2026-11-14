"""Pure adapters for teammate outputs. No imports of teammate applications.

Accept mappings, stdlib dataclasses, or already-created Pydantic models via
model_dump(mode="json"). Dates and tuples become JSON-friendly copies. These
adapters validate the explanation boundary; they never run scientific models.
"""

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import math
from urllib.parse import urlsplit


KINDS = {"observed", "modeled", "synthetic", "mixed", "farmer_input"}


def _plain(value):
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    elif callable(getattr(value, "model_dump", None)):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("Context must contain JSON-compatible values, dates, dataclasses, or models.")


def _record(value, name):
    value = _plain(value)
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping or dataclass/model instance.")
    return value


def _list(value, name):
    if value is None:
        return []
    if not isinstance(value, list):
        raise TypeError(f"{name} must be a list or tuple.")
    return value


def _strings(value, name):
    items = _list(value, name)
    if any(not isinstance(item, str) or not item.strip() for item in items):
        raise ValueError(f"{name} must contain nonempty strings.")
    return items


def _number(value, name, nonnegative=False):
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                              or (nonnegative and value < 0)):
        raise ValueError(f"{name} must be a finite {'nonnegative ' if nonnegative else ''}number or null.")


def _alias(record, target, source):
    if source in record:
        if target in record and record[target] != record[source]:
            raise ValueError(f"Conflicting {target} and {source} values.")
        record[target] = _plain(record[source])


def _metadata(record, extra=None):
    for key, value in _record(extra or {}, "metadata").items():
        if key in record and record[key] is not None and record[key] != value:
            raise ValueError(f"Conflicting metadata: {key}.")
        record[key] = value
    if record.get("data_kind") is not None and record["data_kind"] not in KINDS:
        raise ValueError("Unsupported data_kind; score kind and hypothetical type are separate fields.")
    for key in ("source_refs", "assumptions", "limitations"):
        record[key] = _strings(record.get(key), key)
    for key in ("source_url", "model_version", "catalog_version", "score_kind"):
        if record.get(key) is not None and (not isinstance(record[key], str) or not record[key].strip()):
            raise ValueError(f"{key} must be a nonempty string or null.")
    if record.get("source_url") is not None:
        parsed = urlsplit(record["source_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source_url must be a supplied HTTP(S) URL.")
    for key in ("farm_id", "analysis_id", "observation_id", "scenario_id", "baseline_analysis_id"):
        if record.get(key) is not None and (not isinstance(record[key], str) or not record[key].strip()):
            raise ValueError(f"{key} must be a nonempty string or null.")
    if record.get("input_version") is not None:
        if type(record["input_version"]) is not int or record["input_version"] < 1:
            raise ValueError("input_version must be a positive integer.")
    return record


def _period(value, *, allow_label=False):
    if value is None:
        return {"start": None, "end": None}
    if allow_label and isinstance(value, str):
        if not value.strip():
            raise ValueError("Period labels must be nonempty strings.")
        return {"label": value, "start": None, "end": None}
    result = _record(value, "period")
    if result.get("label") is not None and (not isinstance(result["label"], str) or not result["label"].strip()):
        raise ValueError("Period labels must be nonempty strings.")
    for key in ("start", "end"):
        item = result.get(key)
        if item is not None and (not isinstance(item, str) or date.fromisoformat(item).isoformat() != item):
            raise ValueError("Period dates must use YYYY-MM-DD.")
    if result.get("start") and result.get("end") and result["start"] > result["end"]:
        raise ValueError("Period start must not follow end.")
    return result


def normalize_water_budget(value, *, period=None, metadata=None):
    """Preserve scalar/range/signed fields; never turn balance into deficit.

    The boundary supplies period/source metadata absent from engine dataclasses.
    WaterDemandRange alone is supported as a demand-only record: nominal_mm is
    retained for reference and is never substituted for a demand range.
    """
    record = _metadata(_record(value, "water budget"), metadata)
    for target, source in (("demand_mm", "crop_demand_mm"),
                           ("irrigation_supply_mm", "irrigation_mm"),
                           ("demand_low_mm", "low_mm"), ("demand_high_mm", "high_mm"),
                           ("demand_basis", "basis")):
        _alias(record, target, source)
    if period is not None:
        if record.get("period") is not None and _period(record["period"], allow_label=True) != _period(_plain(period), allow_label=True):
            raise ValueError("Conflicting budget periods.")
        record["period"] = _plain(period)
    record["period"] = _period(record.get("period"), allow_label=True)
    if record.get("season_index") is not None and (type(record["season_index"]) is not int or record["season_index"] < 1):
        raise ValueError("Budget season_index must be a positive integer or null.")
    if record.get("crop_id") is not None and (not isinstance(record["crop_id"], str) or not record["crop_id"].strip()):
        raise ValueError("Budget crop_id must be a nonempty string or null.")
    if record.get("unit", "mm") != "mm":
        raise ValueError("Water depths must be supplied in mm; no conversion is performed.")
    record["unit"] = "mm"
    for key, item in record.items():
        if key.endswith("_mm") or key.endswith("_percent"):
            _number(item, key, nonnegative=not key.startswith("balance"))
    for low, high in (("demand_low_mm", "demand_high_mm"),
                      ("balance_low_mm", "balance_high_mm"),
                      ("coverage_low_percent", "coverage_high_percent")):
        if record.get(low) is not None and record.get(high) is not None and record[low] > record[high]:
            raise ValueError(f"{low} must not exceed {high}.")
    if record.get("nominal_mm") is not None and record.get("demand_low_mm") is not None and record.get("demand_high_mm") is not None:
        if not record["demand_low_mm"] <= record["nominal_mm"] <= record["demand_high_mm"]:
            raise ValueError("Nominal demand must lie inside the supplied range.")
    return record


def _candidate(value, identifier=None):
    record = _metadata(_record(value, "candidate"))
    existing = record.get("candidate_id")
    if identifier is not None and existing is not None and identifier != existing:
        raise ValueError("Boundary candidate ID disagrees with the supplied candidate.")
    identifier = identifier if identifier is not None else existing
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("Stable candidate IDs must be supplied by the integration boundary.")
    record["candidate_id"] = identifier
    if "crop_ids" in record:
        crops = _strings(record["crop_ids"], "crop_ids")
        sequence = [{"season_index": index, "crop_id": crop} for index, crop in enumerate(crops, 1)]
        if "sequence" in record:
            existing_sequence = _list(record["sequence"], "sequence")
            if [{"season_index": step.get("season_index"), "crop_id": step.get("crop_id")}
                    for step in existing_sequence if isinstance(step, dict)] != sequence:
                raise ValueError("crop_ids and sequence disagree.")
        else:
            record["sequence"] = sequence
    if "sequence" in record:
        steps = _list(record["sequence"], "sequence")
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict) or type(step.get("season_index")) is not int or step["season_index"] != index or not isinstance(step.get("crop_id"), str) or not step["crop_id"].strip():
                raise ValueError("Sequence must preserve ordered, one-based season indices and crop IDs.")
    if "reasons" in record:
        record["reasons"] = _strings(record["reasons"], "candidate reasons")
    for key in ("score", "rank"):
        _number(record.get(key), key)
    if record.get("rank") is not None and (type(record["rank"]) is not int or record["rank"] < 1):
        raise ValueError("Supplied ranks must be positive integers.")
    # Missing scores/ranks deliberately remain absent, not zero or array indices.
    if "score_components" in record:
        components = record["score_components"] if record["score_components"] is not None else {}
        if isinstance(components, list):
            converted = {}
            for component in components:
                component = _record(component, "score component")
                name = component.get("name")
                if not isinstance(name, str) or not name.strip() or name in converted:
                    raise ValueError("Score components need unique supplied names.")
                converted[name] = component
            components = converted
        components = _record(components, "score_components")
        for component in components.values():
            component = _record(component, "score component")
            _number(component.get("value"), "component value")
            for key in ("weight", "requested_weight", "effective_weight"):
                _number(component.get(key), f"component {key}", nonnegative=True)
            if component.get("direction") not in (None, "higher_is_better", "lower_is_better"):
                raise ValueError("Unknown score direction.")
        record["score_components"] = components
    checks = []
    for check in _list(record.get("constraint_checks"), "constraint_checks"):
        if isinstance(check, str):
            check = {"rule": check, "passed": None, "note": None}
        check = _record(check, "constraint check")
        if not isinstance(check.get("rule"), str) or not check["rule"].strip():
            raise ValueError("Constraint checks require a supplied rule description.")
        if check.get("passed") is not None and type(check["passed"]) is not bool:
            raise ValueError("Constraint passed must be boolean or null.")
        if check.get("note") is not None and not isinstance(check["note"], str):
            raise ValueError("Constraint note must be text or null.")
        check = _metadata(check)
        checks.append(check)
    record["constraint_checks"] = checks
    if record.get("water_budget") is not None:
        record["water_budget"] = normalize_water_budget(record["water_budget"])
    if record.get("water_budget_range") is not None:
        supplied_ranges = record["water_budget_range"]
        ranges = supplied_ranges if isinstance(supplied_ranges, list) else [supplied_ranges]
        ranges = [normalize_water_budget(budget) for budget in ranges]
        if "water_budgets" in record:
            existing_budgets = [normalize_water_budget(budget) for budget in
                                _list(record["water_budgets"], "water_budgets")]
            if existing_budgets != ranges:
                raise ValueError("Conflicting water_budgets and water_budget_range values.")
        record["water_budgets"] = ranges
        record["water_budget_range"] = ranges if isinstance(supplied_ranges, list) else ranges[0]
    if "water_budgets" in record:
        budgets = []
        for budget in _list(record["water_budgets"], "water_budgets"):
            budget = normalize_water_budget(budget)
            if budget.get("season_index") is not None:
                step = next((step for step in record.get("sequence", [])
                             if step["season_index"] == budget["season_index"]), None)
                if step is None or (budget.get("crop_id") is not None and step["crop_id"] != budget["crop_id"]):
                    raise ValueError("Water budget does not match its supplied sequence step.")
            elif budget.get("crop_id") is not None and record.get("sequence") and not any(
                    step["crop_id"] == budget["crop_id"] for step in record["sequence"]):
                raise ValueError("Water budget crop_id is not present in its candidate sequence.")
            budgets.append(budget)
        record["water_budgets"] = budgets
    return record


def _difference(value, identifier=None):
    """Normalize supplied deltas only; never subtract scores or infer ranks."""
    record = _metadata(_record(value, "candidate difference"))
    if identifier is not None:
        if record.get("candidate_id") is not None and record["candidate_id"] != identifier:
            raise ValueError("Difference candidate_id disagrees with its mapping key.")
        record["candidate_id"] = identifier
    if not isinstance(record.get("candidate_id"), str) or not record["candidate_id"].strip():
        raise ValueError("Differences require supplied candidate IDs.")
    _alias(record, "score_delta", "score_change")
    _number(record.get("score_delta"), "score difference")
    for key in ("rank_baseline", "rank_scenario"):
        if record.get(key) is not None and (type(record[key]) is not int or record[key] < 1):
            raise ValueError("Supplied difference ranks must be positive integers or null.")
    return record


def _normalize_differences(record, candidate_ids=None):
    """Keep legacy lists and the frontend's candidate-keyed mapping compatible."""
    rows = None
    if record.get("differences") is not None:
        rows = [_difference(row) for row in _list(record["differences"], "differences")]
    if record.get("baseline_differences") is not None:
        supplied = _record(record["baseline_differences"], "baseline_differences")
        if any(not isinstance(identifier, str) or not identifier.strip() for identifier in supplied):
            raise ValueError("Difference mapping keys must be supplied nonempty candidate IDs.")
        converted = [_difference(row, identifier) for identifier, row in supplied.items()]
        if rows is not None:
            def comparable(items):
                if len({row["candidate_id"].casefold() for row in items}) != len(items):
                    raise ValueError("Difference candidate IDs must be unique, including case variants.")
                return {row["candidate_id"]: {key: value for key, value in row.items()
                                               if key != "score_change"} for row in items}
            if comparable(rows) != comparable(converted):
                raise ValueError("Conflicting differences and baseline_differences values.")
        rows = converted
    if rows is not None:
        identifiers = [row["candidate_id"] for row in rows]
        if len({identifier.casefold() for identifier in identifiers}) != len(identifiers):
            raise ValueError("Difference candidate IDs must be unique, including case variants.")
        # Preserve legacy-list selection/error semantics. New candidate-keyed
        # records must agree with the supplied scenario candidate identities.
        if record.get("baseline_differences") is not None and candidate_ids is not None and set(identifiers) - set(candidate_ids):
            raise ValueError("Differences reference an unknown candidate ID.")
        record["differences"] = rows


def normalize_rotation(result, *, candidate_ids=None, metadata=None, water_budgets=None):
    """Serialize CandidateGenerationResult or a JSON analysis without scoring.

    candidate_ids is an explicit ordered list supplied by the caller, with one
    stable ID per generated candidate. Budgets are explicitly bound by those IDs.
    Use a list of per-crop/season budgets rather than aggregating crop cycles.
    """
    record = _metadata(_record(result, "analysis"), metadata)
    if "reasons" in record:
        record["reasons"] = _strings(record["reasons"], "analysis reasons")
    if record.get("observation_rainfall") is not None:
        comparison = _record(record["observation_rainfall"], "observation rainfall")
        _period({"start": comparison.get("period_start"), "end": comparison.get("period_end")})
        for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm"):
            _number(comparison.get(key), key, nonnegative=key != "difference_mm")
        coverage = _coverage({key: comparison[key] for key in ("expected_days", "valid_days") if key in comparison})
        if coverage.get("expected_days") is not None and coverage.get("valid_days") is not None:
            if coverage["valid_days"] < coverage["expected_days"] and any(
                comparison.get(key) is not None for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm")
            ):
                raise ValueError("Incomplete observation-period scenario totals must remain null.")
        record["observation_rainfall"] = comparison
    supplied = record.get("candidates")
    if supplied is None:
        if candidate_ids is not None or water_budgets:
            raise ValueError("Cannot bind IDs or budgets to unavailable candidate results.")
        _normalize_differences(record)
        return record
    rows = _list(supplied, "candidates")
    ids = _plain(candidate_ids)
    if ids is not None and len(_strings(ids, "candidate_ids")) != len(rows):
        raise ValueError("Supply one stable ID for every candidate.")
    bindings = _record(water_budgets or {}, "water_budgets")
    candidates = []
    for index, row in enumerate(rows):
        candidate = _candidate(row, ids[index] if ids is not None else None)
        identifier = candidate["candidate_id"]
        if identifier in bindings:
            if "water_budget" in candidate or "water_budgets" in candidate:
                raise ValueError("Water budgets were supplied twice for a candidate.")
            budgets = bindings[identifier]
            candidate["water_budgets"] = budgets if isinstance(budgets, list) else [budgets]
            candidate = _candidate(candidate)
        candidates.append(candidate)
    actual_ids = [candidate["candidate_id"] for candidate in candidates]
    if len(set(identifier.casefold() for identifier in actual_ids)) != len(actual_ids):
        raise ValueError("Candidate IDs must be unique, including case variants.")
    if set(bindings) - set(actual_ids):
        raise ValueError("Water budgets reference an unknown candidate ID.")
    record["candidates"] = candidates
    _normalize_differences(record, actual_ids)
    return record


def _coverage(value):
    coverage = _record(value or {}, "coverage")
    expected = coverage.get("expected_days")
    if expected is not None and (type(expected) is not int or expected <= 0):
        raise ValueError("Coverage expected_days must be a positive integer.")
    for key, count in coverage.items():
        if count is not None:
            if type(count) is not int or count < 0 or (expected is not None and count > expected):
                raise ValueError("Coverage must contain nonnegative counts no greater than expected_days.")
    return coverage


def normalize_observation(value):
    """Accept Matheesha's normalizer/envelope or Dulanjaya's HTTP model/dict."""
    record = _record(value, "observations")
    _alias(record, "source_refs", "sources")
    record = _metadata(record)
    summary = _record(record.get("summary", {}), "observation summary")
    # A full total is authoritative, including null. Never use the partial sum.
    _alias(summary, "rainfall_mm", "rainfall_total_mm")
    for key in ("rainfall_mm", "rainfall_total_mm", "rainfall_available_days_mm", "mean_temperature_c"):
        _number(summary.get(key), key, nonnegative=key != "mean_temperature_c")
    period = record.get("period")
    if period is None:
        period = {"start": summary.get("start"), "end": summary.get("end")}
    record["period"] = _period(period)
    for key in ("start", "end"):
        if summary.get(key) is not None and summary[key] != record["period"].get(key):
            raise ValueError("Observation summary and period disagree.")
    coverage = record.get("coverage")
    if coverage is None:
        coverage = {key: summary[key] for key in ("expected_days", "temperature_valid_days", "precipitation_valid_days") if key in summary}
    coverage = _coverage(coverage)
    for key, count in coverage.items():
        if key in summary and summary[key] != count:
            raise ValueError("Observation coverage and summary disagree.")
    expected = coverage.get("expected_days")
    if expected is not None and all(record["period"].get(key) for key in ("start", "end")):
        start, end = (date.fromisoformat(record["period"][key]) for key in ("start", "end"))
        if expected != (end - start).days + 1:
            raise ValueError("Observation period and expected_days disagree.")
    valid = coverage.get("precipitation_valid_days")
    if expected is not None and valid is not None and valid < expected and summary.get("rainfall_mm") is not None:
        raise ValueError("Incomplete rainfall coverage cannot have a complete-period rainfall total.")
    units = _record(record.get("units", {}), "observation units")
    for field in ("rainfall_mm", "rainfall_total_mm", "rainfall_available_days_mm"):
        if field in units and units[field] != "mm":
            raise ValueError("Observation rainfall totals must be in mm.")
    if units.get("mean_temperature_c", "C") not in ("C", "Celsius", "°C"):
        raise ValueError("Mean temperature must be Celsius.")
    record.update(summary=summary, coverage=coverage)
    return record


def normalize_rainfall_scenario(value, *, observation=None, metadata=None):
    """A rainfall-only what-if, never a rotation-analysis scenario."""
    record = _metadata(_record(value, "rainfall scenario"), metadata)
    if record.get("kind") != "hypothetical_rainfall_scenario":
        raise ValueError("Expected Matheesha's hypothetical_rainfall_scenario kind.")
    change = record.get("rainfall_change_pct")
    _number(change, "rainfall_change_pct")
    if change is not None and not -100 <= change <= 100:
        raise ValueError("rainfall_change_pct must be between -100 and 100.")
    summary = _record(record.get("summary", {}), "scenario summary")
    for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm"):
        _number(summary.get(key), key, nonnegative=key != "difference_mm")
    _coverage({key: summary[key] for key in ("expected_days", "valid_days") if key in summary})
    if summary.get("valid_days") is not None and summary.get("expected_days") is not None and summary["valid_days"] < summary["expected_days"]:
        if any(summary.get(key) is not None for key in ("baseline_rainfall_mm", "scenario_rainfall_mm", "difference_mm")):
            raise ValueError("Incomplete rainfall scenario totals must remain null.")
    if observation is not None:
        observed = normalize_observation(observation)
        for key in ("data_kind", "period", "source_refs", "limitations", "observation_id", "farm_id", "input_version"):
            if key not in record or record[key] in (None, []):
                record[key] = _plain(observed.get(key))
        if record.get("data_kind") != observed.get("data_kind"):
            raise ValueError("Rainfall scenario and baseline provenance disagree.")
        for key in ("farm_id", "observation_id", "input_version"):
            if record.get(key) is not None and observed.get(key) is not None and record[key] != observed[key]:
                raise ValueError(f"Rainfall scenario and observation {key} disagree.")
        if record.get("baseline_observation_id") is not None and record["baseline_observation_id"] != observed.get("observation_id"):
            raise ValueError("Rainfall scenario references a different baseline observation.")
        if record.get("period") != observed["period"]:
            raise ValueError("Rainfall scenario and baseline periods disagree.")
        if summary.get("baseline_rainfall_mm") != observed["summary"].get("rainfall_mm"):
            raise ValueError("Scenario baseline rainfall does not match the linked observation.")
        record["baseline_observation_id"] = observed.get("observation_id")
    record["period"] = _period(record.get("period"))
    record["summary"] = summary
    record["parameters"] = {"rainfall_change_pct": change}
    return record


def normalize_context(context, *, candidate_ids=None, analysis_metadata=None, water_budgets=None, scenario_metadata=None):
    """Normalize explicit context or Matheesha's climate_bundle; no ID allocation.

    Analysis/scenario metadata comes from the integration boundary. Unknown
    provenance and versions remain unknown. Normalization never marks source
    data synthetic unless the caller/producer actually labels it synthetic.
    """
    result = _record(context, "context")
    if "observation" in result:
        _alias(result, "observations", "observation")
        result.pop("observation")
    if "rainfall_scenario" in result:
        _alias(result, "scenario", "rainfall_scenario")
        result.pop("rainfall_scenario")
    if "profile" in result:
        profile = _metadata(_record(result["profile"], "profile"))
        for key in ("area_ha", "irrigation_supply_mm_per_season"):
            _number(profile.get(key), key, nonnegative=True)
        result["profile"] = profile
    if result.get("analysis") is not None:
        result["analysis"] = normalize_rotation(result["analysis"], candidate_ids=candidate_ids,
                                                metadata=analysis_metadata, water_budgets=water_budgets)
    elif candidate_ids is not None or analysis_metadata is not None or water_budgets is not None:
        raise ValueError("Analysis boundary options require an analysis result.")
    if result.get("observations") is not None:
        result["observations"] = normalize_observation(result["observations"])
    if result.get("scenario") is not None:
        scenario = _record(result["scenario"], "scenario")
        if scenario.get("kind") == "hypothetical_rainfall_scenario":
            result["scenario"] = normalize_rainfall_scenario(scenario, observation=result.get("observations"), metadata=scenario_metadata)
        else:
            result["scenario"] = normalize_rotation(scenario, metadata=scenario_metadata)
    elif scenario_metadata is not None:
        raise ValueError("Scenario metadata requires a supplied scenario.")
    records = [result.get(key) for key in ("analysis", "observations", "scenario")]
    if "profile" in result:
        records.append({"farm_id": result.get("id"), "input_version": result.get("input_version")})
    for key in ("farm_id", "input_version", "observation_id"):
        values = [record[key] for record in records if record and record.get(key) is not None]
        if values and any(value != values[0] for value in values[1:]):
            raise ValueError(f"Conflicting context {key} values.")
    analysis, scenario = result.get("analysis") or {}, result.get("scenario") or {}
    if analysis.get("analysis_id") is not None and scenario.get("baseline_analysis_id") is not None:
        if analysis["analysis_id"] != scenario["baseline_analysis_id"]:
            raise ValueError("Scenario does not belong to the supplied baseline analysis.")
    if result.get("candidate_id") is not None:
        if not any(item["candidate_id"] == result["candidate_id"] for record in (analysis, scenario) for item in record.get("candidates", []) or []):
            raise ValueError("Selected candidate ID is not present in the supplied results.")
    return result
