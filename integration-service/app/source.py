from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import requests

from .config import Settings


class SourceError(RuntimeError):
    pass


def _as_utc_timestamp(value: Any, field: str = "updated_at") -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceError(f"Field {field} must be a non-empty RFC 3339 string")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceError(f"Field {field} has invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise SourceError(f"Field {field} must include timezone: {value!r}")
    return parsed.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _require_string(item: dict[str, Any], field: str, *, nullable: bool = False) -> str | None:
    value = item.get(field)
    if nullable and (value is None or (isinstance(value, str) and not value.strip())):
        return None
    if not isinstance(value, str) or not value.strip():
        raise SourceError(f"Field {field} must be a non-empty string")
    return value.strip()


def _require_uuid(item: dict[str, Any], field: str, *, nullable: bool = False) -> str | None:
    value = _require_string(item, field, nullable=nullable)
    if value is None:
        return None
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise SourceError(f"Field {field} must be a UUID: {value!r}") from exc


def normalize_ownership_form(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise SourceError("Every ownership form must be an object")
    deleted = item.get("deleted")
    if not isinstance(deleted, bool):
        raise SourceError("Field deleted must be boolean")
    return {
        "id": _require_uuid(item, "id"),
        "code": _require_string(item, "code", nullable=True),
        "name": _require_string(item, "name"),
        "deleted": deleted,
        "updated_at": _as_utc_timestamp(item.get("updated_at")),
    }


def normalize_counterparty(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise SourceError("Every counterparty must be an object")
    deleted = item.get("deleted")
    if not isinstance(deleted, bool):
        raise SourceError("Field deleted must be boolean")
    return {
        "id": _require_uuid(item, "id"),
        "code": _require_string(item, "code", nullable=True),
        "name": _require_string(item, "name"),
        "inn": _require_string(item, "inn", nullable=True),
        "kpp": _require_string(item, "kpp", nullable=True),
        "ownership_form_id": _require_uuid(item, "ownership_form_id", nullable=True),
        "deleted": deleted,
        "updated_at": _as_utc_timestamp(item.get("updated_at")),
    }


class OneCClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        if settings.one_c_host_header:
            self.session.headers["Host"] = settings.one_c_host_header

    def fetch(self, path: str, changed_since: datetime | None) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if changed_since is not None:
            params["changed_since"] = changed_since.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        url = f"{self.settings.one_c_base_url}/{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.settings.timeout_seconds)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SourceError(f"Cannot read 1C endpoint {url}: {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise SourceError(f"1C endpoint {url} returned invalid JSON") from exc
        if not isinstance(body, list):
            raise SourceError(f"1C endpoint {url} must return a JSON array")
        return body
