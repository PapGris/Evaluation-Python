"""Client minimaliste autour de la bibliothèque `ollama`."""

from typing import Any, Protocol

import httpx
import ollama

from triagebot.config import DEFAULT_MODEL, LLM_TEMPERATURE, OLLAMA_HOST
from triagebot.errors import InvalidLLMResponseError, ModelNotFoundError, OllamaUnavailableError
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

# Erreurs réseau signifiant qu'Ollama ne répond pas.
_CONNECTION_ERRORS: tuple[type[Exception], ...] = (ConnectionError, httpx.ConnectError, httpx.TimeoutException)


class LLMClient(Protocol):
    """Interface commune : permet de remplacer Ollama par un faux client dans les tests."""

    model: str

    def complete(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str: ...


class OllamaClient:
    """Appelle un modèle servi localement par Ollama."""

    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_HOST) -> None:
        self.model = model
        self.host = host
        self._client = ollama.Client(host=host)

    def ensure_ready(self) -> None:
        """Vérifie qu'Ollama répond et que le modèle est installé, avant tout traitement."""
        try:
            installed = self._client.list().models
        except _CONNECTION_ERRORS as exc:
            raise OllamaUnavailableError(self.host) from exc
        names = {m.model for m in installed if m.model}
        if self.model not in names and f"{self.model}:latest" not in names:
            raise ModelNotFoundError(self.model)

    def complete(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        try:
            response = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                format=schema,
                options={"temperature": LLM_TEMPERATURE},
            )
        except _CONNECTION_ERRORS as exc:
            raise OllamaUnavailableError(self.host) from exc
        except ollama.ResponseError as exc:
            if exc.status_code == 404:
                raise ModelNotFoundError(self.model) from exc
            # Erreur ponctuelle côté serveur : traitée comme une réponse invalide (donc retentée).
            raise InvalidLLMResponseError(f"erreur Ollama : {exc.error}") from exc
        return response.message.content or ""
