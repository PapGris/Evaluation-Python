"""Nettoyage des entrées avant tout appel au LLM.

- les entrées mal structurées ou sans contenu exploitable sont écartées (statut `skipped`) ;
- les doublons (même joueur + même message) ne sont analysés qu'une seule fois.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from triagebot.config import MIN_MESSAGE_LENGTH
from triagebot.models import Status, Ticket, TriageResult

UNKNOWN_PLAYER = "<inconnu>"


@dataclass
class PreparedTickets:
    to_analyze: list[Ticket] = field(default_factory=list)
    skipped: list[TriageResult] = field(default_factory=list)
    duplicates: list[TriageResult] = field(default_factory=list)


def prepare_tickets(entries: list[Any]) -> PreparedTickets:
    """Répartit les entrées brutes entre tickets à analyser, écartés et doublons."""
    prepared = PreparedTickets()
    seen: dict[tuple[str, str], int] = {}
    for position, entry in enumerate(entries, start=1):
        ticket, problem = to_ticket(entry, position)
        if problem:
            prepared.skipped.append(TriageResult(ticket, Status.SKIPPED, reason=problem))
            continue
        key = duplicate_key(ticket)
        if key in seen:
            prepared.duplicates.append(_duplicate(ticket, seen[key]))
            continue
        seen[key] = ticket.id
        prepared.to_analyze.append(ticket)
    return prepared


def to_ticket(entry: Any, position: int) -> tuple[Ticket, str | None]:
    """Construit un Ticket et renvoie, le cas échéant, la raison pour laquelle il est inutilisable."""
    if not isinstance(entry, dict):
        return Ticket(position, UNKNOWN_PLAYER, str(entry)), "entrée qui n'est pas un objet JSON"
    ticket_id = entry.get("id")
    player = entry.get("player")
    message = entry.get("message")
    ticket = Ticket(
        id=ticket_id if _is_valid_id(ticket_id) else position,
        player=player.strip() if isinstance(player, str) and player.strip() else UNKNOWN_PLAYER,
        message=message if isinstance(message, str) else "",
    )
    return ticket, _find_problem(ticket_id, message)


def _is_valid_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _find_problem(ticket_id: Any, message: Any) -> str | None:
    if not _is_valid_id(ticket_id):
        return "identifiant manquant ou invalide"
    if not isinstance(message, str):
        return "message absent ou qui n'est pas un texte"
    if not is_meaningful(message):
        return "message vide ou sans contenu exploitable"
    return None


def is_meaningful(message: str) -> bool:
    """Un message est exploitable s'il contient assez de lettres ou de chiffres."""
    useful_chars = re.findall(r"\w", message)
    return len(useful_chars) >= MIN_MESSAGE_LENGTH


def duplicate_key(ticket: Ticket) -> tuple[str, str]:
    """Clé de déduplication insensible à la casse et aux espaces superflus."""
    normalized = " ".join(ticket.message.lower().split())
    return ticket.player.lower(), normalized


def _duplicate(ticket: Ticket, original_id: int) -> TriageResult:
    return TriageResult(
        ticket,
        Status.DUPLICATE,
        reason=f"doublon du ticket #{original_id}",
        duplicate_of=original_id,
    )
