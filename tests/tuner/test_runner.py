"""Run tests and read one JUnit outcome per requested id."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from affidavit.runner import run_tests

_WRITER = """\
import json
import os
import sys
from pathlib import Path

probe = Path(sys.argv[1])
report_arg = sys.argv[2]
rest = sys.argv[3:]
marker = "--junitxml="
report = Path(report_arg[len(marker) :] if report_arg.startswith(marker) else report_arg)
probe.write_text(
    json.dumps(
        {
            "cwd": os.getcwd(),
            "rest": rest,
            "report_arg": report_arg,
            "report": str(report),
            "has_pythonpath": "PYTHONPATH" in os.environ,
            "pythonpath": os.environ.get("PYTHONPATH"),
            "has_pytest_addopts": "PYTEST_ADDOPTS" in os.environ,
            "pytest_addopts": os.environ.get("PYTEST_ADDOPTS"),
            "sentinel": os.environ.get("AFF_SENTINEL"),
        }
    )
)
if __MODE__ == "drop":
    report.unlink(missing_ok=True)
else:
    report.write_text(__XML__)
"""


def _xml(cases: list[str]) -> str:
    body = "\n".join(cases)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<testsuites>\n"
        '<testsuite name="local">\n'
        f"{body}\n"
        "</testsuite>\n"
        "</testsuites>\n"
    )


def _case(
    name: str,
    *children: str,
    file: str | None = None,
    classname: str | None = None,
) -> str:
    attrs = [f'name="{name}"']
    if classname is not None:
        attrs.append(f'classname="{classname}"')
    if file is not None:
        attrs.append(f'file="{file}"')
    opening = " ".join(attrs)
    if not children:
        return f"    <testcase {opening} />"
    inner = "\n".join(f"      {child}" for child in children)
    return f"    <testcase {opening}>\n{inner}\n    </testcase>"


def _start(
    tmp_path: Path,
    xml: str,
    *,
    name: str,
    drop: bool = False,
) -> tuple[Path, list[str], Path]:
    worktree = tmp_path / name
    worktree.mkdir()
    script = tmp_path / f"{name}-write_junit.py"
    script.write_text(
        _WRITER.replace("__MODE__", repr("drop" if drop else "write")).replace(
            "__XML__", repr(xml)
        )
    )
    probe = tmp_path / f"{name}-probe.json"
    runner = [
        sys.executable,
        str(script),
        str(probe),
        "--junitxml={report}",
        "prefix-{tests}",
        "{tests}",
    ]
    return worktree, runner, probe


def test_run_tests_returns_id_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", "/leak-pythonpath")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--leak")
    monkeypatch.setenv("AFF_SENTINEL", "kept")
    ok = "tests/test_widget.py::test_ok"
    bad = "tests/test_widget.py::test_bad"
    xml = _xml(
        [
            _case(ok, "<system-out>ok</system-out>"),
            _case(bad, '<failure message="no">assert False</failure>'),
            _case(
                "tests/test_widget.py::test_extra",
                '<error message="no">trace</error>',
            ),
        ]
    )
    ids = [ok, bad]
    worktree, runner, probe = _start(tmp_path, xml, name="outcomes")

    assert run_tests(worktree, ids, runner) == {
        ok: "passed",
        bad: "assertion_failed",
    }

    seen = json.loads(probe.read_text())
    assert seen["rest"] == ["prefix-{tests}", *ids]
    assert seen["report_arg"].startswith("--junitxml=")
    assert "{report}" not in seen["report_arg"]
    assert "{tests}" not in seen["report_arg"]
    report = Path(seen["report"])
    assert report.is_file()
    assert report.read_text() == xml
    assert Path(seen["cwd"]).resolve() == worktree.resolve()
    assert seen["has_pythonpath"] is False
    assert seen["pythonpath"] is None
    assert seen["has_pytest_addopts"] is False
    assert seen["pytest_addopts"] is None
    assert seen["sentinel"] == "kept"


def test_run_tests_maps_failure_error_skipped(tmp_path: Path) -> None:
    ids = [
        "case_fail",
        "case_error",
        "case_skip",
        "case_missing",
        "case_both",
        "case_pass",
    ]
    xml = _xml(
        [
            _case("case_fail", '<failure message="boom">trace</failure>'),
            _case("case_error", '<error message="boom">trace</error>'),
            _case("case_skip", '<skipped message="nope" />'),
            _case(
                "case_both",
                '<failure message="boom">trace</failure>',
                '<error message="boom">trace</error>',
            ),
            _case("case_pass", "<system-out>hello</system-out>"),
        ]
    )
    worktree, runner, _probe = _start(tmp_path, xml, name="mapped")
    assert run_tests(worktree, ids, runner) == {
        "case_fail": "assertion_failed",
        "case_error": "errored",
        "case_skip": "not_run",
        "case_missing": "not_run",
        "case_both": "errored",
        "case_pass": "passed",
    }

    missing_tree, missing_runner, _missing_probe = _start(
        tmp_path, "", name="absent", drop=True
    )
    assert run_tests(missing_tree, ["gone"], missing_runner) == {"gone": "not_run"}


def test_run_tests_joins_name_or_file(tmp_path: Path) -> None:
    by_name = "tests/test_plain.py::test_by_name"
    by_class = "pkg/mod.py::TestCase::Nested::test_by_file"
    by_func = "tests/test_oracle.py::test_func"
    collapse_error = "collapse-error"
    collapse_fail = "collapse-fail"
    collapse_skip = "collapse-skip"
    collapse_pass = "collapse-pass"
    xml = _xml(
        [
            _case(by_name, classname="ignored.Class"),
            _case(
                "test_by_file",
                '<failure message="boom">trace</failure>',
                file="pkg/mod.py",
                classname="pkg.mod.TestCase.Nested",
            ),
            _case(
                "test_func",
                file="tests/test_oracle.py",
                classname="tests.test_oracle",
            ),
            _case(collapse_error, '<error message="boom">trace</error>'),
            _case(collapse_error, '<failure message="boom">trace</failure>'),
            _case(collapse_fail, '<failure message="boom">trace</failure>'),
            _case(collapse_fail, '<skipped message="nope" />'),
            _case(collapse_skip, '<skipped message="nope" />'),
            _case(collapse_skip),
            _case(collapse_pass),
            _case(collapse_pass),
        ]
    )
    ids = [
        by_name,
        by_class,
        by_func,
        collapse_error,
        collapse_fail,
        collapse_skip,
        collapse_pass,
    ]
    worktree, runner, _probe = _start(tmp_path, xml, name="join")

    assert run_tests(worktree, ids, runner) == {
        by_name: "passed",
        by_class: "assertion_failed",
        by_func: "passed",
        collapse_error: "errored",
        collapse_fail: "assertion_failed",
        collapse_skip: "not_run",
        collapse_pass: "passed",
    }
