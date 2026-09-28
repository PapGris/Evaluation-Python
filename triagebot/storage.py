"""Écriture des résultats sur disque."""

import json
from pathlib import Path

from triagebot.errors import TriageBotError
from triagebot.models import TriageResult


def save_results(results: list[TriageResult], path: Path) -> None:
    """Sauvegarde chaque ticket d'origine accompagné de son analyse."""
    payload = [result.to_dict() for result in results]
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def write_text(path: Path, content: str) -> None:
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise TriageBotError(f"Impossible d'écrire le fichier {path} : {exc.strerror}") from exc
