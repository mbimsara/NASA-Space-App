"""Structured, UI-compatible results without HTTP or provider dependencies."""

from dataclasses import dataclass, field

from .assistant_normalization import normalize_context


@dataclass
class ExplanationTrace:
    """Evidence selected during rendering, never recovered by parsing prose."""

    status: str = "answered"
    records: list = field(default_factory=list)

    def add(self, record):
        self.records.append({key: record[key] for key in
                             ("source_refs", "source_url", "assumptions", "limitations")
                             if key in record})

    def missing(self):
        if self.status == "answered":
            self.status = "insufficient_context"

    def unsupported(self):
        self.status = "unsupported_question"


def respond(context, question, language="en", **normalization_options):
    """Normalize teammate context and return Shehani's four required fields.

    Extra status/language/assumptions fields are internal additions, not a frozen
    HTTP contract. Invalid context raises TypeError/ValueError; unsupported
    languages retain explain()'s explicit ValueError rather than silently
    returning English under another language code.
    """
    from .assistant import _explain

    if language != "en":
        raise ValueError("Only English ('en') is supported in this milestone.")
    normalized = normalize_context(context, **normalization_options)
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

    return {
        "role": "assistant", "content": content,
        "source_ids": collect("source_refs"), "limitations": collect("limitations"),
        "status": trace.status, "language": "en", "assumptions": collect("assumptions"),
    }
