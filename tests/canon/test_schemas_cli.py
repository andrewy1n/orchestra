from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path

import pytest

from orchestra.canon.cli import main as canon_main

pytestmark = pytest.mark.usefixtures("site")


def _run(cwd: Path, *argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    previous = Path.cwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = canon_main(list(argv))
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 1
    finally:
        os.chdir(previous)
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def bare_dir(tmp_path: Path) -> Path:
    path = tmp_path / "bare" / "nested"
    path.mkdir(parents=True)
    return path


def _assert_store_not_ready(code: int, out: str, cwd: Path) -> None:
    assert code != 0
    payload = json.loads(out)
    assert payload["error"] == "store_not_ready"
    assert str(cwd) in payload["message"]


def test_schemas_show_without_store_lists_installed_modules(bare_dir: Path) -> None:
    code, out, err = _run(bare_dir, "schemas", "show")
    assert code == 0, out + err
    assert {"alpha", "beta"} <= set(json.loads(out)["schemas"])


def test_schemas_sync_requires_store(bare_dir: Path) -> None:
    code, out, _ = _run(bare_dir, "schemas", "sync")
    _assert_store_not_ready(code, out, bare_dir)


def test_schemas_add_requires_store(bare_dir: Path) -> None:
    code, out, _ = _run(bare_dir, "schemas", "add", "alpha")
    _assert_store_not_ready(code, out, bare_dir)


@pytest.mark.parametrize("argv", [["list"], ["validate"], ["get", "--id", "x"]])
def test_canon_no_store_reports_store_not_ready_with_searched_paths(
    bare_dir: Path, argv: list[str]
) -> None:
    code, out, _ = _run(bare_dir, *argv)
    _assert_store_not_ready(code, out, bare_dir)
