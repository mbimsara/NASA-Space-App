"""Optional LLM wording layer over the deterministic, cited assistant result."""

import json

from app.config import settings


INSTRUCTIONS = """You explain a farm decision using only the supplied grounded draft.
Do not add numbers, crops, causes, forecasts, recommendations, or sources that are not in it.
Preserve uncertainty and every material limitation. If the draft lacks the answer, say so.
Return only the concise answer text, with no markdown heading and no source list."""


def enhance(body, grounded, client_factory=None):
    if settings.assistant_provider != "openai":
        return grounded
    try:
        if client_factory is None:
            from openai import OpenAI
            client_factory = OpenAI
        client = client_factory()
        supplied = {"question": body["message"], "grounded_draft": grounded["content"],
                    "source_ids": grounded["source_ids"], "assumptions": grounded.get("assumptions", []),
                    "limitations": grounded["limitations"]}
        result = client.responses.create(model=settings.openai_model, instructions=INSTRUCTIONS,
                                         input=json.dumps(supplied, ensure_ascii=False),
                                         max_output_tokens=500, store=False)
        text = result.output_text.strip()
        if not text:
            raise ValueError("Empty model response")
        return {**grounded, "content": text, "status": "answered_llm_grounded",
                "assumptions": list(dict.fromkeys([*grounded.get("assumptions", []),
                    "LLM wording is constrained to the deterministic grounded draft."]))}
    except Exception:
        return {**grounded, "limitations": list(dict.fromkeys([*grounded["limitations"],
            "LLM explanation was unavailable; this is the deterministic grounded response."]))}
