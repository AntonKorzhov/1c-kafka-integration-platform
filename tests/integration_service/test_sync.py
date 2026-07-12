import json
from datetime import datetime, timezone

import pytest

from app import sync


class FakeClient:
    def __init__(self, items: list[dict[str, object]]) -> None:
        self.items = items
        self.calls: list[tuple[str, datetime | None]] = []

    def fetch(self, path: str, changed_since: datetime | None) -> list[dict[str, object]]:
        self.calls.append((path, changed_since))
        return self.items


class FakeProducer:
    def __init__(self, flush_result: int = 0) -> None:
        self.messages: list[dict[str, object]] = []
        self.flush_result = flush_result

    def produce(self, **kwargs: object) -> None:
        self.messages.append(kwargs)

    def poll(self, _: float) -> None:
        return None

    def flush(self, _: float) -> int:
        return self.flush_result


def test_publish_resource_uses_stable_key_and_saves_watermark_after_flush(monkeypatch: pytest.MonkeyPatch) -> None:
    watermark = datetime(2026, 7, 11, 9, 20, tzinfo=timezone.utc)
    saved: list[tuple[str, datetime]] = []
    monkeypatch.setattr(sync, "get_watermark", lambda _: watermark)
    monkeypatch.setattr(sync, "save_watermark", lambda resource, value: saved.append((resource, value)))

    payload = {"id": "b7e2a1f0-3b5d-4a1d-8d5a-1d6c8c1a0001", "name": "ООО Ромашка"}
    client = FakeClient([payload])
    producer = FakeProducer()

    count = sync.publish_resource(
        producer, client, resource_name="counterparties", path="counterparties",
        topic="1c.counterparties.v1", event_type="counterparty.upsert",
        normalizer=lambda item: item, mode="incremental",
    )

    assert count == 1
    assert client.calls == [("counterparties", datetime(2026, 7, 11, 9, 19, 59, tzinfo=timezone.utc))]
    assert producer.messages[0]["key"] == payload["id"].encode()
    event = json.loads(producer.messages[0]["value"].decode())
    assert event["event_type"] == "counterparty.upsert"
    assert event["source"] == "1c"
    assert event["payload"] == payload
    assert saved and saved[0][0] == "counterparties"


def test_publish_resource_does_not_advance_watermark_when_kafka_flush_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: list[object] = []
    monkeypatch.setattr(sync, "save_watermark", lambda *_: saved.append("called"))

    with pytest.raises(RuntimeError, match="did not confirm"):
        sync.publish_resource(
            FakeProducer(flush_result=1), FakeClient([]), resource_name="ownership_forms",
            path="forms-ownership", topic="1c.ownership_forms.v1",
            event_type="ownership_form.upsert", normalizer=lambda item: item, mode="full",
        )

    assert saved == []
