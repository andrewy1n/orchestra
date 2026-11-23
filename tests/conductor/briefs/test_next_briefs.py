from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import pytest
from conductor_support import EFFORT, HEAD, PHASE, Cli, Phase, seed

from orchestra.canon.project import open_store
from orchestra.cli import main
from orchestra.conductor.phases.workflow import workflow_review

STEPS = ("spec", "design", "tasks", "execute", "verify", "land")
ReviewedStep = Literal["spec", "design", "tasks"]
UPSTREAM_REVIEWS: dict[str, tuple[ReviewedStep, ...]] = {
    "spec": (),
    "design": ("spec",),
    "tasks": ("spec", "design"),
    "execute": ("spec", "design", "tasks"),
    "verify": ("spec", "design", "tasks"),
    "land": ("spec", "design", "tasks"),
}


def _review(phase: Phase, step: ReviewedStep) -> None:
    project = open_store(phase.store)
    workflow_review.record_step_review(
        project,
        phase=PHASE,
        step=step,
        artifact=project.resolve("score:phase", PHASE),
        authority="user-approval",
        basis="Approved in the test fixture.",
    )


def _execution_reports(phase: Phase) -> None:
    for subject in (f"{PHASE}-impl", f"verify-{PHASE}"):
        phase.create(
            "conductor:execution-report",
            subject,
            {
                "work_item": subject,
                "result": "pass",
                "verdict": "pass",
                "revision": HEAD,
                "effort": EFFORT,
            },
        )


def _proof(phase: Phase) -> None:
    phase.create(
        "conductor:proof-packet",
        PHASE,
        {"phase": PHASE, "effort": EFFORT, "revision": HEAD, "base": "main", "kind": "claims"},
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\nno tree change\n",
    )


def _specify(phase: Phase) -> None:
    project = open_store(phase.store)
    record = project.resolve("score:phase", PHASE)
    body = record.get("body") or ""
    project.update(
        record["id"],
        record_type="score:phase",
        payload={"weight": "light"},
        body=body.replace(
            "## Approach", "## Requirements\n\nR1: Preserve the contract.\n\n## Approach"
        ),
    )
    item = project.resolve("score:work-item", f"{PHASE}-impl")
    project.update(item["id"], record_type="score:work-item", payload={"requirements": ["R1"]})


def _make_ready(phase: Phase, step: str) -> None:
    _specify(phase)
    for upstream in UPSTREAM_REVIEWS[step]:
        _review(phase, upstream)
    if step in ("verify", "land"):
        _execution_reports(phase)
    if step == "land":
        _proof(phase)


def _invoke(store: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    try:
        code = main(["workflow", *args, "--store", str(store)])
    except SystemExit as exit_:
        code = exit_.code if isinstance(exit_.code, int) else 1
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _start(store: Path, capsys: pytest.CaptureFixture[str], step: str) -> str:
    _, output, _ = _invoke(store, capsys, "preview", EFFORT, PHASE, step, "--json")
    token = json.loads(output)["snapshot_token"]
    code, output, error = _invoke(
        store, capsys, "start", EFFORT, PHASE, step, "--snapshot-token", token, "--json"
    )
    assert code == 0, output + error
    return str(json.loads(output)["run"]["subject"])


def _action(
    store: Path, capsys: pytest.CaptureFixture[str], run: str, *extra: str
) -> dict[str, str]:
    code, output, error = _invoke(store, capsys, "next", run, "--json", *extra)
    assert code == 0, output + error
    (action,) = json.loads(output)["actions"]
    return action


@pytest.mark.parametrize("step", STEPS)
def test_every_ready_step_has_brief(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str], step: str
) -> None:
    phase = seed(store, cli)
    _make_ready(phase, step)
    run = _start(store, capsys, step)

    action = _action(store, capsys, run)

    assert action["step"] == step
    assert action["state"] == "ready", action
    assert action["brief"].strip()
    assert PHASE in action["brief"]
    assert "brief" not in _action(store, capsys, run, "--no-brief")


def test_blocked_step_has_no_brief_through_next(
    store: Path, cli: Cli, capsys: pytest.CaptureFixture[str]
) -> None:
    phase = seed(store, cli)
    _make_ready(phase, "design")
    run = _start(store, capsys, "tasks")

    action = _action(store, capsys, run)

    assert action["state"] == "blocked"
    assert "brief" not in action
    assert action["reason"]
