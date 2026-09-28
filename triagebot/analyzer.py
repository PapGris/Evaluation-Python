"""Analyse d'un ticket par le LLM."""

import json

from triagebot.llm import ANALYSIS_SCHEMA, LLMClient
from triagebot.models import Analysis, Category, Sentiment, Status, Ticket, TriageResult
from triagebot.prompts import ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt


def analyze_ticket(ticket: Ticket, client: LLMClient) -> TriageResult:
    """Interroge le LLM et convertit sa réponse JSON en `Analysis`."""
    raw = client.complete(ANALYSIS_SYSTEM_PROMPT, build_analysis_prompt(ticket.message), ANALYSIS_SCHEMA)
    data = json.loads(raw)
    analysis = Analysis(
        category=Category(data["category"]),
        severity=int(data["severity"]),
        sentiment=Sentiment(data["sentiment"]),
        summary=data["summary"],
    )
    return TriageResult(ticket=ticket, status=Status.OK, analysis=analysis)
