"""Analyse d'un ticket par le LLM, avec validation, nouvelles tentatives et cache."""

import json
import logging

from triagebot.cache import ResponseCache
from triagebot.config import MAX_ATTEMPTS
from triagebot.errors import InvalidLLMResponseError
from triagebot.llm import ANALYSIS_SCHEMA, LLMClient
from triagebot.models import Analysis, Status, Ticket, TriageResult
from triagebot.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt
from triagebot.validation import parse_analysis

logger = logging.getLogger(__name__)

CACHE_KIND = "analysis"


def analyze_ticket(
    ticket: Ticket,
    client: LLMClient,
    max_attempts: int = MAX_ATTEMPTS,
    cache: ResponseCache | None = None,
) -> TriageResult:
    """Renvoie l'analyse en cache si elle existe, sinon interroge le LLM.

    Après `max_attempts` réponses invalides, le ticket est marqué `to_check`.
    """
    cached = _read_cache(ticket, client.model, cache)
    if cached:
        return TriageResult(ticket, Status.OK, analysis=cached)
    result = _ask_llm(ticket, client, max_attempts)
    if cache and result.analysis:
        cache.put(CACHE_KIND, client.model, ticket.message, json.dumps(result.analysis.to_dict()))
    return result


def _ask_llm(ticket: Ticket, client: LLMClient, max_attempts: int) -> TriageResult:
    prompt = build_analysis_prompt(ticket.message)
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            raw = client.complete(ANALYSIS_SYSTEM_PROMPT, prompt, ANALYSIS_SCHEMA)
            return TriageResult(ticket, Status.OK, analysis=parse_analysis(raw))
        except InvalidLLMResponseError as exc:
            last_error = str(exc)
            logger.warning("Ticket #%s, essai %d/%d : %s", ticket.id, attempt, max_attempts, exc)
    return TriageResult(
        ticket,
        Status.TO_CHECK,
        reason=f"réponse du LLM invalide après {max_attempts} essais ({last_error})",
    )


def _read_cache(ticket: Ticket, model: str, cache: ResponseCache | None) -> Analysis | None:
    """Lit et revalide l'analyse en cache ; une entrée corrompue est supprimée."""
    if cache is None:
        return None
    raw = cache.get(CACHE_KIND, model, ticket.message)
    if raw is None:
        return None
    try:
        return parse_analysis(raw)
    except InvalidLLMResponseError:
        logger.warning("Entrée de cache invalide pour le ticket #%s : ignorée", ticket.id)
        cache.discard(CACHE_KIND, model, ticket.message)
        return None
