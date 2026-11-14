from __future__ import annotations

import itertools
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from orchestra.canon.project import Project, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.canon.validation import ValidationError
from orchestra.score.touches import TouchPattern, overlap, validate_touches


@pytest.fixture()
def project(store_template: Path, tmp_path: Path) -> Project:
    root = tmp_path / "repo"
    shutil.copytree(store_template, root)
    return open_store(root)


def _item(touches: JsonValue) -> Record:
    payload: JsonObject = {"touches": touches}
    return {
        "id": "work-item",
        "record_type": "score:work-item",
        "subject": "build-feature",
        "payload": payload,
        "lifecycle_state": "planned",
        "relationships": {},
        "revision": "revision",
        "recorded_at": "2026-11-14T00:00:00Z",
        "body": "",
    }


def _pattern(value: str) -> TouchPattern:
    result = validate_touches(_item([value]))
    assert result.issues == ()
    assert len(result.patterns) == 1
    return result.patterns[0]


def _seed_project(project: Project) -> None:
    project.create(
        record_type="score:effort",
        subject="workflow",
        payload={"goal": "Deliver work", "kind": "deliver"},
    )
    project.create(
        record_type="score:phase",
        subject="phase",
        payload={"title": "Phase", "ordinal": 1, "effort": "workflow"},
        body="## Problem\nPlan work.\n\n## Approach\nRun tasks.\n\n## Exit criteria\nComplete work.\n",
    )


def _work_item(
    project: Project, subject: str, touches: Sequence[JsonValue] | None = None
) -> Record:
    payload: JsonObject = {
        "title": subject,
        "phase": "phase",
        "kind": "deliver",
        "assignee": "",
        "effort": "workflow",
    }
    if touches is not None:
        payload["touches"] = list(touches)
    return project.create(
        record_type="score:work-item",
        subject=subject,
        payload=payload,
        body="## Description\nImplement the task.\n",
    )


def test_r1_optional_touches_accepts_literals_and_globs_through_project_api(
    project: Project,
) -> None:
    _seed_project(project)

    item = _work_item(
        project, "paths", ["orchestra/*.py", "tests/**", "src/name with space.py", "src/λ.py"]
    )

    assert item["payload"]["touches"] == [
        "orchestra/*.py",
        "tests/**",
        "src/name with space.py",
        "src/λ.py",
    ]
    assert project.validate() == []


def test_r2_missing_and_empty_touches_mean_unknown_scope(project: Project) -> None:
    _seed_project(project)

    missing = _work_item(project, "missing")
    empty = _work_item(project, "empty", [])

    assert "touches" not in missing["payload"]
    assert empty["payload"]["touches"] == []
    assert project.get(missing["id"]) == missing
    assert project.get(empty["id"]) == empty
    assert project.validate() == []


@pytest.mark.parametrize(
    ("declaration", "message"),
    [
        ("", "must not be empty"),
        ("/absolute", "repository-relative"),
        ("C:/drive", "drive prefix"),
        ("a\\b", "backslashes"),
        ("a//b", "empty segments"),
        ("./a", "'.' or '..'"),
        ("a/../b", "'.' or '..'"),
        ("name[ab].py", "brackets and braces"),
        ("name{a}.py", "brackets and braces"),
        ("a**b", "whole path segment"),
        ("a/**suffix", "whole path segment"),
        ("a/", "empty segments"),
    ],
)
def test_r8_invalid_declarations_name_the_task_and_declaration(
    declaration: str, message: str
) -> None:
    result = validate_touches(_item([declaration]))

    assert result.patterns == ()
    assert len(result.issues) == 1
    assert result.issues[0].task == "build-feature"
    assert result.issues[0].declaration == declaration
    assert message in result.issues[0].message


def test_r8_invalid_field_shape_names_the_task_and_value() -> None:
    result = validate_touches(_item(["src/a.py", 7]))

    assert len(result.patterns) == 1
    assert result.patterns[0].declaration == "src/a.py"
    assert result.issues[0].task == "build-feature"
    assert result.issues[0].declaration == "7"
    assert result.issues[0].message == "touches entries must be strings"


def test_r8_project_api_rejects_non_string_touches(project: Project) -> None:
    _seed_project(project)

    with pytest.raises(ValidationError, match="touches"):
        _work_item(project, "invalid", ["src/a.py", 7])


def test_overlap_handles_literals_and_globs() -> None:
    assert overlap(_pattern("src/main.py"), _pattern("src/*.py")) == "src/main.py"
    assert overlap(_pattern("src/*.py"), _pattern("tests/*.py")) is None
    assert overlap(_pattern("src/**/test_?.py"), _pattern("src/test_a.py")) == "src/test_a.py"
    assert (
        overlap(_pattern("src/**/test_?.py"), _pattern("src/unit/test_b.py"))
        == "src/unit/test_b.py"
    )


def test_overlap_finds_a_valid_nonempty_path_for_globstar_only_patterns() -> None:
    assert overlap(_pattern("**"), _pattern("*")) == "a"
    assert overlap(_pattern("a/**/b"), _pattern("a/b")) == "a/b"


def _segment_matches(pattern: str, value: str) -> bool:
    pending = [(0, 0)]
    seen: set[tuple[int, int]] = set()
    while pending:
        pattern_index, value_index = pending.pop()
        state = (pattern_index, value_index)
        if state in seen:
            continue
        seen.add(state)
        if pattern_index == len(pattern):
            if value_index == len(value):
                return True
            continue
        token = pattern[pattern_index]
        if token == "*":
            pending.append((pattern_index + 1, value_index))
            if value_index < len(value):
                pending.append((pattern_index, value_index + 1))
        elif value_index < len(value) and (token == "?" or token == value[value_index]):
            pending.append((pattern_index + 1, value_index + 1))
    return False


def _matches(pattern: str, value: str) -> bool:
    pattern_parts = pattern.split("/")
    value_parts = value.split("/")
    pending = [(0, 0)]
    seen: set[tuple[int, int]] = set()
    while pending:
        pattern_index, value_index = pending.pop()
        state = (pattern_index, value_index)
        if state in seen:
            continue
        seen.add(state)
        if pattern_index == len(pattern_parts):
            if value_index == len(value_parts):
                return True
            continue
        if pattern_parts[pattern_index] == "**":
            pending.append((pattern_index + 1, value_index))
            if value_index < len(value_parts):
                pending.append((pattern_index, value_index + 1))
        elif value_index < len(value_parts) and _segment_matches(
            pattern_parts[pattern_index], value_parts[value_index]
        ):
            pending.append((pattern_index + 1, value_index + 1))
    return False


def test_overlap_matches_bounded_exhaustive_oracle() -> None:
    atoms = ["a", "b", "*", "?", "**"]
    patterns = [
        value
        for size in (1, 2)
        for parts in itertools.product(atoms, repeat=size)
        if all("**" not in part or part == "**" for part in parts)
        for value in ["/".join(parts)]
    ]
    paths = [
        "/".join(parts)
        for size in (1, 2, 3)
        for parts in itertools.product(("a", "b", "aa", "ab", "ba", "bb"), repeat=size)
    ]

    for left, right in itertools.product(patterns, repeat=2):
        expected = any(_matches(left, path) and _matches(right, path) for path in paths)
        actual = overlap(_pattern(left), _pattern(right))
        assert (actual is not None) == expected
        if actual is not None:
            assert _matches(left, actual)
            assert _matches(right, actual)
