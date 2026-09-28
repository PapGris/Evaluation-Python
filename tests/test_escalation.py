import pytest

from triagebot.escalation import decide_escalation, is_escalated
from triagebot.models import Category, Escalation, Status

from tests.conftest import make_result


def test_toxicity_goes_to_moderation() -> None:
    assert decide_escalation(make_result(Category.TOXICITY, severity=1)) == Escalation.MODERATION


@pytest.mark.parametrize("severity", [4, 5])
def test_urgent_payment_goes_to_support_manager(severity: int) -> None:
    assert decide_escalation(make_result(Category.PAYMENT, severity)) == Escalation.SUPPORT_MANAGER


@pytest.mark.parametrize("severity", [1, 2, 3])
def test_non_urgent_payment_is_standard(severity: int) -> None:
    assert decide_escalation(make_result(Category.PAYMENT, severity)) == Escalation.STANDARD


def test_to_check_requires_human_review() -> None:
    assert decide_escalation(make_result(status=Status.TO_CHECK)) == Escalation.HUMAN_REVIEW


@pytest.mark.parametrize("category", [Category.BUG, Category.ACCOUNT, Category.SUGGESTION, Category.OTHER])
def test_other_categories_are_standard(category: Category) -> None:
    assert decide_escalation(make_result(category, severity=5)) == Escalation.STANDARD


def test_skipped_ticket_is_standard() -> None:
    result = make_result(status=Status.SKIPPED)
    result.analysis = None
    assert decide_escalation(result) == Escalation.STANDARD


def test_rules_are_deterministic() -> None:
    result = make_result(Category.PAYMENT, 4)
    assert {decide_escalation(result) for _ in range(20)} == {Escalation.SUPPORT_MANAGER}


def test_is_escalated_only_for_moderation_and_manager() -> None:
    toxic = make_result(Category.TOXICITY)
    toxic.escalation = Escalation.MODERATION
    bug = make_result(Category.BUG)
    bug.escalation = Escalation.STANDARD
    assert is_escalated(toxic)
    assert not is_escalated(bug)
