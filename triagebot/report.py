"""Rapport Markdown destiné à un manager non technique."""

from datetime import datetime
from pathlib import Path

from triagebot.escalation import ESCALATION_LABELS, is_escalated
from triagebot.models import Escalation, Status, TriageResult
from triagebot.stats import TriageStats, compute_stats
from triagebot.storage import write_text

CATEGORY_LABELS: dict[str, str] = {
    "bug": "Bugs",
    "payment": "Paiements",
    "account": "Comptes / connexion",
    "suggestion": "Suggestions",
    "toxicity": "Messages toxiques",
    "autre": "Autres demandes",
}


def export_report(results: list[TriageResult], path: Path, model: str) -> None:
    write_text(path, build_report(results, model))


def build_report(results: list[TriageResult], model: str, generated_at: datetime | None = None) -> str:
    stats = compute_stats(results)
    date = (generated_at or datetime.now()).strftime("%d/%m/%Y à %H:%M")
    sections = [
        f"# Rapport de tri des tickets — Dungeon Delivery\n\n_Généré le {date} par TriageBot (modèle {model})._",
        _summary_section(stats),
        _category_section(stats),
        _escalation_section(results),
        _to_check_section(results),
        _urgent_section(stats),
    ]
    return "\n\n".join(sections) + "\n"


def _summary_section(stats: TriageStats) -> str:
    average = f"{stats.average_severity:.1f} / 5" if stats.average_severity is not None else "n/a"
    rows = [
        ("Tickets reçus", stats.total),
        ("Tickets analysés automatiquement", stats.by_status[Status.OK]),
        ("Tickets à vérifier par un humain", stats.by_status[Status.TO_CHECK]),
        ("Doublons regroupés", stats.by_status[Status.DUPLICATE]),
        ("Tickets vides ou illisibles", stats.by_status[Status.SKIPPED]),
    ]
    lines = ["## Synthèse chiffrée", "", "| Indicateur | Valeur |", "|---|---:|"]
    lines += [f"| {label} | {value} |" for label, value in rows]
    lines.append(f"| Urgence moyenne (1 = faible, 5 = critique) | {average} |")
    return "\n".join(lines)


def _category_section(stats: TriageStats) -> str:
    lines = ["## Répartition par type de demande", "", "| Type | Nombre |", "|---|---:|"]
    lines += [f"| {CATEGORY_LABELS[str(cat)]} | {count} |" for cat, count in stats.by_category.items()]
    return "\n".join(lines)


def _escalation_section(results: list[TriageResult]) -> str:
    escalated = [r for r in results if is_escalated(r) and r.status != Status.DUPLICATE]
    lines = ["## Tickets à escalader", ""]
    if not escalated:
        return "\n".join(lines + ["Aucun ticket à escalader."])
    lines += ["| Ticket | Joueur | Transmis à | Urgence | Résumé |", "|---|---|---|---:|---|"]
    lines += [_escalation_row(r) for r in escalated]
    return "\n".join(lines)


def _escalation_row(result: TriageResult) -> str:
    analysis = result.analysis
    label = ESCALATION_LABELS[result.escalation or Escalation.STANDARD]
    severity = analysis.severity if analysis else "-"
    summary = _escape(analysis.summary) if analysis else "-"
    return f"| #{result.ticket.id} | {_escape(result.ticket.player)} | {label} | {severity} | {summary} |"


def _to_check_section(results: list[TriageResult]) -> str:
    to_check = [r for r in results if r.escalation == Escalation.HUMAN_REVIEW]
    lines = ["## Tickets à vérifier", ""]
    if not to_check:
        return "\n".join(lines + ["Aucun ticket à vérifier."])
    lines += [
        "L'outil n'a pas pu analyser ces tickets de façon fiable : un membre de l'équipe doit les lire.",
        "",
        "| Ticket | Joueur | Message | Raison |",
        "|---|---|---|---|",
    ]
    lines += [
        f"| #{r.ticket.id} | {_escape(r.ticket.player)} | {_escape(r.ticket.message)} | {_escape(r.reason or '-')} |"
        for r in to_check
    ]
    return "\n".join(lines)


def _urgent_section(stats: TriageStats) -> str:
    lines = ["## Les 3 tickets les plus urgents", ""]
    for rank, result in enumerate(stats.most_urgent, start=1):
        if result.analysis:
            lines.append(
                f"{rank}. **#{result.ticket.id} ({_escape(result.ticket.player)})** — "
                f"urgence {result.analysis.severity}/5 : {_escape(result.analysis.summary)}"
            )
    return "\n".join(lines)


def _escape(text: str) -> str:
    """Évite qu'un message joueur ne casse la mise en forme des tableaux Markdown."""
    return " ".join(text.split()).replace("|", "\\|")
