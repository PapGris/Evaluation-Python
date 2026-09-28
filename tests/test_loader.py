from pathlib import Path

import pytest

from triagebot.errors import InvalidTicketsFileError, TicketsFileNotFoundError
from triagebot.loader import load_entries


def test_missing_file_raises_clear_error(tmp_path: Path) -> None:
    with pytest.raises(TicketsFileNotFoundError, match="introuvable"):
        load_entries(tmp_path / "absent.json")


def test_malformed_json_raises_clear_error(tmp_path: Path) -> None:
    path = tmp_path / "tickets.json"
    path.write_text('[{"id": 1,', encoding="utf-8")
    with pytest.raises(InvalidTicketsFileError, match="JSON mal formé"):
        load_entries(path)


def test_root_must_be_a_list(tmp_path: Path) -> None:
    path = tmp_path / "tickets.json"
    path.write_text('{"id": 1}', encoding="utf-8")
    with pytest.raises(InvalidTicketsFileError, match="liste"):
        load_entries(path)


def test_valid_file_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "tickets.json"
    path.write_text('[{"id": 1, "player": "A", "message": "Salut"}]', encoding="utf-8")
    assert load_entries(path) == [{"id": 1, "player": "A", "message": "Salut"}]


def test_provided_dataset_loads() -> None:
    assert len(load_entries(Path("data/tickets.json"))) == 10
