"""Détection de la langue du joueur (déterministe, sans LLM)."""

from langdetect import DetectorFactory, LangDetectException, detect

# Graine fixe : langdetect est probabiliste, on veut un résultat reproductible.
DetectorFactory.seed = 0

DEFAULT_LANGUAGE = "fr"

LANGUAGE_NAMES: dict[str, str] = {
    "fr": "français",
    "en": "anglais",
    "de": "allemand",
    "es": "espagnol",
    "it": "italien",
    "pt": "portugais",
    "nl": "néerlandais",
}


def detect_language(text: str) -> str:
    """Renvoie le code ISO 639-1 de la langue, ou le français par défaut si indéterminable."""
    try:
        return detect(text)
    except LangDetectException:
        return DEFAULT_LANGUAGE


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)
