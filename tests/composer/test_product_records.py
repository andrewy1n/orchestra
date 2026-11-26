from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.records import (
    PRODUCT,
    PRODUCT_ITEM,
    current_product,
    current_product_items,
    read_product,
    read_product_item,
)


def _record(
    record_type: str,
    subject: str,
    payload: JsonObject,
    rid: str,
    at: str = "2026-01-01T00:00:00Z",
    state: str = "active",
) -> Record:
    return {
        "id": rid,
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "lifecycle_state": state,
        "relationships": {},
        "revision": "r",
        "recorded_at": at,
    }


def _product(purpose: str, rid: str, at: str = "2026-01-01T00:00:00Z", state: str = "active"):
    payload: JsonObject = {"purpose": purpose, "audience": "maintainers"}
    return _record(PRODUCT, "product", payload, rid, at, state)


def _item(subject: str, status: object, rid: str, state: str = "active") -> Record:
    payload: JsonObject = {"title": f"{subject} title", "description": f"{subject} text"}
    if status is not None:
        payload["status"] = status
    return _record(PRODUCT_ITEM, subject, payload, rid, state=state)


def test_product_statement_reads_purpose_and_audience() -> None:
    product = read_product(_product("Plan work", "p1"))
    assert product.purpose == "Plan work"
    assert product.audience == "maintainers"


def test_current_product_statement_is_the_newest_live_one() -> None:
    records = [
        _product("old", "p1", "2026-01-01T00:00:00Z"),
        _product("new", "p2", "2026-01-02T00:00:00Z"),
        _product("newest but retracted", "p3", "2026-01-03T00:00:00Z", state="retracted"),
        _product("newest but superseded", "p4", "2026-01-04T00:00:00Z", state="superseded"),
    ]
    product = current_product(records)
    assert product is not None
    assert product.purpose == "new"


def test_current_product_statement_is_none_without_a_live_one() -> None:
    assert current_product([]) is None
    assert current_product([_product("gone", "p1", state="retracted")]) is None


def test_capability_item_with_current_status_reads_fields() -> None:
    item = read_product_item(_item("tracks-ideas", "current", "c1"))
    assert item.title == "tracks-ideas title"
    assert item.description == "tracks-ideas text"
    assert item.status == "current"


def test_current_capability_items_list_live_items_and_drop_superseded() -> None:
    records = [
        _item("live-cap", "current", "c1"),
        _item("old-cap", "current", "c2", state="superseded"),
        _item("gone-cap", "current", "c3", state="retracted"),
    ]
    assert [item.title for item in current_product_items(records)] == ["live-cap title"]


def test_goal_item_with_planned_status_reads_fields() -> None:
    item = read_product_item(_item("ship-it", "planned", "g1"))
    assert item.title == "ship-it title"
    assert item.status == "planned"


def test_current_goal_items_keep_planned_status_beside_capabilities() -> None:
    records = [_item("a-cap", "current", "c1"), _item("a-goal", "planned", "g1")]
    statuses = {item.title: item.status for item in current_product_items(records)}
    assert statuses == {"a-cap title": "current", "a-goal title": "planned"}


def test_missing_status_raises_record_shape_error() -> None:
    with pytest.raises(RecordShapeError):
        read_product_item(_item("no-status", None, "s1"))


@pytest.mark.parametrize("status", ["done", "Current", "", 3])
def test_unknown_status_raises_record_shape_error(status: object) -> None:
    with pytest.raises(RecordShapeError):
        read_product_item(_item("bad-status", status, "s2"))


def test_status_is_not_inferred_from_title_or_body() -> None:
    record = _item("planned-goal", None, "s3")
    record["body"] = "This is a planned goal and a current capability."
    with pytest.raises(RecordShapeError):
        read_product_item(record)
