import json
from pathlib import Path

import pytest

from triagebot.analyzer import CACHE_KIND, analyze_ticket
from triagebot.cache import ResponseCache
from triagebot.models import Status, Ticket
from triagebot.pipeline import run_triage

from tests.conftest import VALID_ANSWER, FakeLLM

TICKET = Ticket(1, "DragonSlayer42", "Le jeu crash à l'inventaire")


@pytest.fixture
def cache(tmp_path: Path) -> ResponseCache:
    return ResponseCache(tmp_path / "cache.sqlite3")


def test_second_analysis_uses_cache_without_calling_llm(cache: ResponseCache) -> None:
    first_llm, second_llm = FakeLLM([VALID_ANSWER]), FakeLLM()
    first = analyze_ticket(TICKET, first_llm, cache=cache)
    second = analyze_ticket(TICKET, second_llm, cache=cache)
    assert len(first_llm.calls) == 1
    assert second_llm.calls == []
    assert second.status == Status.OK and second.analysis == first.analysis


def test_cache_persists_between_runs(tmp_path: Path) -> None:
    path = tmp_path / "cache.sqlite3"
    first = ResponseCache(path)
    analyze_ticket(TICKET, FakeLLM([VALID_ANSWER]), cache=first)
    first.close()
    llm = FakeLLM()
    analyze_ticket(TICKET, llm, cache=ResponseCache(path))
    assert llm.calls == []


def test_cache_depends_on_model(cache: ResponseCache) -> None:
    analyze_ticket(TICKET, FakeLLM([VALID_ANSWER]), cache=cache)
    other_model = FakeLLM()
    other_model.model = "autre-modele"
    analyze_ticket(TICKET, other_model, cache=cache)
    assert len(other_model.calls) == 1


def test_invalid_answers_are_not_cached(cache: ResponseCache) -> None:
    analyze_ticket(TICKET, FakeLLM(default="pas du json"), cache=cache)
    llm = FakeLLM([VALID_ANSWER])
    assert analyze_ticket(TICKET, llm, cache=cache).status == Status.OK
    assert len(llm.calls) == 1


def test_corrupted_cache_entry_is_ignored_and_llm_is_called(cache: ResponseCache) -> None:
    cache.put(CACHE_KIND, "fake-model", TICKET.message, json.dumps({"category": "inconnue"}))
    llm = FakeLLM([VALID_ANSWER])
    result = analyze_ticket(TICKET, llm, cache=cache)
    assert result.status == Status.OK
    assert len(llm.calls) == 1


def test_full_pipeline_second_run_makes_no_llm_call(cache: ResponseCache) -> None:
    entries = [{"id": 1, "player": "A", "message": "Le jeu crash au niveau 3"}]
    run_triage(entries, FakeLLM(default=VALID_ANSWER), with_drafts=False, cache=cache)
    llm = FakeLLM()
    run_triage(entries, llm, with_drafts=False, cache=cache)
    assert llm.calls == []
