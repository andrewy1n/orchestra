from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orchestra.canon.config import new_config
from orchestra.canon.metadata import MetadataFiles
from orchestra.canon.modules import PATH_ENV, discover
from orchestra.tools import CliTool, ToolError

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "check_canon_schema_snapshots.py"
_NAMESPACE = "composer"


class _SnapshotCheck(CliTool):
    executable = sys.executable

    def check(self) -> None:
        self._text(str(_SCRIPT))


def _pins() -> dict[str, str]:
    return {namespace: module.version for namespace, module in discover().items()}


@pytest.fixture
def metadata(tmp_path: Path) -> MetadataFiles:
    checkout = MetadataFiles(tmp_path / ".canon")
    checkout.write_config(new_config(_pins()))
    for namespace, module in discover().items():
        checkout.write_snapshot(namespace, module.text)
    return checkout


@pytest.fixture(autouse=True)
def installed_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PATH_ENV, raising=False)


def test_checked_in_schema_snapshots_match_shipped_schemas() -> None:
    _SnapshotCheck(_ROOT).check()


def test_stale_schema_snapshot_fails(tmp_path: Path, metadata: MetadataFiles) -> None:
    snapshot = metadata.snapshot_path(_NAMESPACE)
    stale = snapshot.read_text(encoding="utf-8") + "\n"
    snapshot.write_text(stale, encoding="utf-8")

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "stale schema snapshot .canon/schemas/composer.json" in error.value.stderr
    assert snapshot.read_text(encoding="utf-8") == stale


def test_missing_schema_snapshot_fails(tmp_path: Path, metadata: MetadataFiles) -> None:
    snapshot = metadata.snapshot_path(_NAMESPACE)
    snapshot.unlink()

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "missing schema snapshot .canon/schemas/composer.json" in error.value.stderr
    assert not snapshot.exists()


def test_mismatched_schema_pin_fails(tmp_path: Path, metadata: MetadataFiles) -> None:
    metadata.write_config(new_config({**_pins(), _NAMESPACE: "0.0.0"}))

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "composer: installed schema is" in error.value.stderr
    assert "config.json pins 0.0.0" in error.value.stderr


def test_missing_schema_pin_fails(tmp_path: Path, metadata: MetadataFiles) -> None:
    pins = _pins()
    del pins[_NAMESPACE]
    metadata.write_config(new_config(pins))

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "composer: missing schema pin in .canon/config.json" in error.value.stderr


@pytest.mark.parametrize("orphan", ["snapshot", "pin"])
def test_schema_without_installed_module_fails(
    tmp_path: Path, metadata: MetadataFiles, orphan: str
) -> None:
    if orphan == "snapshot":
        metadata.write_snapshot("orphan", "{}")
    else:
        metadata.write_config(new_config({**_pins(), "orphan": "1.0.0"}))

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert (
        "orphan: schema is pinned or snapshotted but has no installed module" in error.value.stderr
    )


def test_local_schema_override_cannot_hide_stale_snapshot(
    tmp_path: Path, metadata: MetadataFiles, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = metadata.snapshot_path(_NAMESPACE)
    snapshot.write_text(snapshot.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setenv(PATH_ENV, str(snapshot))

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "stale schema snapshot .canon/schemas/composer.json" in error.value.stderr
