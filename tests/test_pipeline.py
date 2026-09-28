import json
from pathlib import Path

from triagebot.models import Escalation, Status
from triagebot.pipeline import run_triage
from triagebot.report import build_report

from tests.conftest import FakeLLM

ENTRIES = [
    {"id": 1, "player": "A", "message": "Le jeu crash au niveau 3"},
    {"id": 2, "player": "B", "message": ""},
    {"id": 3, "player": "A", "message": "Le jeu crash au niveau 3"},
    {"id": 4, "player": "C", "message": "Débité trois fois, remboursez-moi"},
]
PAYMENT = json.dumps({"category": "payment", "severity": 5, "sentiment": "negative", "summary": "Triple débit."})
BUG = json.dumps({"category": "bug", "severity": 4, "sentiment": "negative", "summary": "Crash."})


def test_llm_is_not_called_for_empty_or_duplicate_tickets() -> None:
    llm = FakeLLM([BUG, PAYMENT])
    run_triage(ENTRIES, llm, with_drafts=False)
    assert len(llm.calls) == 2


def test_results_cover_every_entry_with_escalation() -> None:
    results = run_triage(ENTRIES, FakeLLM([BUG, PAYMENT]), with_drafts=False)
    by_id = {r.ticket.id: r for r in results}
    assert [r.ticket.id for r in results] == [1, 2, 3, 4]
    assert by_id[2].status == Status.SKIPPED
    assert by_id[3].status == Status.DUPLICATE and by_id[3].analysis == by_id[1].analysis
    assert by_id[4].escalation == Escalation.SUPPORT_MANAGER


def test_drafts_are_generated_for_every_ticket() -> None:
    results = run_triage(ENTRIES, FakeLLM([BUG, PAYMENT], default="Bonjour, merci. L'équipe"), with_drafts=True)
    assert all(r.draft for r in results)


def test_report_lists_escalated_tickets(tmp_path: Path) -> None:
    results = run_triage(ENTRIES, FakeLLM([BUG, PAYMENT]), with_drafts=False)
    report = build_report(results, "fake-model")
    assert "## Synthèse chiffrée" in report
    assert "| #4 | C | Responsable support | 5 |" in report
