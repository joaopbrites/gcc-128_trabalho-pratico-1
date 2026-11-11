import unittest
from types import SimpleNamespace

from groq_models import MODEL_DEFAULT, list_available_models


class FakeModelsEndpoint:
    def __init__(self, models):
        self.models = models

    def list(self):
        return SimpleNamespace(
            data=[SimpleNamespace(id=model_id) for model_id in self.models]
        )


class FakeGroqClient:
    def __init__(self, models):
        self.models = FakeModelsEndpoint(models)


class GroqModelCatalogTests(unittest.TestCase):
    def test_lists_only_online_models_with_structured_output_support(self):
        captured = {}
        online_models = [
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
            "llama-3.3-70b-versatile",
        ]

        def client_factory(**kwargs):
            captured.update(kwargs)
            return FakeGroqClient(online_models)

        result = list_available_models("  test-key  ", client_factory)

        self.assertEqual(result, ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"])
        self.assertEqual(captured["api_key"], "test-key")
        self.assertEqual(captured["timeout"], 15)
        self.assertEqual(captured["max_retries"], 1)

    def test_default_model_is_present_when_online(self):
        result = list_available_models(
            "test-key",
            lambda **kwargs: FakeGroqClient([MODEL_DEFAULT]),
        )
        self.assertEqual(result, [MODEL_DEFAULT])

    def test_empty_key_is_rejected_without_network_request(self):
        def unexpected_client_factory(**kwargs):
            self.fail("Client should not be constructed when API key is empty.")

        with self.assertRaisesRegex(ValueError, "Informe a chave"):
            list_available_models("  ", unexpected_client_factory)

    def test_empty_compatible_model_list_is_returned_as_empty(self):
        result = list_available_models(
            "test-key",
            lambda **kwargs: FakeGroqClient(["llama-3.3-70b-versatile"]),
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
