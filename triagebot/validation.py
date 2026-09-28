"""Validation stricte des réponses du LLM : on ne lui fait jamais confiance aveuglément."""

import json
from typing import Any

from triagebot.errors import InvalidLLMResponseError
from triagebot.models import MAX_SEVERITY, MIN_SEVERITY, Analysis, Category, Sentiment

REQUIRED_FIELDS: tuple[str, ...] = ("category", "severity", "sentiment", "summary")


def parse_analysis(raw: str) -> Analysis:
    """Convertit la réponse brute du LLM en `Analysis`, ou lève `InvalidLLMResponseError`."""
    data = _load_json_object(raw)
    _check_required_fields(data)
    return Analysis(
        category=_parse_category(data["category"]),
        severity=_parse_severity(data["severity"]),
        sentiment=_parse_sentiment(data["sentiment"]),
        summary=_parse_summary(data["summary"]),
    )


def _load_json_object(raw: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise InvalidLLMResponseError(f"JSON invalide : {exc}") from exc
    if not isinstance(data, dict):
        raise InvalidLLMResponseError("la réponse n'est pas un objet JSON")
    return data


def _check_required_fields(data: dict[str, Any]) -> None:
    missing = [name for name in REQUIRED_FIELDS if name not in data]
    if missing:
        raise InvalidLLMResponseError(f"champ(s) manquant(s) : {', '.join(missing)}")


def _normalize(value: Any) -> str:
    if not isinstance(value, str):
        raise InvalidLLMResponseError(f"valeur texte attendue, reçu {value!r}")
    return value.strip().lower()


def _parse_category(value: Any) -> Category:
    try:
        return Category(_normalize(value))
    except ValueError as exc:
        raise InvalidLLMResponseError(f"catégorie non autorisée : {value!r}") from exc


def _parse_sentiment(value: Any) -> Sentiment:
    try:
        return Sentiment(_normalize(value))
    except ValueError as exc:
        raise InvalidLLMResponseError(f"sentiment non autorisé : {value!r}") from exc


def _parse_severity(value: Any) -> int:
    # bool est une sous-classe de int en Python : on l'exclut explicitement.
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidLLMResponseError(f"la sévérité doit être un entier, reçu {value!r}")
    if not MIN_SEVERITY <= value <= MAX_SEVERITY:
        raise InvalidLLMResponseError(f"sévérité hors de l'intervalle 1-5 : {value}")
    return value


def _parse_summary(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidLLMResponseError("le résumé est vide ou n'est pas un texte")
    return value.strip()
