import json

import pytest

from triagebot.errors import InvalidLLMResponseError
from triagebot.models import Category, Sentiment
from triagebot.validation import parse_analysis


def answer(**overrides: object) -> str:
    data = {"category": "payment", "severity": 5, "sentiment": "negative", "summary": "Triple débit."}
    data.update(overrides)
    return json.dumps(data)


def test_valid_answer_is_parsed() -> None:
    analysis = parse_analysis(answer())
    assert analysis.category == Category.PAYMENT
    assert analysis.severity == 5
    assert analysis.sentiment == Sentiment.NEGATIVE
    assert analysis.summary == "Triple débit."


def test_case_and_spaces_are_normalized() -> None:
    analysis = parse_analysis(answer(category=" BUG ", sentiment="Positive"))
    assert analysis.category == Category.BUG
    assert analysis.sentiment == Sentiment.POSITIVE


@pytest.mark.parametrize("raw", ["", "pas du json", "[1, 2]", "null", '"texte"'])
def test_non_object_json_is_rejected(raw: str) -> None:
    with pytest.raises(InvalidLLMResponseError):
        parse_analysis(raw)


@pytest.mark.parametrize("missing", ["category", "severity", "sentiment", "summary"])
def test_missing_field_is_rejected(missing: str) -> None:
    data = json.loads(answer())
    del data[missing]
    with pytest.raises(InvalidLLMResponseError, match=missing):
        parse_analysis(json.dumps(data))


@pytest.mark.parametrize("category", ["question", "refund", "", 3, None])
def test_unknown_category_is_rejected(category: object) -> None:
    with pytest.raises(InvalidLLMResponseError):
        parse_analysis(answer(category=category))


@pytest.mark.parametrize("severity", [0, 6, -1, 9, 3.5, "4", True, None])
def test_invalid_severity_is_rejected(severity: object) -> None:
    with pytest.raises(InvalidLLMResponseError):
        parse_analysis(answer(severity=severity))


@pytest.mark.parametrize("severity", [1, 2, 3, 4, 5])
def test_all_valid_severities_are_accepted(severity: int) -> None:
    assert parse_analysis(answer(severity=severity)).severity == severity


def test_unknown_sentiment_is_rejected() -> None:
    with pytest.raises(InvalidLLMResponseError):
        parse_analysis(answer(sentiment="angry"))


@pytest.mark.parametrize("summary", ["", "   ", 42])
def test_empty_summary_is_rejected(summary: object) -> None:
    with pytest.raises(InvalidLLMResponseError):
        parse_analysis(answer(summary=summary))
