"""Orchestration du traitement : préparation, analyse LLM, brouillons, escalade."""

from collections.abc import Callable
from typing import Any

from triagebot.analyzer import analyze_ticket
from triagebot.drafts import generate_draft
from triagebot.escalation import apply_escalation
from triagebot.language import detect_language
from triagebot.llm import LLMClient
from triagebot.models import Ticket, TriageResult
from triagebot.preprocess import prepare_tickets

ProgressCallback = Callable[[str, Ticket], None]


def run_triage(
    entries: list[Any],
    client: LLMClient,
    with_drafts: bool = True,
    on_progress: ProgressCallback | None = None,
) -> list[TriageResult]:
    """Traite toutes les entrées et renvoie un résultat par entrée, triés par identifiant."""
    prepared = prepare_tickets(entries)
    analyzed = [_analyze(ticket, client, on_progress) for ticket in prepared.to_analyze]
    if with_drafts:
        _add_drafts(analyzed + prepared.skipped, client, on_progress)
    _copy_original_to_duplicates(prepared.duplicates, analyzed)
    all_results = analyzed + prepared.skipped + prepared.duplicates
    apply_escalation(all_results)
    return sorted(all_results, key=lambda result: result.ticket.id)


def _analyze(ticket: Ticket, client: LLMClient, on_progress: ProgressCallback | None) -> TriageResult:
    if on_progress:
        on_progress("Analyse", ticket)
    result = analyze_ticket(ticket, client)
    result.language = detect_language(ticket.message)
    return result


def _add_drafts(results: list[TriageResult], client: LLMClient, on_progress: ProgressCallback | None) -> None:
    for result in results:
        if on_progress:
            on_progress("Brouillon", result.ticket)
        result.draft = generate_draft(result, client)


def _copy_original_to_duplicates(duplicates: list[TriageResult], analyzed: list[TriageResult]) -> None:
    """Un doublon reprend l'analyse et le brouillon de l'original, sans nouvel appel au LLM."""
    by_id = {result.ticket.id: result for result in analyzed}
    for duplicate in duplicates:
        original = by_id.get(duplicate.duplicate_of) if duplicate.duplicate_of is not None else None
        if original:
            duplicate.analysis = original.analysis
            duplicate.language = original.language
            duplicate.draft = original.draft
