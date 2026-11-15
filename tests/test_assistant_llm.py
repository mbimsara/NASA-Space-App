import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services.assistant_llm import enhance


class FakeClient:
    def __init__(self):
        self.responses = self
        self.kwargs = None
    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text="  Grounded natural-language explanation.  ")


class AssistantLlmTests(unittest.TestCase):
    def test_default_deterministic_mode_makes_no_call(self):
        grounded = {"content": "Draft", "source_ids": ["o1"], "assumptions": [], "limitations": []}
        self.assertIs(enhance({"message": "Why?"}, grounded), grounded)

    def test_optional_provider_preserves_citations_and_disclosures(self):
        grounded = {"content": "Draft 12 mm", "source_ids": ["o1"], "assumptions": ["A"], "limitations": ["L"]}
        client = FakeClient()
        fake_settings = SimpleNamespace(assistant_provider="openai", openai_model="configured-model")
        with patch("backend.app.services.assistant_llm.settings", fake_settings):
            result = enhance({"message": "Why?"}, grounded, lambda: client)
        self.assertEqual(result["source_ids"], ["o1"])
        self.assertEqual(result["limitations"], ["L"])
        self.assertFalse(client.kwargs["store"])
        self.assertEqual(client.kwargs["model"], "configured-model")


if __name__ == "__main__":
    unittest.main()
