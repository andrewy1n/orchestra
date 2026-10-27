"""Run a test command and read one JUnit outcome per requested id."""

from __future__ import annotations

import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Sequence
from xml.etree.ElementTree import Element


def run_tests(
    worktree: Path | str,
    test_ids: Sequence[str],
    runner: Sequence[str],
) -> dict[str, str]:
    """Start ``runner`` in ``worktree`` and return each id's JUnit outcome.

    The argv element that is exactly ``{tests}`` expands to one argument per
    id, in order. ``{report}`` inside an element becomes a temporary XML path.
    The child environment is a copy of this process with ``PYTHONPATH`` and
    ``PYTEST_ADDOPTS`` removed.
    """
    fd, report = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTEST_ADDOPTS", None)
    subprocess.run(
        _expand(runner, test_ids, report),
        cwd=worktree,
        env=env,
        check=False,
        capture_output=True,
    )
    grouped = _read_report(report)
    return {test_id: _collapse(grouped.get(test_id, ())) for test_id in test_ids}


def _expand(runner: Sequence[str], test_ids: Sequence[str], report: str) -> list[str]:
    argv: list[str] = []
    for element in runner:
        if element == "{tests}":
            argv.extend(test_ids)
        else:
            argv.append(element.replace("{report}", report))
    return argv


def _read_report(path: str) -> dict[str, list[str]]:
    if not Path(path).is_file():
        return {}
    grouped: dict[str, list[str]] = {}
    for case in ET.parse(path).getroot().iter():
        if _local(case.tag) != "testcase":
            continue
        status = _status(case)
        for key in _keys(case):
            grouped.setdefault(key, []).append(status)
    return grouped


def _collapse(statuses: Sequence[str]) -> str:
    if not statuses:
        return "not_run"
    if "errored" in statuses:
        return "errored"
    if "assertion_failed" in statuses:
        return "assertion_failed"
    if "not_run" in statuses:
        return "not_run"
    return "passed"


def _status(case: Element) -> str:
    children = {_local(child.tag) for child in case}
    if "error" in children:
        return "errored"
    if "failure" in children:
        return "assertion_failed"
    if "skipped" in children:
        return "not_run"
    return "passed"


def _keys(case: Element) -> list[str]:
    name = case.get("name")
    keys: list[str] = []
    if name is not None:
        keys.append(name)
    file_name = case.get("file")
    if not file_name:
        return keys
    joined = _joined_id(file_name, case.get("classname"), name or "")
    if joined is not None and joined not in keys:
        keys.append(joined)
    return keys


def _joined_id(file_name: str, classname: str | None, name: str) -> str | None:
    if classname is None:
        return None
    stem = PurePosixPath(file_name).with_suffix("").as_posix().replace("/", ".")
    if classname == stem:
        remainder = ""
    elif classname.startswith(stem + "."):
        remainder = classname[len(stem) + 1 :]
    else:
        return None
    segments = [part for part in remainder.split(".") if part]
    return "::".join([file_name, *segments, name])


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
