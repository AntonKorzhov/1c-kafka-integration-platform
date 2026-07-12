import pytest

from app import database


COUNTERPARTY_ID = "b7e2a1f0-3b5d-4a1d-8d5a-1d6c8c1a0001"


def event(event_type: str = "counterparty.upsert") -> dict[str, object]:
    return {
        "event_type": event_type,
        "payload": {
            "id": COUNTERPARTY_ID,
            "name": "ООО Ромашка",
            "deleted": False,
            "updated_at": "2026-07-11T09:20:00Z",
        },
    }


def test_payload_rejects_missing_required_field() -> None:
    invalid = event()
    del invalid["payload"]["deleted"] 

    with pytest.raises(database.EventValidationError, match="deleted"):
        database._payload(invalid)


def test_upsert_event_routes_counterparty_to_correct_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[dict[str, object]] = []
    monkeypatch.setattr(database, "_upsert_counterparty", lambda payload: received.append(payload))

    database.upsert_event(event())

    assert received[0]["id"] == COUNTERPARTY_ID


def test_upsert_event_rejects_unknown_event_type() -> None:
    with pytest.raises(database.EventValidationError, match="unsupported event_type"):
        database.upsert_event(event("counterparty.deleted"))


def test_counterparty_upsert_rejects_invalid_uuid_before_database_connection() -> None:
    invalid = event()["payload"]
    invalid["id"] = "not-a-uuid"  

    with pytest.raises(database.EventValidationError, match="UUID"):
        database._upsert_counterparty(invalid)  
