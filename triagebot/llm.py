"""Client minimaliste autour de la bibliothèque `ollama`."""

from typing import Any, Protocol

import ollama

from triagebot.config import DEFAULT_MODEL, LLM_TEMPERATURE, OLLAMA_HOST
from triagebot.models import Category, Sentiment

# Schéma JSON transmis à Ollama pour contraindre la sortie (structured output).
ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": [c.value for c in Category]},
        "severity": {"type": "integer", "minimum": 1, "maximum": 5},
        "sentiment": {"type": "string", "enum": [s.value for s in Sentiment]},
        "summary": {"type": "string"},
    },
    "required": ["category", "severity", "sentiment", "summary"],
}


class LLMClient(Protocol):
    """Interface commune : permet de remplacer Ollama par un faux client dans les tests."""

    model: str

    def complete(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str: ...


class OllamaClient:
    """Appelle un modèle servi localement par Ollama."""

    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST) -> None:
        self.model = model
        self._client = ollama.Client(host=host)

    def complete(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        response = self._client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            format=schema,
            options={"temperature": LLM_TEMPERATURE},
        )
        return response.message.content or ""
