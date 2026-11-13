from __future__ import annotations

import json
import math
import os
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import IO

from orchestra.canon.types import JsonValue
from orchestra.conductor.suite import (
    atomic_write_suite_json,
    read_suite_json_object,
    suite_worktree_matches,
    validate_suite_request_version,
)
from orchestra.tools import CliTool, ProcessHandle, ToolError


def _required_text(request: Mapping[str, JsonValue], key: str, path: Path) -> str:
    value = request.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"invalid suite run metadata at {path}: missing {key}")
    return value


def _request_paths(request: Mapping[str, JsonValue], request_path: Path) -> dict[str, Path]:
    paths = request.get("paths")
    if not isinstance(paths, dict):
        raise RuntimeError(f"invalid suite run metadata at {request_path}: missing paths")
    names = (
        "worker_log_path",
        "output_path",
        "ready_path",
        "result_path",
        "exit_path",
        "lifecycle_path",
        "cancel_path",
    )
    parsed: dict[str, Path] = {}
    for name in names:
        value = paths.get(name)
        if not isinstance(value, str):
            raise RuntimeError(f"invalid suite run metadata at {request_path}: missing path {name}")
        parsed[name] = Path(value)
    if request_path.resolve() != request_path.parent.joinpath("request.json").resolve():
        raise RuntimeError(f"invalid suite run metadata at {request_path}: invalid request path")
    return parsed


def _write_result(
    result_path: Path,
    *,
    run_id: str,
    exit_code: int | None,
    reason: str,
    started: float,
) -> None:
    atomic_write_suite_json(
        result_path,
        {
            "run_id": run_id,
            "exit_code": exit_code,
            "reason": reason,
            "duration_s": round(max(0.0, time.monotonic() - started), 6),
        },
    )


def _timeout(request: Mapping[str, JsonValue], path: Path) -> float | None:
    value = request.get("timeout_seconds")
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"invalid suite run metadata at {path}: invalid timeout")
    timeout = float(value)
    if not math.isfinite(timeout) or timeout <= 0:
        raise RuntimeError(f"invalid suite run metadata at {path}: invalid timeout")
    return timeout


def _cancel_reason(path: Path, run_id: str) -> str | None:
    if not path.is_file():
        return None
    request = read_suite_json_object(path)
    if request.get("run_id") != run_id or request.get("reason") != "cancelled":
        raise RuntimeError(f"invalid cancellation metadata at {path}")
    return "cancelled"


def _stop_group(process: ProcessHandle) -> int | None:
    process.terminate_group()
    deadline = time.monotonic() + 5.0
    while process.group_exists and time.monotonic() < deadline:
        time.sleep(0.02)
    if process.group_exists:
        process.kill_group()
    try:
        return process.wait(timeout=1.0)
    except ToolError:
        return process.returncode


def run(request_path: Path, lifecycle_fd: int) -> int:
    request = read_suite_json_object(request_path)
    validate_suite_request_version(request, request_path)
    run_id = _required_text(request, "run_id", request_path)
    worktree = Path(_required_text(request, "worktree", request_path))
    command = _required_text(request, "command", request_path)
    start_head = _required_text(request, "start_head", request_path)
    start_diff = request.get("start_diff_sha256")
    if start_diff is not None and not isinstance(start_diff, str):
        raise RuntimeError(f"invalid suite run metadata at {request_path}: invalid starting diff")
    paths = _request_paths(request, request_path)
    timeout = _timeout(request, request_path)
    started = time.monotonic()
    exit_code: int | None = None
    reason = "startup_failed"
    output: IO[bytes] | None = None
    try:
        output = paths["output_path"].open("wb")
        atomic_write_suite_json(
            paths["ready_path"], {"run_id": run_id, "ready": True, "worker_pid": os.getpid()}
        )
        if not suite_worktree_matches(worktree, start_head, start_diff):
            reason = "revision_changed"
        else:
            process = CliTool(worktree).start_process(
                ["bash", "-lc", command],
                cwd=worktree,
                stdout=output,
            )
            reason = "completed"
            deadline = time.monotonic() + timeout if timeout is not None else None
            while True:
                code = process.returncode
                if code is not None:
                    exit_code = process.wait(timeout=0)
                    break
                cancel_reason = _cancel_reason(paths["cancel_path"], run_id)
                if cancel_reason is not None:
                    reason = cancel_reason
                    exit_code = _stop_group(process)
                    break
                if deadline is not None and time.monotonic() >= deadline:
                    reason = "timeout"
                    exit_code = _stop_group(process)
                    break
                time.sleep(0.05)
    except (OSError, RuntimeError, ToolError) as error:
        worker_log = paths["worker_log_path"]
        with worker_log.open("ab") as log:
            log.write(f"{type(error).__name__}: {error}\n".encode("utf-8", errors="replace"))
    finally:
        if output is not None:
            output.close()
        _write_result(
            paths["result_path"],
            run_id=run_id,
            exit_code=exit_code,
            reason=reason,
            started=started,
        )
        if exit_code is not None:
            paths["exit_path"].write_text(f"{exit_code}\n", encoding="utf-8")
        os.close(lifecycle_fd)
    return 0


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    try:
        lifecycle_fd = int(sys.argv[2])
    except ValueError:
        return 2
    try:
        return run(Path(sys.argv[1]), lifecycle_fd)
    except (OSError, RuntimeError, json.JSONDecodeError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
