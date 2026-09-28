"""Paramètres de configuration centralisés (surchargeables par variables d'environnement)."""

import os
from pathlib import Path

DEFAULT_MODEL: str = os.getenv("TRIAGEBOT_MODEL", "llama3.2:3b")
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

DEFAULT_TICKETS_PATH = Path("data/tickets.json")
DEFAULT_RESULTS_PATH = Path("results.json")
DEFAULT_REPORT_PATH = Path("report.md")
DEFAULT_CACHE_PATH = Path("triagebot_cache.sqlite3")

# Nombre maximum d'essais auprès du LLM pour obtenir une réponse valide.
MAX_ATTEMPTS: int = 2

# Température basse : on veut des réponses stables et reproductibles.
LLM_TEMPERATURE: float = 0.0

# Un message plus court que ce seuil (après nettoyage) est jugé inutilisable.
MIN_MESSAGE_LENGTH: int = 3
