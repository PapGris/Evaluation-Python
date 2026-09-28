"""Génération de brouillons de réponse dans la langue du joueur."""

import logging

from triagebot.config import MAX_ATTEMPTS
from triagebot.errors import InvalidLLMResponseError
from triagebot.language import DEFAULT_LANGUAGE, language_name
from triagebot.llm import LLMClient
from triagebot.models import Status, TriageResult
from triagebot.prompts import DRAFT_SYSTEM_PROMPT, build_draft_prompt

logger = logging.getLogger(__name__)

MAX_DRAFT_LENGTH = 1500

# Réponses de secours, utilisées quand le LLM n'est pas appelé ou échoue.
FALLBACK_DRAFTS: dict[str, str] = {
    "fr": "Bonjour, merci pour votre message. Nous l'avons bien reçu et notre équipe revient vers vous "
    "très rapidement.\nL'équipe support PixelForge",
    "en": "Hello, thank you for your message. We have received it and our team will get back to you "
    "shortly.\nThe PixelForge support team",
    "de": "Hallo, vielen Dank für Ihre Nachricht. Wir haben sie erhalten und unser Team meldet sich "
    "in Kürze bei Ihnen.\nDas PixelForge-Supportteam",
}

EMPTY_MESSAGE_DRAFT = (
    "Bonjour, nous avons reçu un ticket de votre part mais son contenu est vide ou illisible. "
    "Pourriez-vous nous décrire à nouveau votre demande ?\nL'équipe support PixelForge"
)


def generate_draft(result: TriageResult, client: LLMClient, max_attempts: int = MAX_ATTEMPTS) -> str:
    """Produit un brouillon adapté ; se rabat sur un modèle fixe si le LLM échoue."""
    if result.status == Status.SKIPPED:
        return EMPTY_MESSAGE_DRAFT
    language = result.language or DEFAULT_LANGUAGE
    system = DRAFT_SYSTEM_PROMPT.format(language=language_name(language))
    prompt = _prompt_for(result)
    for attempt in range(1, max_attempts + 1):
        try:
            return _clean_draft(client.complete(system, prompt))
        except InvalidLLMResponseError as exc:
            logger.warning("Brouillon du ticket #%s, essai %d/%d : %s", result.ticket.id, attempt, max_attempts, exc)
    return fallback_draft(language)


def fallback_draft(language: str) -> str:
    return FALLBACK_DRAFTS.get(language, FALLBACK_DRAFTS["en"])


def _prompt_for(result: TriageResult) -> str:
    analysis = result.analysis
    return build_draft_prompt(
        result.ticket.message,
        str(analysis.category) if analysis else None,
        analysis.summary if analysis else None,
    )


def _clean_draft(raw: str) -> str:
    draft = raw.strip()
    if not draft:
        raise InvalidLLMResponseError("brouillon vide")
    if len(draft) > MAX_DRAFT_LENGTH:
        raise InvalidLLMResponseError(f"brouillon trop long ({len(draft)} caractères)")
    return draft
