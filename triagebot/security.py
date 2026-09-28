"""Détection des tickets qui tentent de manipuler le bot (prompt injection).

Deux parades complémentaires :
1. `sanitize_for_prompt` neutralise les balises qui délimitent le ticket dans le
   prompt, pour qu'un joueur ne puisse pas « sortir » de la zone de données ;
2. `detect_injection` repère, avec des règles Python déterministes, les formulations
   typiques d'une tentative de manipulation. Un ticket suspect est envoyé en
   relecture humaine, quoi qu'en dise le LLM (voir `escalation`).
"""

import re
import unicodedata

# Motifs recherchés dans le message normalisé (minuscules, sans accents).
INJECTION_PATTERNS: dict[str, str] = {
    "consigne d'ignorer les instructions": (
        r"\b(ignore|oublie|ignorez|oubliez|ignoriere|vergiss|disregard|forget)\s+"
        r"(tes|vos|les|toutes|tous|ces|all|your|previous|the|any|deine|alle|die)\b.{0,30}"
        r"\b(instruction|consigne|regle|prompt|anweisung|rule)\w*"
    ),
    "changement de rôle imposé": r"\b(tu es maintenant|you are now|act as|agis comme|joue le role|du bist jetzt)\b",
    "référence au prompt système": r"\b(system prompt|prompt systeme|message systeme|developer mode|jailbreak)\b",
    "consigne de classement": (
        r"\b(classe|classez|categorise|mets|mettez|marque|classify|set|put|mark)\b.{0,40}"
        r"\b(ticket|urgence|severite|categorie|priorite|severity|priority|category)\b"
    ),
    "urgence ou sévérité imposée": r"\b(urgence|severite|severity|priorite|priority)\s*(de\s*|a\s*|to\s*|=\s*|:\s*)?[1-5]\b",
    "balise de prompt injectée": r"</?\s*(ticket|system|assistant|user|instructions?)\s*>",
}

_COMPILED = {label: re.compile(pattern) for label, pattern in INJECTION_PATTERNS.items()}


def normalize(text: str) -> str:
    """Minuscules, sans accents et espaces uniformisés, pour des motifs plus simples."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.lower().split())


def detect_injection(message: str) -> list[str]:
    """Renvoie la liste des motifs de manipulation trouvés (vide si le ticket est sain)."""
    text = normalize(message)
    return [label for label, pattern in _COMPILED.items() if pattern.search(text)]


def sanitize_for_prompt(message: str) -> str:
    """Empêche le message de fermer ou d'ouvrir les balises utilisées dans nos prompts."""
    return re.sub(r"<\s*(/?)\s*(ticket)\s*>", r"[\1\2]", message, flags=re.IGNORECASE)
