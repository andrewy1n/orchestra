from __future__ import annotations

from pathlib import Path

import pytest
from conductor_support import close_request, green, run_acceptance, setup_acceptance

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.close_batch import CloseRefused, build_batch


def close(project: Project, request: JsonObject) -> list[JsonObject]:
    return build_batch(request, cwd=project.project_root, store_root=project.project_root)


@pytest.mark.parametrize(
    ("method", "policy"),
    [("tdd", "none"), ("check", "none"), ("tdd", "frozen"), ("check", "frozen")],
)
def test_method_and_policy_are_independent(tmp_path: Path, method: str, policy: str) -> None:
    project, acceptance = setup_acceptance(tmp_path, method, policy, frozen=policy == "frozen")
    red = run_acceptance(project, acceptance) if method == "tdd" else None
    passed = green(project, acceptance)
    operations = close(project, close_request(acceptance, passed, red))
    assert operations[-1]["transition"] == "done"


def test_unfrozen_tdd_still_requires_red(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "tdd", "none")
    passed = green(project, acceptance)
    with pytest.raises(CloseRefused, match="red_check_run_id"):
        close(project, close_request(acceptance, passed))


@pytest.mark.parametrize("method", ["tdd", "check"])
def test_legacy_freeze_still_rejects_hash_drift(tmp_path: Path, method: str) -> None:
    project, acceptance = setup_acceptance(tmp_path, method, None, frozen=True)
    red = run_acceptance(project, acceptance) if method == "tdd" else None
    (tmp_path / "test_probe.py").write_text("def test_probe():\n    assert True\n")
    passed = green(project, acceptance)
    with pytest.raises(CloseRefused, match="hash drift"):
        close(project, close_request(acceptance, passed, red))


def test_unfrozen_legacy_tdd_needs_no_freeze(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "tdd", None)
    red = run_acceptance(project, acceptance)
    passed = green(project, acceptance)
    assert close(project, close_request(acceptance, passed, red))[-1]["transition"] == "done"


def test_missing_phase_policy_read_is_refused(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "check", None)
    passed = green(project, acceptance)

    def missing(_: str) -> Record:
        raise LookupError("phase unavailable")

    with pytest.raises(CloseRefused, match=r"phase.*unavailable"):
        build_batch(
            close_request(acceptance, passed), cwd=tmp_path, store_root=tmp_path, load_phase=missing
        )


def test_phase_frozen_default_requires_complete_metadata(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "check", None, phase_policy="frozen")
    passed = green(project, acceptance)
    with pytest.raises(CloseRefused, match="incomplete oracle freeze"):
        close(project, close_request(acceptance, passed))


def test_explicit_none_overrides_frozen_phase_default(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "check", "none", phase_policy="frozen")
    passed = green(project, acceptance)
    assert close(project, close_request(acceptance, passed))[-1]["transition"] == "done"


def test_close_refuses_none_with_freeze_metadata(tmp_path: Path) -> None:
    project, acceptance = setup_acceptance(tmp_path, "check", "none", frozen=True)
    passed = green(project, acceptance)
    with pytest.raises(CloseRefused, match="conflicts"):
        close(project, close_request(acceptance, passed))
