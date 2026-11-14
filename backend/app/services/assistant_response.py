"""Structured, UI-compatible results without HTTP or provider dependencies."""

from dataclasses import dataclass, field
from collections.abc import Mapping

from .assistant_normalization import normalize_context
from .assistant_errors import (
    AssistantContextError, AssistantRequestError, InvalidCandidateError,
    require_supported_language,
)


@dataclass
class ExplanationTrace:
    """Evidence selected during rendering, never recovered by parsing prose."""

    status: str = "answered"
    records: list = field(default_factory=list)
    diagnostics: list = field(default_factory=list)

    def add(self, record):
        self.records.append({key: record[key] for key in
                             ("source_refs", "source_url", "assumptions", "limitations")
                             if key in record})

    def limitation(self, reason):
        if reason not in self.diagnostics:
            self.diagnostics.append(reason)

    def missing(self, reason="Some requested information is unknown or was not supplied."):
        self.limitation(reason)
        if self.status == "answered":
            self.status = "insufficient_context"

    def unsupported(self):
        self.status = "unsupported_question"


def respond(context, question, language="en", **normalization_options):
    """Normalize teammate context and return Shehani's four required fields.

    The four required fields match Shehani's confirmed contract. Extra
    status/language/assumptions fields are optional. For the confirmed request
    object and resolved-record ID checks, use respond_to_request(). Invalid
    context raises TypeError/ValueError. UnsupportedLanguageError is a ValueError
    subclass, preserving existing error handling without relabeling English.
    """
    require_supported_language(language)
    normalized = normalize_context(context, **normalization_options)
    return _respond_normalized(normalized, question, language)


def _respond_normalized(normalized, question, language):
    from .assistant import _explain

    trace = ExplanationTrace()
    content = _explain(normalized, question, language, trace=trace)

    def collect(key):
        entries = []
        for record in trace.records:
            values = record.get(key) or []
            if key == "source_refs" and record.get("source_url"):
                # A producer's actual URL is usable as a reference; no registry
                # ID or citation is generated for it.
                values = [*values, record["source_url"]]
            for value in values:
                if value not in entries:
                    entries.append(value)
        return entries

    limitations = collect("limitations")
    for reason in trace.diagnostics:
        if reason not in limitations:
            limitations.append(reason)
    return {
        "role": "assistant", "content": content,
        "source_ids": collect("source_refs"), "limitations": limitations,
        "status": trace.status, "language": "en", "assumptions": collect("assumptions"),
    }


def _request_fields(request):
    """Validate exactly Shehani's agreed request fields, without an HTTP model."""
    if not isinstance(request, Mapping):
        raise AssistantRequestError("Assistant request must be an object.")
    required = {"farm_id", "analysis_id", "language", "message"}
    optional = {"scenario_id", "candidate_id"}
    errors = {key: "Field is required." for key in required - request.keys()}
    errors.update({str(key): "Unexpected request field." for key in request.keys() - required - optional})
    for key in required:
        if key in request and (not isinstance(request[key], str) or not request[key].strip()):
            errors[key] = "Must be a nonempty string."
    for key in optional:
        if request.get(key) is not None and (not isinstance(request[key], str) or not request[key].strip()):
            errors[key] = "Must be a nonempty string or omitted/null."
    if isinstance(request.get("message"), str) and len(request["message"]) > 2000:
        errors["message"] = "Must be at most 2000 characters."
    if errors:
        raise AssistantRequestError("Invalid assistant request.", errors)
    require_supported_language(request["language"])
    return dict(request)


def respond_to_request(request, resolved_context, **normalization_options):
    """Answer a confirmed frontend request using caller-resolved records only.

    No lookup, authorization, ID allocation, or request-supplied scientific facts
    occur here. Dulanjaya resolves and authorizes snapshots before calling this
    function. Missing result records give a controlled limited answer; conflicting
    supplied identities raise a typed context error. Explicit unknown candidates
    in otherwise available results raise InvalidCandidateError.
    """
    body = _request_fields(request)
    if not isinstance(resolved_context, Mapping):
        raise AssistantRequestError("Resolved assistant context must be an object.")
    scoped = dict(resolved_context)
    # An omitted selection means all candidates, not an old server/UI selection.
    scoped.pop("candidate_id", None)
    if body.get("scenario_id") is None:
        scoped.pop("scenario", None)
        scoped.pop("rainfall_scenario", None)
        if normalization_options.get("scenario_metadata") is not None:
            raise AssistantContextError("Scenario metadata was supplied without a requested scenario.")
    normalized = normalize_context(scoped, **normalization_options)
    records = [normalized.get(key) or {} for key in ("analysis", "scenario", "observations")]
    farm_ids = [record["farm_id"] for record in records if record.get("farm_id") is not None]
    if normalized.get("profile") is not None and normalized.get("id") is not None:
        farm_ids.append(normalized["id"])
    if normalized.get("farm_id") is not None:
        farm_ids.append(normalized["farm_id"])
    if not farm_ids or any(identifier != body["farm_id"] for identifier in farm_ids):
        raise AssistantContextError("Resolved records do not identify the requested farm.", {"farm_id": "Context does not match this farm."})

    analysis, scenario = records[:2]
    missing = []
    if analysis:
        if analysis.get("farm_id") != body["farm_id"]:
            raise AssistantContextError("Resolved analysis must identify the requested farm.", {"farm_id": "Analysis farm identity is missing or mismatched."})
        if analysis.get("analysis_id") != body["analysis_id"]:
            raise AssistantContextError("Resolved analysis does not match analysis_id.", {"analysis_id": "A matching persisted analysis ID is required."})
    else:
        missing.append("Requested analysis results were not supplied; rotation scores, rankings and recommendations cannot be inferred.")
        # Preserve the distinction between unavailable analytical context and an
        # unsupported topic. The original explain() behavior is unchanged.
        normalized.setdefault("analysis", None)
    if body.get("scenario_id") is not None:
        if not scenario:
            missing.append("Requested scenario results were not supplied; scenario effects have not been calculated.")
        else:
            if scenario.get("scenario_id") != body["scenario_id"]:
                raise AssistantContextError("Resolved scenario does not match scenario_id.", {"scenario_id": "A matching persisted scenario ID is required."})
            # Rainfall-only scenarios can link through the exact observation
            # snapshot; rotation scenarios must link through the analysis ID.
            linked_analysis = scenario.get("baseline_analysis_id") == body["analysis_id"]
            linked_observation = (scenario.get("kind") == "hypothetical_rainfall_scenario" and
                                  analysis.get("observation_id") is not None and
                                  scenario.get("baseline_observation_id") == analysis["observation_id"])
            if analysis and not (linked_analysis or linked_observation):
                raise AssistantContextError("Scenario is not linked to the requested analysis.", {"scenario_id": "Baseline context does not match."})
    selected = body.get("candidate_id")
    if selected is not None:
        if analysis.get("candidates") is None:
            missing.append("The requested candidate cannot be verified because analysis candidates are unavailable.")
        else:
            candidates = analysis["candidates"]
            if not any(candidate["candidate_id"] == selected for candidate in candidates):
                raise InvalidCandidateError("Candidate is not present in the selected analysis.", {"candidate_id": "Unknown candidate for this analysis."})
            if scenario and scenario.get("kind") != "hypothetical_rainfall_scenario" and scenario.get("candidates") is not None:
                if not any(candidate["candidate_id"] == selected for candidate in scenario["candidates"]):
                    raise InvalidCandidateError("Candidate is not present in the selected scenario.", {"candidate_id": "Unknown candidate for this scenario."})
            normalized["candidate_id"] = selected

    response = _respond_normalized(normalized, body["message"], body["language"])
    for reason in missing:
        if reason not in response["limitations"]:
            response["limitations"].append(reason)
    if missing and response["status"] != "unsupported_question":
        response["status"] = "insufficient_context"
    response["context"] = {
        "farm_id": body["farm_id"], "analysis_id": analysis.get("analysis_id"),
        "scenario_id": scenario.get("scenario_id"), "candidate_id": normalized.get("candidate_id"),
    }
    return response
