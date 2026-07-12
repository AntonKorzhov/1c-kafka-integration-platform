import json
import os
import sys
import time
from typing import Any

from confluent_kafka import Consumer, KafkaException, Producer

from .common import configure_logging, log, utc_now
from .database import EventValidationError, upsert_event
from .health import start_health_server


def publish_to_dlq(producer: Producer, message: Any, reason: str) -> None:
    value = {
        "failed_at": utc_now(),
        "reason": reason,
        "original_topic": message.topic(),
        "original_partition": message.partition(),
        "original_offset": message.offset(),
        "key": message.key().decode("utf-8") if message.key() else None,
        "value": message.value().decode("utf-8", errors="replace") if message.value() else None,
    }
    producer.produce(
        os.getenv("KAFKA_DLQ_TOPIC", "1c.integration.dlq.v1"),
        key=message.key(),
        value=json.dumps(value, ensure_ascii=False).encode("utf-8"),
    )
    if producer.flush(30):
        raise RuntimeError("Kafka did not confirm DLQ message")


def main() -> int:
    logger = configure_logging()
    ready = {"ready": False}
    start_health_server(int(os.getenv("HEALTH_PORT", "8081")), ready)
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    consumer = Consumer({
        "bootstrap.servers": bootstrap,
        "group.id": os.getenv("KAFKA_CONSUMER_GROUP", "one-c-postgres-sink-v1"),
        "enable.auto.commit": False,
        "auto.offset.reset": "earliest",
        "enable.auto.offset.store": False,
    })
    dlq_producer = Producer({"bootstrap.servers": bootstrap, "acks": "all", "enable.idempotence": True})
    topics = [
        os.getenv("KAFKA_OWNERSHIP_TOPIC", "1c.ownership_forms.v1"),
        os.getenv("KAFKA_COUNTERPARTIES_TOPIC", "1c.counterparties.v1"),
    ]
    max_retries = int(os.getenv("MAX_RETRIES", "5"))
    consumer.subscribe(topics)
    ready["ready"] = True
    log(logger, "INFO", "consumer_started", topics=topics)
    try:
        while True:
            message = consumer.poll(1.0)
            if message is None:
                continue
            if message.error():
                log(logger, "ERROR", "kafka_consumer_error", error=str(message.error()))
                continue
            try:
                event = json.loads(message.value().decode("utf-8"))
                if not isinstance(event, dict):
                    raise EventValidationError("event must be a JSON object")
                upsert_event(event)
            except (UnicodeDecodeError, json.JSONDecodeError, EventValidationError) as exc:
                # Невалидный контракт нельзя исправить повтором: сохраняем исходное
                # сообщение в DLQ и коммитим offset, чтобы поток не остановился.
                publish_to_dlq(dlq_producer, message, str(exc))
                consumer.commit(message=message, asynchronous=False)
                log(logger, "ERROR", "message_sent_to_dlq", reason=str(exc), offset=message.offset())
                continue
            except Exception as exc:
                # Ошибки БД (включая внешний ключ) могут быть временными. Не коммитим
                # offset до успеха; после лимита сообщение также остаётся в DLQ.
                delivered = False
                last_error = exc
                for attempt in range(1, max_retries + 1):
                    log(logger, "WARNING", "message_processing_retry", attempt=attempt, error=str(last_error), offset=message.offset())
                    time.sleep(min(attempt, 5))
                    try:
                        upsert_event(event)
                        delivered = True
                        break
                    except Exception as retry_error:
                        last_error = retry_error
                if not delivered:
                    publish_to_dlq(dlq_producer, message, f"processing failed after {max_retries} attempts: {last_error}")
                    consumer.commit(message=message, asynchronous=False)
                    log(logger, "ERROR", "message_sent_to_dlq", reason=str(last_error), offset=message.offset())
                    continue
            consumer.commit(message=message, asynchronous=False)
            log(logger, "INFO", "message_upserted", topic=message.topic(), offset=message.offset())
    except KeyboardInterrupt:
        log(logger, "INFO", "consumer_stopping")
    except KafkaException as exc:
        log(logger, "ERROR", "consumer_stopped", error=str(exc))
        return 1
    finally:
        consumer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
