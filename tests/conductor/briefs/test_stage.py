from __future__ import annotations

from pathlib import Path

import pytest
from conductor_support import EFFORT, HEAD, PHASE, Cli, Phase, ready_for_verify
from conductor_support import seed as seed_phase

from orchestra.canon.project import open_store
from orchestra.conductor.phases.workflow.workflow import WorkflowRunError, step_stage

ADAPTER_TABLE = '\n[land]\nadapter = "{adapter}"\n'


def seed(store: Path, cli: Cli, *, review: bool = True, runner_check: bool = True) -> Phase:
    phase = seed_phase(store, cli, review=review, runner_check=runner_check)
    ready_for_verify(phase)
    return phase


def _stage(phase: Phase, step: str, phase_slug: str = PHASE) -> str | None:
    project = open_store(phase.store)
    return step_stage(project, project.records(), phase_slug, step)


def _use_adapter(phase: Phase, adapter: str) -> None:
    path = phase.store / "orchestra.toml"
    path.write_text(path.read_text() + ADAPTER_TABLE.format(adapter=adapter))


def _proof(phase: Phase, revision: str = HEAD) -> None:
    phase.create(
        "conductor:proof-packet",
        PHASE,
        {"phase": PHASE, "effort": EFFORT, "revision": revision, "base": "main", "kind": "claims"},
        "## Look\nl\n\n## Machine\nm\n\n## Attention\nnone\n\n## Diff\nno tree change\n",
    )


def _landing(phase: Phase, result: str, head: str = HEAD) -> None:
    phase.create(
        "conductor:landing",
        PHASE,
        {
            "phase": PHASE,
            "effort": EFFORT,
            "number": 7,
            "url": "https://github.com/o/r/pull/7",
            "head_sha": head,
            "result": result,
        },
    )


def test_verify_stage_is_analyze_while_an_acceptance_has_no_check_run(
    store: Path, cli: Cli
) -> None:
    phase = seed(store, cli, runner_check=False, review=False)

    assert _stage(phase, "verify") == "analyze"


def test_verify_stage_is_suite_when_a_required_suite_has_not_passed(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False)
    phase.set_suite_policy("required")

    assert _stage(phase, "verify") == "suite"


def test_verify_stage_is_reviewer_without_a_passing_review(store: Path, cli: Cli) -> None:
    phase = seed(store, cli, review=False)

    assert _stage(phase, "verify") == "reviewer"


def test_verify_stage_is_reviewer_when_the_latest_review_failed(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    phase.review("fail", HEAD)

    assert _stage(phase, "verify") == "reviewer"


def test_verify_stage_is_gate_while_a_gate_term_is_missing(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    phase.finding()

    assert _stage(phase, "verify") == "gate"


def test_verify_stage_is_proof_when_the_gate_holds_without_a_packet(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)

    assert _stage(phase, "verify") == "proof"


def test_verify_stage_is_proof_when_the_packet_is_for_another_head(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    _proof(phase, revision="b" * 40)

    assert _stage(phase, "verify") == "proof"


def test_verify_stage_is_none_when_every_stage_is_complete(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    _proof(phase)

    assert _stage(phase, "verify") is None


def test_stage_raises_when_the_phase_cannot_be_read(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)

    with pytest.raises(WorkflowRunError, match="no-such-phase"):
        _stage(phase, "verify", "no-such-phase")
    with pytest.raises(WorkflowRunError, match="no-such-phase"):
        _stage(phase, "land", "no-such-phase")


def test_stage_is_none_for_a_step_without_stages(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)

    assert _stage(phase, "spec") is None


def test_land_stage_is_land_without_a_landing_record(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    _proof(phase)

    assert _stage(phase, "land") == "land"


def test_land_stage_is_repair_ci_after_a_failed_github_pr_landing(store: Path, cli: Cli) -> None:
    phase = seed(store, cli)
    _proof(phase)
    _use_adapter(phase, "github-pr")
    _landing(phase, "fail")

    assert _stage(phase, "land") == "repair-ci"


def test_land_stage_stays_land_after_a_failed_landing_with_another_adapter(
    store: Path, cli: Cli
) -> None:
    phase = seed(store, cli)
    _proof(phase)
    _use_adapter(phase, "other")
    _landing(phase, "fail")

    assert _stage(phase, "land") == "land"


def test_land_stage_is_land_when_the_landing_is_not_at_the_proof_head(
    store: Path, cli: Cli
) -> None:
    phase = seed(store, cli)
    _proof(phase)
    _landing(phase, "success", head="b" * 40)

    assert _stage(phase, "land") == "land"


def test_land_stage_is_close_after_a_successful_landing_at_the_proof_head(
    store: Path, cli: Cli
) -> None:
    phase = seed(store, cli)
    _proof(phase)
    _landing(phase, "success")

    assert _stage(phase, "land") == "close"
