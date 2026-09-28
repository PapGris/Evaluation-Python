from triagebot.models import Status
from triagebot.preprocess import is_meaningful, prepare_tickets


def entry(ticket_id: int, message: object, player: str = "Joueur") -> dict[str, object]:
    return {"id": ticket_id, "player": player, "message": message}


def test_valid_ticket_is_kept() -> None:
    prepared = prepare_tickets([entry(1, "Le jeu crash au niveau 3")])
    assert [t.id for t in prepared.to_analyze] == [1]
    assert not prepared.skipped and not prepared.duplicates


def test_empty_and_blank_messages_are_skipped() -> None:
    prepared = prepare_tickets([entry(1, ""), entry(2, "    "), entry(3, "!!! ??")])
    assert not prepared.to_analyze
    assert [r.status for r in prepared.skipped] == [Status.SKIPPED] * 3


def test_malformed_entries_are_skipped_without_crash() -> None:
    entries = ["texte brut", 42, None, {"player": "A", "message": "sans id"}, {"id": 5, "player": "B"}]
    prepared = prepare_tickets(entries)
    assert not prepared.to_analyze
    assert len(prepared.skipped) == len(entries)
    assert all(r.reason for r in prepared.skipped)


def test_same_player_same_message_is_a_duplicate() -> None:
    prepared = prepare_tickets([entry(1, "Crash inventaire"), entry(8, "  crash   INVENTAIRE ")])
    assert [t.id for t in prepared.to_analyze] == [1]
    assert prepared.duplicates[0].duplicate_of == 1
    assert prepared.duplicates[0].status == Status.DUPLICATE


def test_same_message_from_other_player_is_not_a_duplicate() -> None:
    prepared = prepare_tickets([entry(1, "Crash inventaire", "A"), entry(2, "Crash inventaire", "B")])
    assert len(prepared.to_analyze) == 2
    assert not prepared.duplicates


def test_is_meaningful() -> None:
    assert is_meaningful("Ich kann mich nicht einloggen")
    assert not is_meaningful("")
    assert not is_meaningful("?!")
