"""Discovery of live Groq models compatible with the agent's output schema."""

from __future__ import annotations

from collections.abc import Callable

from groq import Groq

MODEL_DEFAULT = "openai/gpt-oss-20b"

# Current models documented by Groq as supporting JSON structured outputs.
STRUCTURED_OUTPUT_MODELS = frozenset({
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-safeguard-20b",
    "qwen/qwen3.8-27b",
    "meta-models/muse-spark-open",
})


def list_available_models(
    api_key: str,
    client_factory: Callable[..., Groq] = Groq,
) -> list[str]:
    """Fetch models available to this key and keep only schema-capable models."""
    normalized_key = api_key.strip()
    if not normalized_key:
        raise ValueError("Informe a chave de API Groq antes de consultar os modelos.")

    client = client_factory(api_key=normalized_key, timeout=15, max_retries=1)
    response = client.models.list()
    online_models = {model.id for model in response.data}
    return sorted(online_models & STRUCTURED_OUTPUT_MODELS)
