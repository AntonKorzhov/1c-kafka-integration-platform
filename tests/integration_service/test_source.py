import pytest

from app.source import SourceError, normalize_counterparty, normalize_ownership_form


FORM_ID = "7d6874d2-86db-4ed1-b4ad-68839dc32901"
COUNTERPARTY_ID = "b7e2a1f0-3b5d-4a1d-8d5a-1d6c8c1a0001"
TIMESTAMP = "2026-07-11T09:20:00Z"


def test_normalize_counterparty_accepts_empty_kpp_for_individual_entrepreneur() -> None:
    result = normalize_counterparty({
        "id": COUNTERPARTY_ID,
        "code": "000003",
        "name": "ИП Иванов И.И.",
        "inn": "312345678901",
        "kpp": "",
        "ownership_form_id": FORM_ID,
        "deleted": False,
        "updated_at": TIMESTAMP,
    })

    assert result["kpp"] is None
    assert result["ownership_form_id"] == FORM_ID


@pytest.mark.parametrize("field, value", [
    ("id", "not-a-uuid"),
    ("ownership_form_id", "not-a-uuid"),
])
def test_normalize_counterparty_rejects_invalid_uuid(field: str, value: str) -> None:
    item = {
        "id": COUNTERPARTY_ID,
        "code": "000001",
        "name": "ООО Ромашка",
        "inn": "7701234567",
        "kpp": "770101001",
        "ownership_form_id": FORM_ID,
        "deleted": False,
        "updated_at": TIMESTAMP,
    }
    item[field] = value

    with pytest.raises(SourceError, match=field):
        normalize_counterparty(item)


def test_normalize_ownership_form_converts_offset_to_utc() -> None:
    result = normalize_ownership_form({
        "id": FORM_ID,
        "code": "000001",
        "name": "ООО",
        "deleted": False,
        "updated_at": "2026-07-11T12:20:00+03:00",
    })

    assert result["updated_at"] == TIMESTAMP


@pytest.mark.parametrize("updated_at", ["2026-07-11 09:20:00", "not-a-date", ""])
def test_normalize_ownership_form_rejects_non_rfc3339_utc_timestamp(updated_at: str) -> None:
    item = {
        "id": FORM_ID,
        "code": "000001",
        "name": "ООО",
        "deleted": False,
        "updated_at": updated_at,
    }

    with pytest.raises(SourceError, match="updated_at"):
        normalize_ownership_form(item)
