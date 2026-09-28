"""Chargement du fichier de tickets.

Le chargeur ne valide que l'enveloppe du fichier (existence, JSON bien formé,
liste à la racine). Le contenu de chaque entrée est vérifié ensuite par
`preprocess`, pour qu'une entrée abîmée n'empêche pas de traiter les autres.
"""

import json
from pathlib import Path
from typing import Any

from triagebot.errors import InvalidTicketsFileError, TicketsFileNotFoundError


def load_entries(path: Path) -> list[Any]:
    """Lit le fichier et renvoie la liste brute des entrées."""
    if not path.is_file():
        raise TicketsFileNotFoundError(str(path))
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise InvalidTicketsFileError(str(path), f"lecture impossible ({exc})") from exc
    return _parse(content, path)


def _parse(content: str, path: Path) -> list[Any]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise InvalidTicketsFileError(
            str(path), f"JSON mal formé ligne {exc.lineno}, colonne {exc.colno} : {exc.msg}"
        ) from exc
    if not isinstance(data, list):
        raise InvalidTicketsFileError(str(path), "la racine doit être une liste de tickets")
    return data
