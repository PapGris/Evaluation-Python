"""Analyse d'un ticket par le LLM, avec validation et nouvelles tentatives."""

import logging

from triagebot.config import MAX_ATTEMPTS
from triagebot.errors import InvalidLLMResponseError
from triagebot.llm import ANALYSIS_SCHEMA, LLMClient
from triagebot.models import Status, Ticket, TriageResult
from triagebot.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt
from triagebot.validation import parse_analysis

logger = logging.getLogger(__name__)


def analyze_ticket(ticket: Ticket, client: LLMClient, max_attempts: int = MAX_ATTEMPTS) -> TriageResult:
    """Interroge le LLM jusqu'à obtenir une réponse valide.

    Après `max_attempts` réponses invalides, le ticket est marqué `to_check`.
    """
    prompt = build_analysis_prompt(ticket.message)
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            raw = client.complete(ANALYSIS_SYSTEM_PROMPT, prompt, ANALYSIS_SCHEMA)
            analysis = parse_analysis(raw)
        except InvalidLLMResponseError as exc:
            last_error = str(exc)
            logger.warning("Ticket #%s, essai %d/%d : %s", ticket.id, attempt, max_attempts, exc)
            continue
        return TriageResult(ticket, Status.OK, analysis=analysis)
    return TriageResult(
        ticket,
        Status.TO_CHECK,
        reason=f"réponse du LLM invalide après {max_attempts} essais ({last_error})",
    )
