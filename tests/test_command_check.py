from __future__ import annotations

import ast
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from orchestra.conductor import check
from orchestra.conductor.check import run_verify_command


def _imports_subprocess(path: Path) -> bool:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(a.name == "subprocess" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            return True
    return False


def test_check_runs_verify_commands_through_command(tmp_path: Path) -> None:
    assert not _imports_subprocess(Path(check.__file__))
    exit_code, duration, output, timed_out, missing = run_verify_command(
        "echo hi", cwd=tmp_path, timeout=5
    )
    assert (exit_code, output, timed_out, missing) == (0, "hi\n", False, False)
    assert duration >= 0


def test_check_reports_exit_duration_output_timeout_missing(tmp_path: Path) -> None:
    def failing(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["sh"], 3, "out\n", "err\n")

    def timing_out(
        argv: Sequence[str],
        *,
        timeout: float | None,
        env: Mapping[str, str] | None = None,
        **kw: object,
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(list(argv), timeout or 0, output=b"partial", stderr="e")

    def absent(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("sh")

    code, duration, output, timed_out, missing = run_verify_command(
        "x",
        cwd=tmp_path,
        timeout=5,
        run=failing,  # pyright: ignore[reportArgumentType]
    )
    assert (code, output, timed_out, missing) == (3, "out\nerr\n", False, False)
    assert duration >= 0

    code, _, output, timed_out, missing = run_verify_command(
        "x",
        cwd=tmp_path,
        timeout=2.5,
        run=timing_out,  # pyright: ignore[reportArgumentType]
    )
    assert code is None
    assert output == "partiale\n[orchestra check] timed out after 2.5s\n"
    assert (timed_out, missing) == (True, False)

    code, _, output, timed_out, missing = run_verify_command(
        "nope",
        cwd=tmp_path,
        timeout=5,
        run=absent,  # pyright: ignore[reportArgumentType]
    )
    assert code is None
    assert output == "[orchestra check] command not found: 'nope'\n"
    assert (timed_out, missing) == (False, True)


def test_check_reports_could_not_run_command(tmp_path: Path) -> None:
    def denied(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise PermissionError("denied")

    code, _, output, timed_out, missing = run_verify_command(
        "x",
        cwd=tmp_path,
        timeout=5,
        run=denied,  # pyright: ignore[reportArgumentType]
    )
    assert code is None
    assert output == "[orchestra check] could not run command: denied\n"
    assert (timed_out, missing) == (False, True)
