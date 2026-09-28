"""Exceptions métier : chacune porte un message clair destiné à l'utilisateur."""


class TriageBotError(Exception):
    """Erreur attendue, affichée proprement par la CLI (sans traceback)."""


class TicketsFileNotFoundError(TriageBotError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Fichier de tickets introuvable : {path}")


class InvalidTicketsFileError(TriageBotError):
    def __init__(self, path: str, detail: str) -> None:
        super().__init__(f"Fichier de tickets invalide ({path}) : {detail}")


class OllamaUnavailableError(TriageBotError):
    def __init__(self, host: str) -> None:
        super().__init__(
            f"Impossible de joindre Ollama sur {host}. "
            "Vérifiez qu'il est lancé (commande : `ollama serve`) puis réessayez."
        )


class ModelNotFoundError(TriageBotError):
    def __init__(self, model: str) -> None:
        super().__init__(
            f"Le modèle « {model} » n'est pas installé dans Ollama. "
            f"Téléchargez-le avec : `ollama pull {model}`"
        )


class InvalidLLMResponseError(Exception):
    """Réponse du LLM inexploitable (JSON invalide, champ manquant, valeur hors liste...)."""
