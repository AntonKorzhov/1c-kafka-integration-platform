import uuid
from typing import Any

import psycopg

from .common import postgres_kwargs


class EventValidationError(ValueError):
    pass


def _payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        raise EventValidationError("event.payload must be an object")
    for field in ("id", "name", "deleted", "updated_at"):
        if field not in payload:
            raise EventValidationError(f"event.payload.{field} is required")
    if not isinstance(payload["id"], str) or not payload["id"]:
        raise EventValidationError("event.payload.id must be a string")
    if not isinstance(payload["name"], str) or not payload["name"]:
        raise EventValidationError("event.payload.name must be a non-empty string")
    if not isinstance(payload["deleted"], bool):
        raise EventValidationError("event.payload.deleted must be boolean")
    return payload


def upsert_event(event: dict[str, Any]) -> None:
    event_type = event.get("event_type")
    payload = _payload(event)
    if event_type == "ownership_form.upsert":
        _upsert_ownership_form(payload)
    elif event_type == "counterparty.upsert":
        _upsert_counterparty(payload)
    else:
        raise EventValidationError(f"unsupported event_type: {event_type!r}")


def _upsert_ownership_form(payload: dict[str, Any]) -> None:
    with psycopg.connect(**postgres_kwargs()) as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ownership_forms (id, code, name, source_updated_at, deleted)
            VALUES (%(id)s, %(code)s, %(name)s, %(updated_at)s, %(deleted)s)
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                name = EXCLUDED.name,
                source_updated_at = EXCLUDED.source_updated_at,
                imported_at = now(),
                deleted = EXCLUDED.deleted
            WHERE ownership_forms.source_updated_at IS NULL
               OR EXCLUDED.source_updated_at >= ownership_forms.source_updated_at
            """,
            payload,
        )


def _upsert_counterparty(payload: dict[str, Any]) -> None:
    try:
        uuid.UUID(payload["id"])
    except (ValueError, AttributeError) as exc:
        raise EventValidationError("counterparty payload.id must be UUID") from exc
    for field in ("code", "inn", "kpp", "ownership_form_id"):
        payload.setdefault(field, None)
    with psycopg.connect(**postgres_kwargs()) as conn, conn.transaction(), conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO counterparties
                (id, code, name, inn, kpp, ownership_form_id, source_updated_at, deleted)
            VALUES
                (%(id)s, %(code)s, %(name)s, %(inn)s, %(kpp)s, %(ownership_form_id)s,
                 %(updated_at)s, %(deleted)s)
            ON CONFLICT (id) DO UPDATE SET
                code = EXCLUDED.code,
                name = EXCLUDED.name,
                inn = EXCLUDED.inn,
                kpp = EXCLUDED.kpp,
                ownership_form_id = EXCLUDED.ownership_form_id,
                source_updated_at = EXCLUDED.source_updated_at,
                imported_at = now(),
                deleted = EXCLUDED.deleted
            WHERE counterparties.source_updated_at IS NULL
               OR EXCLUDED.source_updated_at >= counterparties.source_updated_at
            """,
            payload,
        )
