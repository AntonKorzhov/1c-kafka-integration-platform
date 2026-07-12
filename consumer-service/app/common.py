import json
import logging
import os
import sys
from datetime import datetime, timezone


def configure_logging() -> logging.Logger:
    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")
    return logging.getLogger("consumer-service")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def log(logger: logging.Logger, level: str, message: str, **fields: object) -> None:
    record = {"timestamp": utc_now(), "level": level, "service": "consumer-service", "message": message, **fields}
    getattr(logger, level.lower())(json.dumps(record, ensure_ascii=False, default=str))


def postgres_kwargs() -> dict[str, object]:
    return {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "dbname": os.getenv("POSTGRES_DB", "integration"),
        "user": os.getenv("POSTGRES_USER", "integration"),
        "password": os.environ["POSTGRES_PASSWORD"],
    }
