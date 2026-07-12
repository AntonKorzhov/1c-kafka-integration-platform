import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from confluent_kafka import Producer

from .common import configure_logging, log, utc_now
from .config import Settings
from .source import OneCClient, normalize_counterparty, normalize_ownership_form
from .state import get_watermark, save_watermark


def delivery_report(error: Any, message: Any) -> None:
    if error is not None:
        raise RuntimeError(f"Kafka delivery failed: {error}")


def publish_resource(
    producer: Producer,
    client: OneCClient,
    *,
    resource_name: str,
    path: str,
    topic: str,
    event_type: str,
    normalizer: Callable[[Any], dict[str, Any]],
    mode: str,
) -> int:
    logger = configure_logging()
    watermark = get_watermark(resource_name) if mode == "incremental" else None
    # Watermark фиксируется в начале: изменения, случившиеся во время чтения,
    # безопасно попадут в следующий запуск (не потеряются).
    next_watermark = datetime.now(timezone.utc)
    fetch_since = watermark - timedelta(seconds=1) if watermark else None
    raw_items = client.fetch(path, fetch_since)
    for raw_item in raw_items:
        payload = normalizer(raw_item)
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "source": "1c",
            "occurred_at": utc_now(),
            "payload": payload,
        }
        producer.produce(
            topic=topic,
            key=payload["id"].encode("utf-8"),
            value=json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            on_delivery=delivery_report,
        )
        producer.poll(0)
    outstanding = producer.flush(30)
    if outstanding:
        raise RuntimeError(f"Kafka did not confirm {outstanding} message(s)")
    save_watermark(resource_name, next_watermark)
    log(logger, "INFO", "resource_synchronized", resource=resource_name, mode=mode, count=len(raw_items), watermark=next_watermark)
    return len(raw_items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize 1C catalogues to Kafka")
    parser.add_argument("--mode", required=True, choices=("full", "incremental"))
    args = parser.parse_args()
    logger = configure_logging()
    try:
        settings = Settings.from_env()
        producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": "one-c-integration-producer",
            "acks": "all",
            "enable.idempotence": True,
            "retries": 5,
        })
        client = OneCClient(settings)
        publish_resource(producer, client, resource_name="ownership_forms", path=settings.forms_path,
                         topic=settings.ownership_topic, event_type="ownership_form.upsert",
                         normalizer=normalize_ownership_form, mode=args.mode)
        publish_resource(producer, client, resource_name="counterparties", path=settings.counterparties_path,
                         topic=settings.counterparties_topic, event_type="counterparty.upsert",
                         normalizer=normalize_counterparty, mode=args.mode)
    except Exception as exc:
        log(logger, "ERROR", "synchronization_failed", error=str(exc), mode=args.mode)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
