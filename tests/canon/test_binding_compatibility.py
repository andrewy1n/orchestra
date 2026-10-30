from __future__ import annotations

import json
from pathlib import Path

import pytest

from orchestra.canon.backend import open_backend
from orchestra.canon.config import new_config
from orchestra.canon.project import open_store
from orchestra.canon.sqlite_backend import SqliteBackend
from orchestra.canon.store import Store
from conftest import ALPHA, Cli


@pytest.mark.parametrize("binding_name", ["store-binding.json", "store-binding.local.json"])
@pytest.mark.parametrize(
    "local_config",
    [
        "{broken",
        "null",
        '[]',
        json.dumps({**new_config(), "format": "canon/unsupported"}),
        json.dumps({**new_config(), "backend": "unsupported"}),
        json.dumps({**new_config(), "schemas": []}),
    ],
    ids=["malformed-json", "null", "array", "unsupported-format", "unsupported-backend", "invalid-schemas"],
)
def test_global_files_binding_ignores_unrelated_local_config(
    repo: Path, cli: Cli, binding_name: str, local_config: str
) -> None:
    global_root = Path.home() / ".canon" / repo.name
    store = Store(global_root)
    store.init(new_config({"alpha": "0.1.0"}), {"alpha": json.dumps(ALPHA)})
    metadata = repo / ".canon"
    metadata.mkdir()
    (metadata / binding_name).write_text('{"store":"global"}')
    (metadata / "config.json").write_text(local_config)

    project = open_store(repo)
    assert project.store_path == global_root
    assert project.binding.location == "global"
    assert project.binding.source == str(metadata / binding_name)
    record = project.create(
        record_type="alpha:task", subject="legacy", payload={"title": "Legacy files"}
    )
    assert isinstance(open_backend(project.store_path), Store)
    assert store.read_record("alpha:task", record["id"]) == record
    assert project.validate() == []
    assert cli("validate").code == 0
    assert not (global_root / "canon.db").exists()


@pytest.mark.parametrize("binding_name", ["store-binding.json", "store-binding.local.json"])
def test_global_sqlite_binding_uses_repository_metadata(
    repo: Path, binding_name: str
) -> None:
    metadata = repo / ".canon"
    metadata.mkdir()
    (metadata / binding_name).write_text('{"store":"global"}')
    config = {**new_config({"alpha": "0.1.0"}), "backend": "sqlite"}
    backend = open_backend(metadata, config)
    backend.init(config, {"alpha": json.dumps(ALPHA)})

    project = open_store(repo)
    assert project.store_path == metadata
    assert project.binding.location == "global"
    selected = open_backend(project.store_path)
    assert isinstance(selected, SqliteBackend)
    assert selected.db_path == Path.home() / ".canon" / repo.name / "canon.db"
    assert project.validate() == []
