from __future__ import annotations

import ast
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def _project(tmp_path: Path) -> Path:
    shutil.copy2(ROOT / "pyproject.toml", tmp_path / "pyproject.toml")
    package = tmp_path / "orchestra" / "canon"
    shutil.copytree(ROOT / "orchestra" / "canon", package)
    baseline = tmp_path / ".basedpyright"
    baseline.mkdir()
    shutil.copy2(ROOT / ".basedpyright" / "baseline.json", baseline / "baseline.json")
    return tmp_path


def _typecheck(project: Path, paths: list[str]) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            "uv",
            "run",
            "--no-sync",
            "--project",
            str(ROOT),
            "--directory",
            str(project),
            "--",
            "basedpyright",
            "--project",
            str(project / "pyproject.toml"),
            "--baselinefile",
            str(project / ".basedpyright" / "baseline.json"),
            *paths,
        ],
        cwd=project,
    )


def _config() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        return tomllib.load(stream)


def _section(config: dict[str, object], *keys: str) -> dict[str, object]:
    value: object = config
    for key in keys:
        assert isinstance(value, dict)
        value = value[key]
    assert isinstance(value, dict)
    return value


def _assert_canon_exports(*names: str) -> None:
    module_path = ROOT / "orchestra" / "canon" / "__init__.py"
    assert module_path.is_file(), "orchestra.canon module is missing"
    source = module_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    exports: set[str] = set()
    for statement in module.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.add(statement.name)
        elif isinstance(statement, ast.ImportFrom):
            exports.update(alias.asname or alias.name for alias in statement.names)
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            exports.update(target.id for target in targets if isinstance(target, ast.Name))
    missing = set(names) - exports
    assert not missing, f"orchestra.canon does not export: {', '.join(sorted(missing))}"


def test_r1_json_value_alias_accepts_recursive_json(tmp_path: Path) -> None:
    _assert_canon_exports("JsonValue")
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r1.py"
    probe.write_text(
        "from orchestra.canon import JsonValue\n"
        'value: JsonValue = {"items": [None, True, 3, 2.5, "x", {"nested": []}]}\n',
        encoding="utf-8",
    )
    result = _typecheck(project, [str(probe)])
    assert result.returncode == 0, result.stdout


def test_r2_json_object_alias_accepts_json_members(tmp_path: Path) -> None:
    _assert_canon_exports("JsonObject")
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r2.py"
    probe.write_text(
        "from orchestra.canon import JsonObject\n"
        'value: JsonObject = {"nested": [None, True, 1, 1.5, "x"]}\n',
        encoding="utf-8",
    )
    result = _typecheck(project, [str(probe)])
    assert result.returncode == 0, result.stdout


def test_r3_record_typed_dict_accepts_record_and_rejects_non_json(tmp_path: Path) -> None:
    _assert_canon_exports("Record")
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r3.py"
    valid = (
        "from orchestra.canon import Record\n"
        'record: Record = {"id": "r1", "record_type": "task", "subject": "s", '
        '"payload": {"values": [None, True, 1, 1.5, "x"]}, "lifecycle_state": "open", '
        '"relationships": {}, "revision": "", "body": "", "recorded_at": "now"}\n'
    )
    probe.write_text(valid, encoding="utf-8")
    accepted = _typecheck(project, [str(probe)])
    assert accepted.returncode == 0, accepted.stdout
    probe.write_text(
        valid + 'bad_record: Record = {**record, "payload": {"bad": object()}}\n', encoding="utf-8"
    )
    rejected = _typecheck(project, [str(probe)])
    assert rejected.returncode != 0, rejected.stdout
    assert "reportAssignmentType" in rejected.stdout, rejected.stdout
    assert str(probe) in rejected.stdout, rejected.stdout


def test_r4_record_payload_has_json_object_result(tmp_path: Path) -> None:
    _assert_canon_exports("JsonObject", "Record", "record_payload")
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r4.py"
    probe.write_text(
        "from orchestra.canon import JsonObject, Record, record_payload\n"
        "def payload(record: Record) -> JsonObject:\n"
        "    return record_payload(record)\n",
        encoding="utf-8",
    )
    result = _typecheck(project, [str(probe)])
    assert result.returncode == 0, result.stdout


def test_r5_get_string_helper_cases(tmp_path: Path) -> None:
    _assert_canon_exports("get_string")
    canon = importlib.import_module("orchestra.canon")
    helper = getattr(canon, "get_string", None)
    assert callable(helper), "orchestra.canon.get_string must be callable"
    assert helper({"key": "value"}, "key") == "value"
    assert helper({}, "key") is None
    assert helper({"key": 3}, "key") is None
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r5.py"
    probe.write_text(
        "from orchestra.canon import JsonObject, get_string\n"
        "def value(obj: JsonObject) -> str | None:\n"
        '    return get_string(obj, "key")\n',
        encoding="utf-8",
    )
    result = _typecheck(project, [str(probe)])
    assert result.returncode == 0, result.stdout


def test_r6_strict_includes_canon() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    assert "orchestra/canon" in basedpyright.get("strict", [])


def test_r7_strict_includes_composer() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    assert "orchestra/composer" in basedpyright.get("strict", [])


def test_r8_strict_includes_store() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    assert "orchestra/store.py" in basedpyright.get("strict", [])


def test_r9_canon_explicit_any_is_error() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    environments = basedpyright.get("executionEnvironments", [])
    assert isinstance(environments, list)
    assert any(
        "orchestra/canon" in entry.get("root", "") and entry.get("reportExplicitAny") == "error"
        for entry in environments
    )


def test_r10_composer_explicit_any_is_error() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    environments = basedpyright.get("executionEnvironments", [])
    assert isinstance(environments, list)
    assert any(
        "orchestra/composer" in entry.get("root", "") and entry.get("reportExplicitAny") == "error"
        for entry in environments
    )


def test_r11_store_explicit_any_is_error() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    environments = basedpyright.get("executionEnvironments", [])
    assert isinstance(environments, list)
    assert any(
        "orchestra/store.py" in entry.get("root", "") and entry.get("reportExplicitAny") == "error"
        for entry in environments
    )


def test_r12_ignore_without_rule_is_error() -> None:
    basedpyright = _section(_config(), "tool", "basedpyright")
    assert basedpyright.get("reportIgnoreCommentWithoutRule") == "error"


def test_r13_ruff_bans_cast() -> None:
    lint = _section(_config(), "tool", "ruff", "lint")
    enabled = set(lint.get("select", [])) | set(lint.get("extend-select", []))
    assert "TID251" in enabled
    tidy_imports = lint.get("flake8-tidy-imports", {})
    assert isinstance(tidy_imports, dict)
    banned_api = tidy_imports.get("banned-api", {})
    assert isinstance(banned_api, dict)
    assert "typing.cast" in banned_api


def test_r15_baseline_has_no_converted_path_entries() -> None:
    baseline = json.loads((ROOT / ".basedpyright" / "baseline.json").read_text(encoding="utf-8"))
    files = baseline["files"]
    excluded = ("orchestra/canon/", "orchestra/composer/", "orchestra/store.py")
    offending = [path for path in files if path.removeprefix("./").startswith(excluded)]
    assert offending == []


def test_r16_unannotated_parameter_fails_strict_canon(tmp_path: Path) -> None:
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r16.py"
    probe.write_text("def broken(value):\n    return value\n", encoding="utf-8")
    result = _typecheck(project, [str(probe)])
    assert result.returncode != 0, result.stdout
    assert "reportUnknownParameterType" in result.stdout, result.stdout
    assert str(probe) in result.stdout, result.stdout


def test_r17_explicit_any_fails_canon(tmp_path: Path) -> None:
    project = _project(tmp_path)
    probe = project / "orchestra" / "canon" / "probe_r17.py"
    probe.write_text("from typing import Any\nvalue: Any = 1\n", encoding="utf-8")
    result = _typecheck(project, [str(probe)])
    assert result.returncode != 0, result.stdout
    assert "reportExplicitAny" in result.stdout, result.stdout
    assert str(probe) in result.stdout, result.stdout


def test_r18_explicit_any_outside_strict_scope_passes(tmp_path: Path) -> None:
    project = _project(tmp_path)
    dashboard = project / "dashboard"
    dashboard.mkdir()
    probe = dashboard / "probe_r18.py"
    probe.write_text("from typing import Any\nvalue: Any = 1\n", encoding="utf-8")
    result = _typecheck(project, [str(probe)])
    assert result.returncode == 0, result.stdout


def test_r19_cast_call_fails_ruff(tmp_path: Path) -> None:
    probe = tmp_path / "probe_r19.py"
    probe.write_text(
        "import typing\n\nvalue = typing.cast(str, object())\n",
        encoding="utf-8",
    )
    result = _run(
        [
            "uvx",
            "ruff@0.13.1",
            "check",
            "--config",
            str(ROOT / "pyproject.toml"),
            str(probe),
        ],
        cwd=tmp_path,
    )
    assert result.returncode != 0, result.stdout
    assert "TID251" in result.stdout, result.stdout
    assert probe.name in result.stdout, result.stdout


def test_r20_agents_state_type_standard() -> None:
    instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    assert "annotate all new code" in instructions
    assert "reportexplicitany" in instructions or "explicit `any`" in instructions
    assert "typing.cast" in instructions or "no `cast`" in instructions
    assert "ignore comment" in instructions and "rule" in instructions
