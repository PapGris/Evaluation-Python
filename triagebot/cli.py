"""Point d'entrée en ligne de commande."""

import argparse
from pathlib import Path

from triagebot.analyzer import analyze_ticket
from triagebot.config import DEFAULT_MODEL, DEFAULT_RESULTS_PATH, DEFAULT_TICKETS_PATH
from triagebot.llm import OllamaClient
from triagebot.loader import load_tickets
from triagebot.storage import save_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="triagebot", description="Trie les tickets support avec un LLM local.")
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_TICKETS_PATH, help="fichier de tickets JSON")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_RESULTS_PATH, help="fichier de résultats JSON")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help="modèle Ollama à utiliser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    tickets = load_tickets(args.input)
    client = OllamaClient(model=args.model)
    results = [analyze_ticket(ticket, client) for ticket in tickets]
    save_results(results, args.output)
    print(f"{len(results)} tickets analysés -> {args.output}")
    return 0
