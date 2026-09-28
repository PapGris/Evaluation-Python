"""Tableau de bord affiché dans le terminal avec `rich`."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from triagebot.models import Status
from triagebot.stats import TriageStats

STATUS_LABELS: dict[Status, str] = {
    Status.OK: "Analysés",
    Status.TO_CHECK: "À vérifier",
    Status.SKIPPED: "Écartés (inutilisables)",
    Status.DUPLICATE: "Doublons",
}


def render_dashboard(stats: TriageStats, console: Console | None = None) -> None:
    console = console or Console()
    console.print(Panel.fit("[bold]TriageBot — Tableau de bord[/bold]", border_style="cyan"))
    console.print(_status_table(stats))
    console.print(_category_table(stats))
    console.print(_average_line(stats))
    console.print(_urgent_table(stats))


def _status_table(stats: TriageStats) -> Table:
    table = Table(title=f"Tickets reçus : {stats.total}", title_justify="left")
    table.add_column("Statut")
    table.add_column("Nombre", justify="right")
    for status, count in stats.by_status.items():
        table.add_row(STATUS_LABELS[status], str(count))
    return table


def _category_table(stats: TriageStats) -> Table:
    table = Table(title="Tickets par catégorie", title_justify="left")
    table.add_column("Catégorie")
    table.add_column("Nombre", justify="right")
    for category, count in stats.by_category.items():
        table.add_row(str(category), str(count))
    return table


def _average_line(stats: TriageStats) -> str:
    if stats.average_severity is None:
        return "[bold]Urgence moyenne :[/bold] n/a (aucun ticket analysé)\n"
    return f"[bold]Urgence moyenne :[/bold] {stats.average_severity:.2f} / 5\n"


def _urgent_table(stats: TriageStats) -> Table:
    table = Table(title="Top 3 des tickets les plus urgents", title_justify="left")
    for column in ("#", "Joueur", "Catégorie", "Urgence", "Résumé"):
        table.add_column(column)
    for result in stats.most_urgent:
        if result.analysis:
            table.add_row(
                str(result.ticket.id),
                result.ticket.player,
                str(result.analysis.category),
                str(result.analysis.severity),
                result.analysis.summary,
            )
    return table
