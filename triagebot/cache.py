"""Cache SQLite : un ticket déjà analysé n'est pas renvoyé au LLM.

La clé dépend du modèle, du type de requête (analyse ou brouillon) et du texte
envoyé : changer de modèle ou de message produit donc une nouvelle entrée.
Seules les réponses VALIDÉES sont stockées, et elles sont revalidées à la
lecture : on ne fait pas plus confiance au cache qu'au LLM.
Une panne du cache n'interrompt jamais le traitement : on retombe sur le LLM.
"""

import hashlib
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from triagebot.errors import TriageBotError

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS llm_cache (
    key        TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,
    model      TEXT NOT NULL,
    value      TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def make_key(kind: str, model: str, text: str) -> str:
    return hashlib.sha256(f"{kind}\x1f{model}\x1f{text}".encode()).hexdigest()


class ResponseCache:
    """Stocke les réponses validées du LLM dans une base SQLite locale."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.hits = 0
        self.misses = 0
        try:
            self._connection = sqlite3.connect(path)
            self._connection.execute(_SCHEMA)
            self._connection.commit()
        except sqlite3.Error as exc:
            raise TriageBotError(f"Impossible d'ouvrir le cache SQLite {path} : {exc}") from exc

    def get(self, kind: str, model: str, text: str) -> str | None:
        try:
            row = self._connection.execute(
                "SELECT value FROM llm_cache WHERE key = ?", (make_key(kind, model, text),)
            ).fetchone()
        except sqlite3.Error as exc:
            logger.warning("Lecture du cache impossible : %s", exc)
            row = None
        if row is None:
            self.misses += 1
            return None
        self.hits += 1
        return str(row[0])

    def put(self, kind: str, model: str, text: str, value: str) -> None:
        try:
            self._connection.execute(
                "INSERT OR REPLACE INTO llm_cache (key, kind, model, value, created_at) VALUES (?, ?, ?, ?, ?)",
                (make_key(kind, model, text), kind, model, value, datetime.now(UTC).isoformat()),
            )
            self._connection.commit()
        except sqlite3.Error as exc:
            logger.warning("Écriture dans le cache impossible : %s", exc)

    def discard(self, kind: str, model: str, text: str) -> None:
        """Supprime une entrée devenue invalide (ex. modifiée à la main)."""
        try:
            self._connection.execute("DELETE FROM llm_cache WHERE key = ?", (make_key(kind, model, text),))
            self._connection.commit()
        except sqlite3.Error as exc:
            logger.warning("Nettoyage du cache impossible : %s", exc)

    def close(self) -> None:
        self._connection.close()
