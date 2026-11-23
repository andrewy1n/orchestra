"""One workspace rule for every interface, and store_not_ready that names its real cause."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from canon_support import make_project, seed_effort

from interfaces.interfaces_support import Result, invoke
from orchestra.canon.project import Project, StoreBindingError
from orchestra.canon.workspace import Access, StoreNotReady, Workspace, not_ready_message
from orchestra.conductor.landing.land import LandGateError, land_phase
from orchestra.sessions.session_report import (
    SessionReport,
    _read_all,
)
from orchestra.tuner.authoring.observation import open_subject_store

BINDING_ERROR = "Invalid store binding JSON"
RAW_NO_STORE = "neither"

TUNER_VERBS = [
    pytest.param(["verify", "trail"], 2, id="trail"),
    pytest.param(["verify", "recheck", "--claim", "X"], 2, id="recheck"),
    pytest.param(
        ["verify", "bind", "--observation", "o", "--claim", "X", "--base", "a", "--head", "b"],
        2,
        id="bind",
    ),
    pytest.param(["verify", "unbind", "--id", "x"], 2, id="unbind"),
]


def _efforts(result: Result) -> set[str]:
    assert result.code == 0, result.err
    records = json.loads(result.out)["records"]
    return {record["subject"] for record in records}


def _world_with_effort(root: Path, effort: str) -> Path:
    project = make_project(root)
    seed_effort(project, effort)
    return project.project_root


def _corrupt_checkout(root: Path) -> Path:
    (root / ".canon").mkdir(parents=True)
    (root / ".canon" / "store-binding.json").write_text("{not json", encoding="utf-8")
    return root


def _text(result: Result) -> str:
    return result.out + result.err


def test_r6_canon_explicit_root_beats_orchestra_store(
    fresh_world: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = _world_with_effort(tmp_path / "other", "beta")
    monkeypatch.setenv("ORCHESTRA_STORE", str(other))
    result = invoke(
        "canon", ["--root", str(fresh_world), "list", "--type", "score:effort"], tmp_path
    )
    assert _efforts(result) == {"alpha"}


def test_r6_canon_explicit_root_create_writes_the_root_store_not_the_env_store(
    fresh_world: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = _world_with_effort(tmp_path / "other", "beta")
    monkeypatch.setenv("ORCHESTRA_STORE", str(other))
    created = invoke(
        "canon",
        [
            "--root",
            str(fresh_world),
            "create",
            "--type",
            "score:effort",
            "--subject",
            "gamma",
            "--payload",
            json.dumps({"goal": "g", "kind": "deliver"}),
        ],
        tmp_path,
    )
    assert created.code == 0, _text(created)
    in_root = invoke(
        "canon", ["--root", str(fresh_world), "list", "--type", "score:effort"], tmp_path
    )
    in_env = invoke("canon", ["--root", str(other), "list", "--type", "score:effort"], tmp_path)
    monkeypatch.delenv("ORCHESTRA_STORE")
    assert "gamma" in _efforts(in_root)
    assert "gamma" not in _efforts(in_env)


def test_r6_canon_canon_store_beats_orchestra_store_for_explicit_root(
    fresh_world: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chosen = make_project(tmp_path / "chosen")
    seed_effort(chosen, "beta")
    env_world = _world_with_effort(tmp_path / "env-world", "delta")
    monkeypatch.setenv("CANON_STORE", str(chosen.store_path))
    monkeypatch.setenv("ORCHESTRA_STORE", str(env_world))
    result = invoke(
        "canon", ["--root", str(fresh_world), "list", "--type", "score:effort"], tmp_path
    )
    assert _efforts(result) == {"beta"}


def test_r6_canon_without_root_still_follows_orchestra_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = _world_with_effort(tmp_path / "other", "beta")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.setenv("ORCHESTRA_STORE", str(other))
    result = invoke("canon", ["list", "--type", "score:effort"], elsewhere)
    assert _efforts(result) == {"beta"}


def _record_access(monkeypatch: pytest.MonkeyPatch) -> list[Access]:
    seen: list[Access] = []
    original = Workspace.open

    def spy(self: Workspace) -> Project:
        seen.append(self.access)
        return original(self)

    monkeypatch.setattr(Workspace, "open", spy)
    return seen


def test_r6_gate_opens_every_store_with_the_access_resolved_at_the_edge(
    fresh_world: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _record_access(monkeypatch)
    result = invoke("orchestra", ["gate", "p1"], fresh_world)
    assert result.code in (0, 1), _text(result)
    assert seen
    assert set(seen) == {Access.READ}


def test_r6_gate_with_cwd_opens_every_store_read_only(
    fresh_world: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _record_access(monkeypatch)
    result = invoke("orchestra", ["gate", "p1", "--cwd", str(fresh_world)], fresh_world)
    assert result.code in (0, 1), _text(result)
    assert seen
    assert set(seen) == {Access.READ}


def test_r6_land_phase_gate_terms_keep_the_workspace_access(
    fresh_world: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _record_access(monkeypatch)
    workspace = Workspace.resolve(fresh_world, access=Access.READ)
    with pytest.raises(LandGateError):
        land_phase(
            workspace,
            "p1",
            fresh_world,
            None,  # pyright: ignore[reportArgumentType]  # the gate refuses before the client is used
            base="main",
            remote="origin",
            poll_interval_s=0.0,
            timeout_s=0.0,
        )
    assert seen
    assert set(seen) == {Access.READ}


@pytest.mark.parametrize(("argv", "code"), TUNER_VERBS)
def test_r6_tuner_verb_with_env_store_and_bare_cwd_does_not_print_raw_open_error(
    argv: list[str],
    code: int,
    fresh_world: Path,
    bare_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ORCHESTRA_STORE", str(fresh_world))
    result = invoke("orchestra", [*argv, "--cwd", str(bare_dir)], bare_dir)
    text = _text(result)
    assert RAW_NO_STORE not in text, text
    if "store_not_ready" in text:
        assert result.code == code, text


def test_r6_tuner_trail_with_env_store_and_bare_cwd_is_success_or_store_not_ready(
    fresh_world: Path, bare_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ORCHESTRA_STORE", str(fresh_world))
    result = invoke("orchestra", ["verify", "trail", "--cwd", str(bare_dir)], bare_dir)
    if result.code == 0:
        assert isinstance(json.loads(result.out), list)
    else:
        assert result.code == 2, _text(result)
        assert "store_not_ready" in result.err


@pytest.mark.parametrize(("argv", "code"), TUNER_VERBS)
def test_r6_tuner_verb_with_uninitialised_env_store_is_store_not_ready(
    argv: list[str], code: int, bare_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    empty = tmp_path / "empty-store"
    empty.mkdir()
    monkeypatch.setenv("ORCHESTRA_STORE", str(empty))
    result = invoke("orchestra", [*argv, "--cwd", str(bare_dir)], bare_dir)
    text = _text(result)
    assert result.code == code, text
    assert "store_not_ready" in text
    assert RAW_NO_STORE not in text


def test_r8_resolve_reports_the_binding_error_for_a_corrupt_binding(tmp_path: Path) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    with pytest.raises((StoreNotReady, StoreBindingError)) as caught:
        Workspace.resolve(checkout)
    error = caught.value
    message = not_ready_message(error, checkout) if isinstance(error, StoreNotReady) else str(error)
    assert BINDING_ERROR in message


def test_r8_resolve_from_a_subdirectory_reports_the_binding_error(tmp_path: Path) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    nested = checkout / "a" / "b"
    nested.mkdir(parents=True)
    with pytest.raises((StoreNotReady, StoreBindingError)) as caught:
        Workspace.resolve(nested)
    error = caught.value
    message = not_ready_message(error, nested) if isinstance(error, StoreNotReady) else str(error)
    assert BINDING_ERROR in message


def test_r8_explicit_store_with_a_corrupt_binding_reports_the_binding_error(
    tmp_path: Path,
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    with pytest.raises((StoreNotReady, StoreBindingError)) as caught:
        Workspace.resolve(tmp_path, store=checkout).open()
    error = caught.value
    message = not_ready_message(error, tmp_path) if isinstance(error, StoreNotReady) else str(error)
    assert BINDING_ERROR in message


def test_r8_env_store_with_a_corrupt_binding_reports_the_binding_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    monkeypatch.setenv("ORCHESTRA_STORE", str(checkout))
    with pytest.raises((StoreNotReady, StoreBindingError)) as caught:
        Workspace.resolve(tmp_path).open()
    error = caught.value
    message = not_ready_message(error, tmp_path) if isinstance(error, StoreNotReady) else str(error)
    assert BINDING_ERROR in message


def test_r8_open_reports_the_binding_error_for_a_corrupt_binding(tmp_path: Path) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    with pytest.raises((StoreNotReady, StoreBindingError)) as caught:
        Workspace(root=checkout).open()
    error = caught.value
    message = not_ready_message(error, checkout) if isinstance(error, StoreNotReady) else str(error)
    assert BINDING_ERROR in message


def test_r8_resolve_without_any_store_still_names_the_searched_paths(tmp_path: Path) -> None:
    start = tmp_path / "empty"
    start.mkdir()
    with pytest.raises(StoreNotReady) as caught:
        Workspace.resolve(start)
    message = not_ready_message(caught.value, start)
    assert "searched" in message
    assert BINDING_ERROR not in message


@pytest.mark.parametrize(
    ("tool", "argv"),
    [
        pytest.param("orchestra", ["view", "plan"], id="view"),
        pytest.param("orchestra", ["handoff"], id="handoff"),
        pytest.param("orchestra", ["status"], id="status"),
        pytest.param("canon", ["list"], id="canon_list"),
        pytest.param("orchestra", ["verify", "trail"], id="tuner_trail"),
        pytest.param("orchestra", ["verify", "unbind", "--id", "x"], id="tuner_unbind"),
        pytest.param("orchestra", ["gate", "p1"], id="gate"),
    ],
)
def test_r8_interface_verb_reports_the_binding_error_for_a_corrupt_binding(
    tool: str, argv: list[str], tmp_path: Path
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    result = invoke(tool, argv, checkout)
    text = _text(result)
    assert result.code != 0, text
    assert BINDING_ERROR in text, text


def test_r8_session_report_names_the_binding_error_for_a_corrupt_binding(
    tmp_path: Path,
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    row: SessionReport = {"cwd": str(checkout)}  # pyright: ignore[reportAssignmentType]  # only cwd is read
    _, _, failures, failed = _read_all([row])
    assert failed == {str(checkout)}
    assert any(BINDING_ERROR in failure for failure in failures), failures


def test_r8_tuner_subject_store_reports_the_binding_error_for_a_corrupt_binding(
    tmp_path: Path,
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    with pytest.raises(StoreBindingError, match=BINDING_ERROR):
        open_subject_store(checkout)


def test_r8_schemas_show_in_a_checkout_with_a_corrupt_binding_reports_the_error(
    tmp_path: Path,
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    result = invoke("canon", ["schemas", "show"], checkout)
    assert result.code != 0, _text(result)
    assert BINDING_ERROR in _text(result)
    assert "composer" not in result.out


def test_r8_schemas_show_with_a_corrupt_binding_and_namespace_reports_the_error(
    tmp_path: Path,
) -> None:
    checkout = _corrupt_checkout(tmp_path / "checkout")
    result = invoke("canon", ["schemas", "show", "score"], checkout)
    assert result.code != 0, _text(result)
    assert BINDING_ERROR in _text(result)


def test_r8_schemas_show_outside_any_checkout_lists_the_installed_schemas(
    bare_dir: Path,
) -> None:
    result = invoke("canon", ["schemas", "show"], bare_dir)
    assert result.code == 0, _text(result)
    assert "composer" in json.loads(result.out)["schemas"]


def test_r8_schemas_show_in_a_healthy_checkout_lists_the_store_schemas(
    fresh_world: Path,
) -> None:
    result = invoke("canon", ["schemas", "show"], fresh_world)
    assert result.code == 0, _text(result)
    assert "score" in json.loads(result.out)["schemas"]
