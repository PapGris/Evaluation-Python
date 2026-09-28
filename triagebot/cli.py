"""Point d'entrée en ligne de commande."""

import argparse
import logging
from pathlib import Path

from rich.console import Console

from triagebot.cache import ResponseCache
from triagebot.config import (
    DEFAULT_CACHE_PATH,
    DEFAULT_MODEL,
    DEFAULT_REPORT_PATH,
    DEFAULT_RESULTS_PATH,
    DEFAULT_TICKETS_PATH,
)
from triagebot.dashboard import render_dashboard
from triagebot.errors import TriageBotError
from triagebot.llm import OllamaClient
from triagebot.loader import load_entries
from triagebot.models import Ticket
from triagebot.pipeline import run_triage
from triagebot.report import export_report
from triagebot.stats import compute_stats
from triagebot.storage import save_results

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triagebot", description="Trie les tickets support avec un LLM local.")
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_TICKETS_PATH, help="fichier de tickets JSON")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_RESULTS_PATH, help="fichier de résultats JSON")
    parser.add_argument("-r", "--report", type=Path, default=DEFAULT_REPORT_PATH, help="rapport Markdown")
    parser.add_argument("--no-drafts", action="store_true", help="ne génère pas les brouillons de réponse")
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH, help="base SQLite du cache")
    parser.add_argument("--no-cache", action="store_true", help="désactive le cache (tout est renvoyé au LLM)")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="modèle Ollama à utiliser")
    parser.add_argument("-v", "--verbose", action="store_true", help="affiche le détail des réponses invalides")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.WARNING if args.verbose else logging.ERROR, format="  %(message)s")
    try:
        return _run(args)
    except TriageBotError as exc:
        console.print(f"[bold red]Erreur :[/bold red] {exc}")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompu par l'utilisateur.[/yellow]")
        return 130


def _run(args: argparse.Namespace) -> int:
    entries = load_entries(args.input)
    client = OllamaClient(model=args.model)
    client.ensure_ready()
    cache = None if args.no_cache else ResponseCache(args.cache)
    try:
        results = run_triage(
            entries, client, with_drafts=not args.no_drafts, on_progress=_print_progress, cache=cache
        )
    finally:
        if cache:
            cache.close()
    save_results(results, args.output)
    export_report(results, args.report, client.model)
    render_dashboard(compute_stats(results), console)
    if cache:
        console.print(f"[dim]Cache : {cache.hits} réponse(s) réutilisée(s), {cache.misses} absente(s) du cache[/dim]")
    console.print(f"[green]Résultats : {args.output} — Rapport : {args.report}[/green]")
    return 0


def _print_progress(step: str, ticket: Ticket) -> None:
    console.print(f"[dim]{step} du ticket #{ticket.id} ({ticket.player})...[/dim]")
