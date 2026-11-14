"""Assistant-domain errors. HTTP mapping belongs to Dulanjaya's backend."""


class AssistantRequestError(ValueError):
    code = "VALIDATION_ERROR"

    def __init__(self, message, fields=None):
        super().__init__(message)
        self.fields = dict(fields or {})

    def to_error_envelope(self):
        return {"error": {"code": self.code, "message": str(self), "fields": dict(self.fields)}}


class UnsupportedLanguageError(AssistantRequestError):
    code = "UNSUPPORTED_LANGUAGE"
    supported_languages = ("en",)

    def __init__(self, language):
        self.language = language
        super().__init__("Only English ('en') is supported in this milestone.",
                         {"language": "Supported assistant languages: en. Sinhala (si) and Tamil (ta) are not implemented yet."})


class AssistantContextError(AssistantRequestError):
    code = "CONTEXT_MISMATCH"


class InvalidCandidateError(AssistantRequestError):
    code = "INVALID_CANDIDATE"


def require_supported_language(language):
    if language != "en":
        raise UnsupportedLanguageError(language)
