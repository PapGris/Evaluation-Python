"""Calcul des indicateurs, partagés par le dashboard terminal et le rapport Markdown."""

from collections import Counter
from dataclasses import dataclass

from triagebot.models import Category, Status, TriageResult


@dataclass(frozen=True)
class TriageStats:
    total: int
    by_status: dict[Status, int]
    by_category: dict[Category, int]
    average_severity: float | None
    most_urgent: list[TriageResult]


def compute_stats(results: list[TriageResult], top_n: int = 3) -> TriageStats:
    """Les doublons sont exclus des indicateurs pour ne pas compter deux fois le même problème."""
    analyzed = unique_analyzed(results)
    severities = [r.analysis.severity for r in analyzed if r.analysis]
    return TriageStats(
        total=len(results),
        by_status=_count_statuses(results),
        by_category=_count_categories(analyzed),
        average_severity=sum(severities) / len(severities) if severities else None,
        most_urgent=_most_urgent(analyzed, top_n),
    )


def unique_analyzed(results: list[TriageResult]) -> list[TriageResult]:
    return [r for r in results if r.status == Status.OK and r.analysis]


def _count_statuses(results: list[TriageResult]) -> dict[Status, int]:
    counts = Counter(r.status for r in results)
    return {status: counts.get(status, 0) for status in Status}


def _count_categories(analyzed: list[TriageResult]) -> dict[Category, int]:
    counts = Counter(r.analysis.category for r in analyzed if r.analysis)
    return {category: counts.get(category, 0) for category in Category}


def _most_urgent(analyzed: list[TriageResult], top_n: int) -> list[TriageResult]:
    # Tri stable : à sévérité égale, le ticket le plus ancien (id le plus petit) passe devant.
    ranked = sorted(analyzed, key=lambda r: (-r.analysis.severity if r.analysis else 0, r.ticket.id))
    return ranked[:top_n]
