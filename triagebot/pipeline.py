"""Orchestration du traitement : préparation, analyse LLM, report sur les doublons."""

from collections.abc import Callable
from typing import Any

from triagebot.analyzer import analyze_ticket
from triagebot.llm import LLMClient
from triagebot.models import Ticket, TriageResult
from triagebot.preprocess import prepare_tickets

ProgressCallback = Callable[[Ticket], None]


def run_triage(entries: list[Any], client: LLMClient, on_progress: ProgressCallback | None = None) -> list[TriageResult]:
    """Traite toutes les entrées et renvoie un résultat par entrée, triés par identifiant."""
    prepared = prepare_tickets(entries)
    analyzed: list[TriageResult] = []
    for ticket in prepared.to_analyze:
        if on_progress:
            on_progress(ticket)
        analyzed.append(analyze_ticket(ticket, client))
    _copy_analysis_to_duplicates(prepared.duplicates, analyzed)
    all_results = analyzed + prepared.skipped + prepared.duplicates
    return sorted(all_results, key=lambda result: result.ticket.id)


def _copy_analysis_to_duplicates(duplicates: list[TriageResult], analyzed: list[TriageResult]) -> None:
    """Un doublon reprend l'analyse de l'original, sans nouvel appel au LLM."""
    by_id = {result.ticket.id: result for result in analyzed}
    for duplicate in duplicates:
        original = by_id.get(duplicate.duplicate_of) if duplicate.duplicate_of is not None else None
        if original:
            duplicate.analysis = original.analysis
