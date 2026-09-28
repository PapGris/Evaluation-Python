"""Chargement des tickets depuis un fichier JSON."""

import json
from pathlib import Path
from typing import Any

from triagebot.models import Ticket


def load_tickets(path: Path) -> list[Ticket]:
    """Lit le fichier JSON et renvoie la liste des tickets."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [_to_ticket(entry) for entry in raw]


def _to_ticket(entry: dict[str, Any]) -> Ticket:
    return Ticket(
        id=entry["id"],
        player=entry["player"],
        message=entry["message"],
    )
