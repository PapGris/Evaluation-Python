from triagebot.analyzer import analyze_ticket
from triagebot.models import Category, Status, Ticket

from tests.conftest import VALID_ANSWER, FakeLLM

TICKET = Ticket(1, "DragonSlayer42", "Le jeu crash à l'inventaire")


def test_valid_answer_on_first_try() -> None:
    llm = FakeLLM([VALID_ANSWER])
    result = analyze_ticket(TICKET, llm)
    assert result.status == Status.OK
    assert result.analysis and result.analysis.category == Category.BUG
    assert len(llm.calls) == 1


def test_retry_after_invalid_answer() -> None:
    llm = FakeLLM(["pas du json", VALID_ANSWER])
    result = analyze_ticket(TICKET, llm)
    assert result.status == Status.OK
    assert len(llm.calls) == 2


def test_to_check_after_two_invalid_answers() -> None:
    llm = FakeLLM(default='{"category": "question", "severity": 9}')
    result = analyze_ticket(TICKET, llm)
    assert result.status == Status.TO_CHECK
    assert result.analysis is None
    assert result.reason and "2 essais" in result.reason
    assert len(llm.calls) == 2
