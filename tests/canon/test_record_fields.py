from __future__ import annotations

import pytest

from orchestra.canon.errors import RecordShapeError
from orchestra.canon.fields import optional_text, required_int, required_text
from orchestra.canon.types import JsonValue, Record


def _record() -> Record:
    return Record(
        id="rec-1",
        record_type="t",
        subject="s",
        payload={},
        lifecycle_state="active",
        relationships={},
        revision="r",
        recorded_at="",
    )


def test_required_text_names_the_record_and_field_when_absent() -> None:
    with pytest.raises(RecordShapeError, match=r"rec-1.*title.*required"):
        required_text(_record(), {}, "title")


def test_required_text_keeps_an_empty_string() -> None:
    assert required_text(_record(), {"title": ""}, "title") == ""


def test_optional_text_is_none_when_absent() -> None:
    assert optional_text(_record(), {}, "base") is None


def test_optional_text_rejects_an_empty_string() -> None:
    with pytest.raises(RecordShapeError, match=r"effort.*empty"):
        optional_text(_record(), {"effort": ""}, "effort")


def test_optional_text_rejects_a_non_string() -> None:
    with pytest.raises(RecordShapeError, match=r"base.*string"):
        optional_text(_record(), {"base": 3}, "base")


@pytest.mark.parametrize("value", [True, "1", 1.5])
def test_required_int_rejects_other_types(value: JsonValue) -> None:
    with pytest.raises(RecordShapeError, match=r"number.*integer"):
        required_int(_record(), {"number": value}, "number")
