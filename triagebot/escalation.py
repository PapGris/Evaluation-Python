"""Règles d'escalade codées en Python pur, sans LLM.

Les décisions critiques restent déterministes : le LLM aide à analyser,
mais c'est ce module qui décide où part chaque ticket.
"""

from triagebot.models import Category, Escalation, Status, TriageResult

PAYMENT_ESCALATION_THRESHOLD = 4

ESCALATION_LABELS: dict[Escalation, str] = {
    Escalation.MODERATION: "Équipe modération",
    Escalation.SUPPORT_MANAGER: "Responsable support",
    Escalation.HUMAN_REVIEW: "Relecture humaine obligatoire",
    Escalation.STANDARD: "Traitement standard",
}


def decide_escalation(result: TriageResult) -> Escalation:
    """Applique les règles dans l'ordre ; la première qui correspond l'emporte."""
    if result.status == Status.TO_CHECK:
        return Escalation.HUMAN_REVIEW
    analysis = result.analysis
    if analysis is None:
        return Escalation.STANDARD
    if analysis.category == Category.TOXICITY:
        return Escalation.MODERATION
    if analysis.category == Category.PAYMENT and analysis.severity >= PAYMENT_ESCALATION_THRESHOLD:
        return Escalation.SUPPORT_MANAGER
    return Escalation.STANDARD


def apply_escalation(results: list[TriageResult]) -> None:
    for result in results:
        result.escalation = decide_escalation(result)


def is_escalated(result: TriageResult) -> bool:
    return result.escalation in (Escalation.MODERATION, Escalation.SUPPORT_MANAGER)
