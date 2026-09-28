"""Outils partagés par les tests : un faux client LLM, sans Ollama."""

import json
from collections.abc import Iterable
from typing import Any

import pytest

from triagebot.models import Analysis, Category, Sentiment, Status, Ticket, TriageResult

VALID_ANSWER = json.dumps({"category": "bug", "severity": 4, "sentiment": "negative", "summary": "Crash."})


class FakeLLM:
    """Renvoie des réponses prédéfinies, dans l'ordre, et compte les appels."""

    model = "fake-model"

    def __init__(self, answers: Iterable[str] | None = None, default: str = VALID_ANSWER) -> None:
        self._answers = list(answers or [])
        self._default = default
        self.calls: list[str] = []

    def complete(self, system: str, prompt: str, schema: dict[str, Any] | None = None) -> str:
        self.calls.append(prompt)
        return self._answers.pop(0) if self._answers else self._default


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


def make_result(
    category: Category = Category.BUG,
    severity: int = 3,
    status: Status = Status.OK,
    ticket_id: int = 1,
) -> TriageResult:
    ticket = Ticket(ticket_id, "Joueur", "Un message de test")
    analysis = Analysis(category, severity, Sentiment.NEUTRAL, "Résumé") if status != Status.TO_CHECK else None
    return TriageResult(ticket, status, analysis=analysis)
