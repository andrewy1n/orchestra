from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
from canon_support import create, make_project, seed_effort

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.check import run_check
from orchestra.conductor.close_batch import CloseRefused, build_batch

PROBE = 'from pathlib import Path\n\ndef test_probe():\n    assert Path("flag.txt").read_text() == "yes"\n'
NODE = "test_probe.py::test_probe"


def _commit(root: Path) -> None:
    subprocess.run(
        ["git", "-C", str(root), "add", "test_probe.py", "flag.txt", ".gitignore"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "test",
        ],
        check=True,
        capture_output=True,
    )


def setup_acceptance(
    root: Path,
    method: str,
    policy: str | None,
    *,
    frozen: bool = False,
    phase_policy: str | None = None,
) -> tuple[Project, Record]:
    project = make_project(root)
    seed_effort(project)
    if phase_policy is not None:
        phase = project.list("score:phase")[0]
        project.update(phase["id"], payload={"oracle_policy": phase_policy})
    (root / "test_probe.py").write_text(PROBE)
    (root / "flag.txt").write_text("no")
    (root / ".gitignore").write_text(".canon/\n.pytest_cache/\n__pycache__/\n")
    _commit(root)
    payload: JsonObject = {
        "method": method,
        "phase": "p1",
        "effort": "alpha",
        "verify_command": f"{sys.executable} -m pytest {NODE} -q",
    }
    if policy is not None:
        payload["oracle_policy"] = policy
    if frozen:
        payload["test_ids"] = [NODE]
        payload["oracle_hashes"] = [
            "test_probe.py:sha256:" + hashlib.sha256(PROBE.encode()).hexdigest()
        ]
    acceptance = create(project, "score:acceptance", "probe", payload)
    return project, acceptance


def run_acceptance(project: Project, acceptance: Record) -> Record:
    outcome = run_check(
        acceptance_id=acceptance["id"], cwd=project.project_root, store_root=project.project_root
    )
    assert outcome.record is not None, outcome.message
    return outcome.record


def green(project: Project, acceptance: Record) -> Record:
    (project.project_root / "flag.txt").write_text("yes")
    _commit(project.project_root)
    result = run_acceptance(project, acceptance)
    assert result["payload"]["result"] == "pass"
    return result


def close_request(acceptance: Record, passed: Record, red: Record | None = None) -> JsonObject:
    entry: JsonObject = {
        "criterion_id": acceptance["id"],
        "method": acceptance["payload"]["method"],
        "check_run_id": passed["id"],
        "result": "pass",
    }
    if red is not None:
        entry["red_check_run_id"] = red["id"]
        entry["revision"] = passed["payload"]["revision"]
    return {
        "subject": "probe",
        "effort": "alpha",
        "work_item_id": "probe-item",
        "transition": "done",
        "acceptance_ids": [acceptance["id"]],
        "criteria": [entry],
    }


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
