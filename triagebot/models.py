"""Structures de données manipulées par TriageBot."""

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Category(StrEnum):
    BUG = "bug"
    PAYMENT = "payment"
    ACCOUNT = "account"
    SUGGESTION = "suggestion"
    TOXICITY = "toxicity"
    OTHER = "autre"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Status(StrEnum):
    OK = "ok"
    TO_CHECK = "to_check"
    SKIPPED = "skipped"
    DUPLICATE = "duplicate"


class Escalation(StrEnum):
    MODERATION = "moderation"
    SUPPORT_MANAGER = "support_manager"
    HUMAN_REVIEW = "human_review"
    STANDARD = "standard"


MIN_SEVERITY = 1
MAX_SEVERITY = 5


@dataclass(frozen=True)
class Ticket:
    id: int
    player: str
    message: str


@dataclass(frozen=True)
class Analysis:
    category: Category
    severity: int
    sentiment: Sentiment
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": str(self.category),
            "severity": self.severity,
            "sentiment": str(self.sentiment),
            "summary": self.summary,
        }


@dataclass
class TriageResult:
    """Résultat complet du traitement d'un ticket."""

    ticket: Ticket
    status: Status
    analysis: Analysis | None = None
    reason: str | None = None
    duplicate_of: int | None = None
    language: str | None = None
    draft: str | None = None
    escalation: Escalation | None = None
    security_flags: list[str] = field(default_factory=list)

    @property
    def is_suspicious(self) -> bool:
        return bool(self.security_flags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket": asdict(self.ticket),
            "status": str(self.status),
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "reason": self.reason,
            "duplicate_of": self.duplicate_of,
            "language": self.language,
            "escalation": str(self.escalation) if self.escalation else None,
            "security_flags": self.security_flags,
            "draft": self.draft,
        }
