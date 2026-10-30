"""Logical operations preserve file storage and allow callers without a layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from orchestra.canon.backend import Backend, open_backend
from orchestra.canon.config import new_config
from orchestra.canon.project import Binding, Project
from orchestra.canon.store import Store, StoreError


def test_factory_honors_explicit_config_and_rejects_unknown_backends(
    tmp_path: Path,
) -> None:
    backend = open_backend(tmp_path, {**new_config(), "backend": "files"})
    assert isinstance(backend, Backend)
    assert isinstance(backend, Store)
    assert backend.is_absent()
    with pytest.raises(StoreError, match="unsupported store backend"):
        open_backend(tmp_path, {**new_config(), "backend": "unknown"})


def test_project_reads_with_a_backend_that_has_no_file_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend = Mock(spec=Backend)
    record: dict[str, Any] = {"id": "test", "record_type": "alpha:task"}
    backend.load_config.return_value = new_config()
    backend.iter_records.side_effect = lambda *args, **kwargs: iter([record])
    backend.change_token.return_value = "opaque"
    monkeypatch.setattr("orchestra.canon.project.open_backend", lambda root: backend)
    project = Project(tmp_path, tmp_path / "absent", Binding(None, "argument"))
    assert project.records() == [record]
    assert project.config() == new_config()
    assert project.schemas().types == {}
    assert project.change_token() == "opaque"
    assert not project.store_path.exists()


@pytest.mark.file_layout
def test_logical_import_preserves_record_history_and_operation_bytes(
    project: Project, tmp_path: Path
) -> None:
    record = project.create(
        record_type="alpha:task", subject="copy", payload={"title": "Copy"}
    )
    source = Store(project.store_path)
    source.archive_history(record)
    target = Store(tmp_path / "copy")
    target.init(new_config())
    with target.transaction():
        for snapshot in source.read_history():
            target.archive_history(snapshot)
        for record_id, ops in source.iter_chains():
            for op in ops:
                target.import_op(op["record"]["record_type"], record_id, op)
        target.import_record(record)
    assert target.read_record(record["record_type"], record["id"]) == record
    for folder in ("records", "history", "log"):
        files = {
            p.relative_to(source.root): p.read_bytes()
            for p in (source.root / folder).rglob("*")
            if p.is_file()
        }
        assert files
        assert all(
            (target.root / name).read_bytes() == data for name, data in files.items()
        )
    target.delete_history_snapshot(
        record["record_type"], record["id"], record["revision"]
    )
    assert not target.history_exists(
        record["record_type"], record["id"], record["revision"]
    )
    assert list(target.history_dir.iterdir()) == []


def test_factory_reads_the_backend_selection_from_stored_config(tmp_path: Path) -> None:
    store = Store(tmp_path)
    store.init(new_config())
    config = store.load_config()
    config["backend"] = "unknown"
    store.config_path().write_text(json.dumps(config))
    with pytest.raises(StoreError, match="unsupported store backend"):
        open_backend(tmp_path)
