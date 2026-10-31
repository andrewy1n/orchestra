from __future__ import annotations

from orchestra.canon.backend import open_backend
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project
from orchestra.canon.validation import validate_append_only_history


def test_malformed_event_id_is_collected_as_validation_error(project: Project) -> None:
    event = {
        "record_type": "alpha:log",
        "id": "bad",
        "revision": "sha256:" + "0" * 64,
    }
    errors: list[str] = []
    failure: StoreError | None = None
    try:
        validate_append_only_history(
            open_backend(project.store_path), [event], project.schemas(), errors
        )
    except StoreError as exc:
        failure = exc
    assert failure is None, f"validation raised instead of collecting errors: {failure}"
    assert any("bad" in error for error in errors)
