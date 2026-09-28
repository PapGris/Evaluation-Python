"""Écriture des résultats sur disque."""

import json
from pathlib import Path

from triagebot.models import TriageResult


def save_results(results: list[TriageResult], path: Path) -> None:
    """Sauvegarde chaque ticket d'origine accompagné de son analyse."""
    payload = [result.to_dict() for result in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
