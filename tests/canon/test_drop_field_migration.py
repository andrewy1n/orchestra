from __future__ import annotations

import pytest

from orchestra.canon.schema import SchemaError
from orchestra.canon.types import JsonObject


def test_drop_field_removes_named_payload_fields_from_the_named_type_only() -> None:
    from orchestra.canon.migrate import transform
    from orchestra.canon.schema import check_migrations

    steps = check_migrations(
        [{"from": "1", "to": "2", "drop_field": {"gamma:note": ["text", "absent"]}}], "module"
    )
    module: JsonObject = {"namespace": "gamma", "types": {"note": {"fields": {}}}}
    note = {"record_type": "gamma:note", "payload": {"text": "x", "keep": 1}}
    other = {"record_type": "gamma:other", "payload": {"text": "x"}}
    assert transform(note, steps, module)["payload"] == {"keep": 1}  # pyright: ignore[reportArgumentType]
    assert transform(other, steps, module)["payload"] == {"text": "x"}  # pyright: ignore[reportArgumentType]


def test_drop_field_requires_a_type_to_field_list_map() -> None:
    from orchestra.canon.schema import check_migrations

    with pytest.raises(SchemaError, match="drop_field"):
        check_migrations([{"from": "1", "to": "2", "drop_field": {"gamma:note": "text"}}], "m")
