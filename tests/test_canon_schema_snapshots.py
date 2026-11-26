from __future__ import annotations

import sys
from pathlib import Path

import pytest

from orchestra.tools import CliTool, ToolError

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "check_canon_schema_snapshots.py"


class _SnapshotCheck(CliTool):
    executable = sys.executable

    def check(self) -> None:
        self._text(str(_SCRIPT))


@pytest.fixture
def schema_snapshot(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project.entry-points."canon.schemas"]\nsample = "shipped.schemas"\n',
        encoding="utf-8",
    )
    shipped = tmp_path / "shipped" / "schemas" / "sample.json"
    snapshot = tmp_path / ".canon" / "schemas" / "sample.json"
    for path in (shipped, snapshot):
        path.parent.mkdir(parents=True)
        path.write_text(
            '{"namespace": "sample", "version": "1.0.0", "types": {}}\n', encoding="utf-8"
        )
    return snapshot


def test_checked_in_schema_snapshots_match_shipped_schemas() -> None:
    _SnapshotCheck(_ROOT).check()


def test_stale_schema_snapshot_fails(tmp_path: Path, schema_snapshot: Path) -> None:
    stale = '{"namespace": "sample", "version": "1.0.0", "types": {}, "migrations": []}\n'
    schema_snapshot.write_text(stale, encoding="utf-8")

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "stale schema snapshot .canon/schemas/sample.json" in error.value.stderr
    assert schema_snapshot.read_text(encoding="utf-8") == stale


def test_missing_schema_snapshot_fails(tmp_path: Path, schema_snapshot: Path) -> None:
    schema_snapshot.unlink()

    with pytest.raises(ToolError) as error:
        _SnapshotCheck(tmp_path).check()

    assert error.value.returncode == 1
    assert "missing schema snapshot .canon/schemas/sample.json" in error.value.stderr
    assert not schema_snapshot.exists()
