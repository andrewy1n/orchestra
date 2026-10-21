"""Tests for se-workflow close-batch -- the batch builder behind the
verify-work `close` procedure.

The pure `build_batch` tests exercise the refusal policy directly; the
`test_end_to_end_*` tests drive the real `adaptive-artifacts` CLI (via the
shared `cli`/`resolved_contract` fixtures) to prove the emitted NDJSON is
actually accepted by `apply` and lands the record shape the skill promises.

For tdd/check, check-runs are runner-produced ahead of close; the batch
must not invent them.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import helpers as h
from conftest import REPO_ROOT
from orchestra import close_batch

CLI = REPO_ROOT / "bin" / "orchestra"

RUNNER = "orchestra"
ORCHESTRA_RUNNER = "orchestra"


def _tdd_pass_only_entry(**extra):
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-cr",
        "result": "pass",
    }
    entry.update(extra)
    return entry


def _tdd_with_dirty_red(**extra):
    """Valid fail→pass via dirty red + diff_sha256 (no git ancestry needed)."""
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": "deadbeef",
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": "dirty",
        "red_runner": RUNNER,
        "red_diff_sha256": "a" * 64,
    }
    entry.update(extra)
    return entry


def _request(**overrides):
    base = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": "rec-er",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [_tdd_with_dirty_red()],
        "finding": None,
    }
    base.update(overrides)
    return base


def _matching_loader(request: dict):
    """Echo request-carried check-run fields as store records (unit-test hook)."""
    by_id: dict[str, dict] = {}
    for entry in request.get("criteria", []):
        cid = entry.get("check_run_id")
        if cid:
            payload = {
                "criterion_id": entry["criterion_id"],
                "result": entry.get("result"),
                "runner": entry.get("runner", RUNNER),
                "revision": entry.get("revision", "deadbeef"),
                "method": entry.get("method"),
            }
            by_id[cid] = {"id": cid, "payload": payload}
        red_id = entry.get("red_check_run_id")
        if red_id:
            red_payload = {
                "criterion_id": entry["criterion_id"],
                "result": entry.get("red_result", "fail"),
                "runner": entry.get("red_runner", RUNNER),
                "revision": entry.get("red_revision", "dirty"),
                "method": "tdd",
            }
            if "red_diff_sha256" in entry:
                red_payload["diff_sha256"] = entry["red_diff_sha256"]
            by_id[red_id] = {"id": red_id, "payload": red_payload}

    def load(check_run_id: str) -> dict:
        if check_run_id not in by_id:
            raise LookupError(check_run_id)
        return by_id[check_run_id]

    return load


def _build(request: dict, *, cwd: Path | None = None, load_check_run=None, **kwargs):
    """build_batch with a matching store loader unless one is supplied."""
    loader = load_check_run
    if loader is None and request.get("transition") == "done":
        loader = _matching_loader(request)
    return close_batch.build_batch(
        request, cwd=cwd, load_check_run=loader, **kwargs
    )


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _ancestry_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """Temp git repo with parent (red) → child (green) commits."""
    repo = tmp_path / "ancestry-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "f.txt").write_text("red\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-m", "red")
    red_sha = _git(repo, "rev-parse", "HEAD")
    (repo / "f.txt").write_text("green\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-m", "green")
    green_sha = _git(repo, "rev-parse", "HEAD")
    return repo, red_sha, green_sha


def _run_script(
    request: dict,
    tmp_path: Path,
    *,
    cwd: Path | None = None,
    process_cwd: Path | None = None,
) -> tuple[subprocess.CompletedProcess, Path]:
    input_path = tmp_path / "close-request.json"
    input_path.write_text(json.dumps(request))
    out_path = tmp_path / "close-batch.ndjson"
    cmd = [sys.executable, str(CLI), "close-batch", "--input", str(input_path), "--out", str(out_path)]
    if cwd is not None:
        cmd.extend(["--cwd", str(cwd)])
    # process_cwd is the primary checkout (store discovery); --cwd is code HEAD.
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(process_cwd) if process_cwd is not None else None,
    )
    return result, out_path


def _manual_request(**overrides):
    base = {
        "subject": "task-1",
        "effort": "effort-1",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": "rec-er",
        "acceptance_ids": ["rec-ac1"],
        "criteria": [
            {
                "criterion_id": "rec-ac1",
                "method": "manual",
                "result": "pass",
                "revision": "abc123",
                "signed_by": "",
            }
        ],
        "finding": None,
    }
    base.update(overrides)
    return base


# -- build_batch: pure policy tests -----------------------------------


def test_all_pass_runner_batch_is_only_the_transition():
    ops = _build(_request())
    assert [op["op"] for op in ops] == ["update"]
    assert ops[-1] == {
        "op": "update",
        "type": "project:work-item",
        "id": "rec-wi",
        "transition": "done",
        "expected_revision": "@current",
    }


def test_manual_pass_batch_is_one_check_run_then_the_transition():
    ops = _build(_manual_request())
    assert [op["op"] for op in ops] == ["create", "update"]
    check_run = ops[0]
    assert check_run["type"] == "project:check-run"
    assert check_run["subject"] == "task-1"
    assert check_run["payload"]["result"] == "pass"
    assert check_run["payload"]["method"] == "manual"
    assert check_run["rel"] == ["informed_by:rec-ac1", "informed_by:rec-er"]


def test_refuses_done_with_failing_criterion_and_no_finding():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "fail",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRefused):
        _build(request)


def test_refuses_done_with_a_criterion_never_checked_at_all():
    request = _request(
        acceptance_ids=["rec-ac1", "rec-ac2"],
        criteria=[_tdd_with_dirty_red()],
    )
    with pytest.raises(close_batch.CloseRefused):
        _build(request)


def test_withdrawn_does_not_require_a_finding_for_a_failing_criterion():
    request = _request(
        transition="withdrawn",
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "fail",
            }
        ],
    )
    ops = _build(request)
    assert ops[-1]["transition"] == "withdrawn"


def test_finding_permits_the_close_and_needs_is_forced_to_human():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "fail",
            }
        ],
        finding={
            "claim": "closed with a known gap",
            "basis": "deferred deliberately",
            "invalidated_when": "when re-verified",
            "needs": "none",  # deliberately wrong -- the script must override this
            "body": "## Evidence\n\nx\n\n## Consequence\n\ny\n\n## Follow-up\n\nz",
        },
    )
    ops = _build(request)
    finding_op = next(op for op in ops if op["type"] == "project:finding")
    assert finding_op["payload"]["needs"] == "human"
    assert ops[-1]["op"] == "update" and ops[-1]["transition"] == "done"
    assert not any(op.get("type") == "project:check-run" for op in ops)


def test_no_execution_report_omits_the_second_informed_by_on_manual():
    ops = _build(_manual_request(execution_report_id=None))
    assert ops[0]["rel"] == ["informed_by:rec-ac1"]


def test_criteria_entry_outside_acceptance_ids_is_malformed():
    request = _request(
        criteria=[_tdd_with_dirty_red(criterion_id="rec-not-active")]
    )
    with pytest.raises(close_batch.CloseRequestError):
        _build(request)


def test_missing_top_level_field_is_malformed_not_refused():
    request = _request()
    del request["work_item_id"]
    with pytest.raises(close_batch.CloseRequestError):
        _build(request)


def test_invented_tdd_with_signed_by_is_malformed():
    request = _request(criteria=[_tdd_with_dirty_red(signed_by="agent")])
    with pytest.raises(close_batch.CloseRequestError, match="signed_by"):
        _build(request)


def test_invented_check_with_revision_is_malformed():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
                "revision": "abc123",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRequestError, match="revision"):
        _build(request)


# -- CLI wrapper: exit codes and output-file behavior ------------------


def test_cli_refusal_exits_2_prints_why_and_writes_no_file(tmp_path):
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "fail",
            }
        ]
    )
    result, out_path = _run_script(request, tmp_path)
    assert result.returncode == 2
    assert "rec-ac1" in result.stderr
    assert not out_path.exists()


def test_cli_fabricated_check_run_id_exits_2_and_writes_no_file(tmp_path):
    """CLI path uses the real store; fabricated ids refuse with no batch."""
    result, out_path = _run_script(_request(), tmp_path)
    assert result.returncode == 2
    assert not out_path.exists()


def test_cli_malformed_json_exits_1(tmp_path):
    input_path = tmp_path / "close-request.json"
    input_path.write_text("{not json")
    out_path = tmp_path / "close-batch.ndjson"
    result = subprocess.run(
        [sys.executable, str(CLI), "close-batch", "--input", str(input_path), "--out", str(out_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert not out_path.exists()


# -- end to end against the real CLI -----------------------------------


def _build_work_item_family(cli, defs, subject: str, effort: str, *, method: str = "tdd"):
    phase = h.create_generic_record(cli, defs, "project:phase", extra_payload={"effort": effort})
    work_item = h.create_generic_record(
        cli,
        defs,
        "project:work-item",
        subject=subject,
        extra_payload={"effort": effort, "phase": phase["subject"], "kind": "deliver"},
    )
    work_item = h._apply_transition(
        cli, defs["project:work-item"], "project:work-item", work_item, "in_progress"
    )
    acceptance = h.create_generic_record(
        cli,
        defs,
        "project:acceptance",
        subject=subject,
        extra_payload={"effort": effort, "phase": phase["subject"], "method": method},
    )
    assignment = h.create_generic_record(
        cli,
        defs,
        "project:assignment",
        subject=subject,
        extra_payload={"effort": effort, "work_item": subject},
    )
    execution_report = h.create_generic_record(
        cli,
        defs,
        "project:execution-report",
        subject=subject,
        extra_payload={
            "work_item": subject,
            "assignment": assignment["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": "deadbeef",
        },
    )
    return work_item, acceptance, execution_report


def _seed_runner_check_run(
    cli,
    defs,
    subject,
    acceptance,
    execution_report,
    *,
    result="pass",
    revision="deadbeef",
    diff_sha256=None,
    body=None,
    failing_node_ids=None,
):
    payload = {
        "criterion_id": acceptance["id"],
        "revision": revision,
        "result": result,
        "effort": acceptance["payload"]["effort"],
        "method": acceptance["payload"]["method"],
        "signed_by": "",
        "runner": "orchestra",
    }
    if diff_sha256 is not None:
        payload["diff_sha256"] = diff_sha256
    if failing_node_ids is not None:
        payload["failing_node_ids"] = failing_node_ids
    args = [
        "create",
        "--type",
        "project:check-run",
        "--subject",
        subject,
        "--payload",
        json.dumps(payload),
        "--rel",
        f"informed_by:{acceptance['id']}",
        "--rel",
        f"informed_by:{execution_report['id']}",
    ]
    check_body = body if body is not None else h.generic_body(defs["project:check-run"])
    if check_body:
        args.extend(["--body", check_body])
    created = cli(*args)
    assert created.returncode == 0, created.stdout + created.stderr
    return json.loads(created.stdout)["record"]


def test_end_to_end_all_pass_closes_the_work_item_to_done(
    cli, store, resolved_contract, tmp_path
):
    defs = h.record_defs_by_id(resolved_contract)
    subject = "demo-close-task"
    effort = "demo-effort"
    work_item, acceptance, execution_report = _build_work_item_family(cli, defs, subject, effort)
    red_digest = "b" * 64
    red_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="fail",
        revision="dirty",
        diff_sha256=red_digest,
    )
    green_cr = _seed_runner_check_run(cli, defs, subject, acceptance, execution_report)

    request = {
        "subject": subject,
        "effort": effort,
        "work_item_id": work_item["id"],
        "transition": "done",
        "execution_report_id": execution_report["id"],
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "tdd",
                "check_run_id": green_cr["id"],
                "result": "pass",
                "revision": "deadbeef",
                "red_check_run_id": red_cr["id"],
                "red_result": "fail",
                "red_revision": "dirty",
                "red_runner": RUNNER,
                "red_diff_sha256": red_digest,
            }
        ],
        "finding": None,
    }
    result, out_path = _run_script(request, tmp_path, process_cwd=store)
    assert result.returncode == 0, result.stderr

    apply_result = cli("apply", str(out_path))
    assert apply_result.returncode == 0, apply_result.stdout + apply_result.stderr
    applied = json.loads(apply_result.stdout)
    assert applied["ok"] is True
    assert applied["applied"] == 1
    assert applied["failed"] == 0

    final_work_item = json.loads(cli("get", "--type", "project:work-item", "--id", work_item["id"]).stdout)
    assert final_work_item["lifecycle_state"] == "done"

    check_runs = json.loads(
        cli("list", "--type", "project:check-run", "--subject", subject, "--full").stdout
    )["records"]
    assert len(check_runs) == 2
    by_id = {cr["id"]: cr for cr in check_runs}
    assert by_id[green_cr["id"]]["payload"]["result"] == "pass"
    assert by_id[green_cr["id"]]["payload"].get("runner") == "orchestra"
    assert by_id[red_cr["id"]]["payload"]["result"] == "fail"


def test_end_to_end_refusal_leaves_the_work_item_in_progress(
    cli, store, resolved_contract, tmp_path
):
    defs = h.record_defs_by_id(resolved_contract)
    subject = "demo-refuse-task"
    effort = "demo-effort"
    work_item, acceptance, execution_report = _build_work_item_family(
        cli, defs, subject, effort, method="check"
    )
    runner_cr = _seed_runner_check_run(
        cli, defs, subject, acceptance, execution_report, result="fail"
    )

    request = {
        "subject": subject,
        "effort": effort,
        "work_item_id": work_item["id"],
        "transition": "done",
        "execution_report_id": execution_report["id"],
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "check",
                "check_run_id": runner_cr["id"],
                "result": "fail",
            }
        ],
        "finding": None,
    }
    result, out_path = _run_script(request, tmp_path, process_cwd=store)
    assert result.returncode == 2
    assert not out_path.exists()

    final_work_item = json.loads(cli("get", "--type", "project:work-item", "--id", work_item["id"]).stdout)
    assert final_work_item["lifecycle_state"] == "in_progress"


def test_end_to_end_failing_criterion_with_finding_closes_and_surfaces_needs_human(
    cli, store, resolved_contract, tmp_path
):
    defs = h.record_defs_by_id(resolved_contract)
    subject = "demo-deferred-task"
    effort = "demo-effort"
    work_item, acceptance, execution_report = _build_work_item_family(
        cli, defs, subject, effort, method="check"
    )
    runner_cr = _seed_runner_check_run(
        cli, defs, subject, acceptance, execution_report, result="fail"
    )

    request = {
        "subject": subject,
        "effort": effort,
        "work_item_id": work_item["id"],
        "transition": "done",
        "execution_report_id": execution_report["id"],
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "check",
                "check_run_id": runner_cr["id"],
                "result": "fail",
            }
        ],
        "finding": {
            "claim": f"{subject} closed done with an unmet or unverified criterion",
            "basis": "live verification deliberately deferred",
            "invalidated_when": "the criterion is re-run and passes",
            "body": "## Evidence\n\nthe check-run above\n\n## Consequence\n\nunverified in prod\n\n## Follow-up\n\nre-run before next release",
        },
    }
    result, out_path = _run_script(request, tmp_path, process_cwd=store)
    assert result.returncode == 0, result.stderr

    apply_result = cli("apply", str(out_path))
    assert apply_result.returncode == 0, apply_result.stdout + apply_result.stderr
    applied = json.loads(apply_result.stdout)
    assert applied["applied"] == 2

    final_work_item = json.loads(cli("get", "--type", "project:work-item", "--id", work_item["id"]).stdout)
    assert final_work_item["lifecycle_state"] == "done"

    findings = json.loads(
        cli("list", "--type", "project:finding", "--subject", subject, "--full").stdout
    )["records"]
    assert len(findings) == 1
    assert findings[0]["payload"]["needs"] == "human"


# -- red-first gate (tdd done) ----------------------------------------


def test_red_first_pass_only_refuses_and_names_criterion():
    request = _request(criteria=[_tdd_pass_only_entry()])
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request)
    assert "red" in str(excinfo.value).lower()


def test_red_first_pass_only_cli_exits_2(tmp_path):
    request = _request(criteria=[_tdd_pass_only_entry()])
    result, out_path = _run_script(request, tmp_path)
    assert result.returncode == 2
    assert "rec-ac1" in result.stderr
    assert not out_path.exists()


def test_red_first_request_accepts_fail_then_pass_with_dirty_red():
    ops = _build(_request(criteria=[_tdd_with_dirty_red()]))
    assert ops[-1]["transition"] == "done"


def test_red_first_request_refuses_non_runner_red():
    request = _request(criteria=[_tdd_with_dirty_red(red_runner="hand-authored")])
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request)
    assert "runner" in str(excinfo.value).lower()


def test_red_first_request_refuses_red_result_not_fail():
    request = _request(criteria=[_tdd_with_dirty_red(red_result="pass")])
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request)
    assert "fail" in str(excinfo.value).lower()


def test_red_first_request_resolves_red_from_store_loader():
    """Red-first uses the injectable store loader (production path is aa.get)."""
    request = _request(criteria=[_tdd_with_dirty_red()])
    seen: list[str] = []

    def tracking_loader(check_run_id: str) -> dict:
        seen.append(check_run_id)
        return _matching_loader(request)(check_run_id)

    ops = _build(request, load_check_run=tracking_loader)
    assert ops[-1]["transition"] == "done"
    assert "rec-runner-green" in seen
    assert "rec-runner-red" in seen


def test_red_first_order_accepts_when_green_descends_from_red(tmp_path):
    repo, red_sha, green_sha = _ancestry_repo(tmp_path)
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": green_sha,
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": red_sha,
        "red_runner": RUNNER,
    }
    ops = _build(_request(criteria=[entry]), cwd=repo)
    assert ops[-1]["transition"] == "done"


def test_red_first_order_accepts_equal_sha(tmp_path):
    repo, red_sha, _green_sha = _ancestry_repo(tmp_path)
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": red_sha,
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": red_sha,
        "red_runner": RUNNER,
    }
    ops = _build(_request(criteria=[entry]), cwd=repo)
    assert ops[-1]["transition"] == "done"


def test_red_first_order_refuses_when_green_is_ancestor_of_red(tmp_path):
    """Wrong order: green SHA is parent of red (green does not descend from red)."""
    repo, red_sha, green_sha = _ancestry_repo(tmp_path)
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": red_sha,  # older
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": green_sha,  # newer — not an ancestor of red_sha
        "red_runner": RUNNER,
    }
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1"):
        _build(_request(criteria=[entry]), cwd=repo)


def test_red_first_order_refuses_non_ancestor_on_divergent_history(tmp_path):
    repo, red_sha, green_sha = _ancestry_repo(tmp_path)
    _git(repo, "checkout", "-b", "other", red_sha)
    (repo / "f.txt").write_text("other\n")
    _git(repo, "add", "f.txt")
    _git(repo, "commit", "-m", "side")
    side_sha = _git(repo, "rev-parse", "HEAD")
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": green_sha,
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": side_sha,
        "red_runner": RUNNER,
    }
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1"):
        _build(_request(criteria=[entry]), cwd=repo)


def test_red_first_order_dirty_red_requires_nonempty_diff_sha256():
    request = _request(
        criteria=[_tdd_with_dirty_red(red_diff_sha256="")]
    )
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request)
    assert "diff_sha256" in str(excinfo.value)


def test_red_first_order_dirty_red_without_digest_refused():
    entry = _tdd_with_dirty_red()
    del entry["red_diff_sha256"]
    # Store red is dirty without digest when request omits red_diff_sha256.
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1"):
        _build(_request(criteria=[entry]))


def test_red_first_escape_permits_tdd_done_without_red_and_forces_human():
    request = _request(
        criteria=[_tdd_pass_only_entry()],
        finding={
            "claim": "closing without red-first evidence for rec-ac1",
            "basis": "refactor-only change; prior red unavailable",
            "invalidated_when": "a runner fail then pass is recorded",
            "needs": "none",
            "body": "## Evidence\n\nno red\n\n## Consequence\n\ngap\n\n## Follow-up\n\nre-verify",
        },
    )
    ops = _build(request)
    finding_op = next(op for op in ops if op["type"] == "project:finding")
    assert finding_op["payload"]["needs"] == "human"
    assert ops[-1]["transition"] == "done"


def test_red_first_other_methods_check_closes_without_red_check_run_id():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
            }
        ]
    )
    ops = _build(request)
    assert ops[-1]["transition"] == "done"
    assert "red_check_run_id" not in request["criteria"][0]


def test_red_first_other_methods_manual_closes_without_red_check_run_id():
    ops = _build(_manual_request())
    assert ops[-1]["transition"] == "done"
    assert [op["op"] for op in ops] == ["create", "update"]


# -- store authority (claim-witnesses) ---------------------------------


def test_store_authority_refuses_fabricated_check_run_id():
    request = _request(criteria=[_tdd_with_dirty_red()])

    def missing(_cid: str) -> dict:
        raise LookupError("fabricated")

    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request, load_check_run=missing)
    assert "not found" in str(excinfo.value).lower() or "fabricated" in str(excinfo.value).lower()


def test_store_authority_refuses_fabricated_red_check_run_id():
    request = _request(criteria=[_tdd_with_dirty_red()])
    base = _matching_loader(request)

    def green_only(cid: str) -> dict:
        if cid == "rec-runner-red":
            raise LookupError(cid)
        return base(cid)

    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build(request, load_check_run=green_only)
    assert "red" in str(excinfo.value).lower()


def test_store_authority_mismatch_result_refuses():
    request = _request(criteria=[_tdd_with_dirty_red()])
    base = _matching_loader(request)

    def wrong_result(cid: str) -> dict:
        rec = base(cid)
        if cid == "rec-runner-green":
            rec = {
                "id": cid,
                "payload": {**rec["payload"], "result": "fail"},
            }
        return rec

    with pytest.raises(close_batch.CloseRefused, match="mismatch") as excinfo:
        _build(request, load_check_run=wrong_result)
    assert "result" in str(excinfo.value).lower()


def test_store_authority_mismatch_revision_refuses():
    request = _request(criteria=[_tdd_with_dirty_red()])
    base = _matching_loader(request)

    def wrong_revision(cid: str) -> dict:
        rec = base(cid)
        if cid == "rec-runner-green":
            rec = {
                "id": cid,
                "payload": {**rec["payload"], "revision": "otherrev"},
            }
        return rec

    with pytest.raises(close_batch.CloseRefused, match="mismatch") as excinfo:
        _build(request, load_check_run=wrong_revision)
    assert "revision" in str(excinfo.value).lower()


def test_cli_store_authority_fabricated_writes_no_batch(tmp_path):
    result, out_path = _run_script(_request(), tmp_path)
    assert result.returncode == 2
    assert not out_path.exists()


def test_red_store_resolves_and_accepts_dirty_red():
    ops = _build(_request(criteria=[_tdd_with_dirty_red()]))
    assert ops[-1]["transition"] == "done"


def test_red_store_refuses_when_store_red_is_not_fail():
    request = _request(criteria=[_tdd_with_dirty_red()])
    base = _matching_loader(request)

    def red_pass(cid: str) -> dict:
        rec = base(cid)
        if cid == "rec-runner-red":
            # Request still says fail — mismatch on result.
            return {
                "id": cid,
                "payload": {**rec["payload"], "result": "pass"},
            }
        return rec

    with pytest.raises(close_batch.CloseRefused, match="rec-ac1"):
        _build(request, load_check_run=red_pass)


def test_dirty_green_refuses_when_red_is_sha(tmp_path):
    repo, red_sha, _green_sha = _ancestry_repo(tmp_path)
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        "revision": "dirty",
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": red_sha,
        "red_runner": RUNNER,
    }
    with pytest.raises(close_batch.CloseRefused, match="dirty") as excinfo:
        _build(_request(criteria=[entry]), cwd=repo)
    assert "green" in str(excinfo.value).lower() or "dirty" in str(excinfo.value).lower()


def test_missing_green_revision_refuses_with_sha_red(tmp_path):
    repo, red_sha, green_sha = _ancestry_repo(tmp_path)
    entry = {
        "criterion_id": "rec-ac1",
        "method": "tdd",
        "check_run_id": "rec-runner-green",
        "result": "pass",
        # revision omitted — mutant a-missing-green-revision-ok
        "red_check_run_id": "rec-runner-red",
        "red_result": "fail",
        "red_revision": red_sha,
        "red_runner": RUNNER,
    }
    # Matching loader still plants a store revision; request omission must refuse.
    loader = _matching_loader(_request(criteria=[{**entry, "revision": green_sha}]))
    with pytest.raises(close_batch.CloseRefused, match="green revision"):
        close_batch.build_batch(
            _request(criteria=[entry]), cwd=repo, load_check_run=loader
        )


def test_tdd_revision_without_red_is_request_error():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "tdd",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
                "revision": "abc123",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRequestError, match="revision"):
        _build(request)


def test_revision_allowed_tdd_with_red_fields():
    ops = _build(_request(criteria=[_tdd_with_dirty_red()]))
    assert ops[-1]["transition"] == "done"


def test_missing_check_run_id_is_request_error():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "tdd",
                "result": "pass",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRequestError, match="check_run_id"):
        _build(request)


def test_missing_result_is_request_error_not_result_optional_pass():
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRequestError, match="result"):
        _build(request)


# -- worktree / --cwd with store on primary --------------------------------


def _linked_phase_worktree(primary: Path, tmp_path: Path) -> Path:
    """Linked worktree for --cwd; store records stay on the primary checkout."""
    worktree = tmp_path / "phase-worktree"
    added = subprocess.run(
        ["git", "-C", str(primary), "worktree", "add", "-b", "phase/close-cwd", str(worktree)],
        capture_output=True,
        text=True,
    )
    assert added.returncode == 0, added.stderr + added.stdout
    return worktree


def test_close_batch_worktree_cwd_primary_store_authority(
    cli, store, resolved_contract, tmp_path,
):
    """R5: close-batch --cwd=worktree still loads check-runs from primary store."""
    defs = h.record_defs_by_id(resolved_contract)
    subject = "wt-close-task"
    effort = "wt-close-effort"
    work_item, acceptance, execution_report = _build_work_item_family(
        cli, defs, subject, effort, method="check"
    )
    runner_cr = _seed_runner_check_run(
        cli, defs, subject, acceptance, execution_report, result="pass"
    )
    worktree = _linked_phase_worktree(store, tmp_path)

    request = {
        "subject": subject,
        "effort": effort,
        "work_item_id": work_item["id"],
        "transition": "done",
        "execution_report_id": execution_report["id"],
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "check",
                "check_run_id": runner_cr["id"],
                "result": "pass",
            }
        ],
        "finding": None,
    }
    result, out_path = _run_script(
        request, tmp_path, cwd=worktree, process_cwd=store
    )
    assert result.returncode == 0, result.stderr
    assert out_path.is_file()
    ops = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert ops[-1]["transition"] == "done"


def test_close_batch_store_cwd_ignores_worktree_when_resolving(
    cli, store, resolved_contract, tmp_path,
):
    """R5: fabricated id still refused when --cwd is a phase worktree."""
    worktree = _linked_phase_worktree(store, tmp_path)
    result, out_path = _run_script(
        _request(), tmp_path, cwd=worktree, process_cwd=store
    )
    assert result.returncode == 2
    assert not out_path.exists()


# -- oracle freeze / assertion-level red (oracle-witnesses) -------------


ORACLE_REL = "tests/test_oracle_probe.py"
ORACLE_NODE = "tests/test_oracle_probe.py::test_expected_behavior"
ORACLE_CONTENT_V1 = b"oracle v1\n"
ORACLE_CONTENT_V2 = b"oracle v2\n"
ORACLE_HASH_V1 = "sha256:ede7b166ddc88e3753eef482f245f300ad2b85ec3ebbe5a5f33270dd83d02896"
ORACLE_HASH_V2 = "sha256:3e9c68d849014d8206d549226306afb687c39fd68dad9536ca6190862139949b"
ORACLE_HASHES_V1 = f"{ORACLE_REL}:{ORACLE_HASH_V1}"
ORACLE_HASHES_V2 = f"{ORACLE_REL}:{ORACLE_HASH_V2}"

ASSERTION_RED_BODY = """\
============================= test session starts ==============================
collected 1 item

tests/test_oracle_probe.py::test_expected_behavior FAILED                 [100%]

_________________________ test_expected_behavior __________________________

    def test_expected_behavior():
>       assert compute() == 42
E       AssertionError: assert 0 == 42

tests/test_oracle_probe.py:12: AssertionError
=========================== short test summary info ============================
FAILED tests/test_oracle_probe.py::test_expected_behavior - AssertionError: assert 0 == 42
============================== 1 failed in 0.02s ===============================
"""

IMPORT_RED_BODY = """\
============================= test session starts ==============================
collected 0 items / 1 error

_________________ ERROR collecting tests/test_oracle_probe.py __________________
ImportError while importing test module '/tmp/tests/test_oracle_probe.py'.
E   ModuleNotFoundError: No module named 'missing_pkg'
=========================== short test summary info ============================
ERROR tests/test_oracle_probe.py - ModuleNotFoundError: No module named 'missing_pkg'
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.05s ===============================
"""


def _oracle_repo(tmp_path: Path, content: bytes = ORACLE_CONTENT_V1) -> tuple[Path, str]:
    """Temp git repo with an oracle file at HEAD; return (repo, head_sha)."""
    repo = tmp_path / "oracle-repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    probe = repo / ORACLE_REL
    probe.parent.mkdir(parents=True)
    probe.write_bytes(content)
    _git(repo, "add", ORACLE_REL)
    _git(repo, "commit", "-m", "oracle")
    return repo, _git(repo, "rev-parse", "HEAD")


def _oracle_acceptance(
    *,
    test_ids: str = ORACLE_NODE,
    oracle_hashes: str = ORACLE_HASHES_V1,
):
    return {
        "id": "rec-ac1",
        "payload": {
            "method": "tdd",
            "test_ids": test_ids,
            "oracle_hashes": oracle_hashes,
            "effort": "effort-1",
        },
    }


def _assertion_red_fields(**extra):
    fields = {
        "red_body": ASSERTION_RED_BODY,
        "red_failing_node_ids": json.dumps([ORACLE_NODE]),
    }
    fields.update(extra)
    return fields


def _oracle_loader(
    request: dict,
    *,
    acceptance: dict | None = None,
    amendments: list | None = None,
):
    """Store loader + acceptance/amendment hooks for oracle unit tests."""
    base = _matching_loader(request)
    by_id = {}
    for entry in request.get("criteria", []):
        cid = entry.get("check_run_id")
        if cid:
            rec = base(cid)
            by_id[cid] = rec
        red_id = entry.get("red_check_run_id")
        if red_id:
            rec = base(red_id)
            payload = dict(rec["payload"])
            if "red_failing_node_ids" in entry:
                payload["failing_node_ids"] = entry["red_failing_node_ids"]
            by_id[red_id] = {
                "id": red_id,
                "payload": payload,
                "body": entry.get("red_body", ""),
            }

    def load(check_run_id: str) -> dict:
        if check_run_id not in by_id:
            raise LookupError(check_run_id)
        return by_id[check_run_id]

    acc = acceptance if acceptance is not None else _oracle_acceptance()

    def load_acceptance(acceptance_id: str) -> dict:
        if acceptance_id != acc["id"] and acceptance_id != "rec-ac1":
            raise LookupError(acceptance_id)
        return acc

    def list_amendments(acceptance_id: str) -> list:
        return list(amendments or [])

    return load, load_acceptance, list_amendments


def _build_oracle(request: dict, *, cwd: Path, acceptance=None, amendments=None):
    load, load_acc, list_am = _oracle_loader(
        request, acceptance=acceptance, amendments=amendments
    )
    return close_batch.build_batch(
        request,
        cwd=cwd,
        load_check_run=load,
        load_acceptance=load_acc,
        list_oracle_amendments=list_am,
    )


def test_oracle_freeze_happy_path_with_assertion_level_red(tmp_path):
    repo, green_sha = _oracle_repo(tmp_path)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    # Dirty red skips ancestry; green revision is still the hash authority.
    ops = _build_oracle(_request(criteria=[entry]), cwd=repo)
    assert ops[-1]["transition"] == "done"


def test_oracle_hash_refuses_silent_freeze_edit(tmp_path):
    repo, green_sha = _oracle_repo(tmp_path, content=ORACLE_CONTENT_V2)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build_oracle(
            _request(criteria=[entry]),
            cwd=repo,
            acceptance=_oracle_acceptance(oracle_hashes=ORACLE_HASHES_V1),
        )
    msg = str(excinfo.value).lower()
    assert "hash" in msg or "oracle" in msg or "freeze" in msg


def test_assertion_level_refuses_import_only_oracle_red(tmp_path):
    repo, green_sha = _oracle_repo(tmp_path)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        red_body=IMPORT_RED_BODY,
        red_failing_node_ids=json.dumps(["tests/test_oracle_probe.py"]),
    )
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1") as excinfo:
        _build_oracle(_request(criteria=[entry]), cwd=repo)
    msg = str(excinfo.value).lower()
    assert "assertion" in msg or "oracle" in msg


def test_oracle_amendment_approved_allows_new_hashes(tmp_path):
    repo, green_sha = _oracle_repo(tmp_path, content=ORACLE_CONTENT_V2)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    amendment = {
        "id": "rec-am1",
        "lifecycle_state": "active",
        "payload": {
            "acceptance": "rec-ac1",
            "status": "approved",
            "old_hashes": ORACLE_HASHES_V1,
            "new_hashes": ORACLE_HASHES_V2,
            "effort": "effort-1",
        },
    }
    ops = _build_oracle(
        _request(criteria=[entry]),
        cwd=repo,
        acceptance=_oracle_acceptance(oracle_hashes=ORACLE_HASHES_V1),
        amendments=[amendment],
    )
    assert ops[-1]["transition"] == "done"


def test_freeze_hash_refuses_requested_amendment_not_approved(tmp_path):
    repo, green_sha = _oracle_repo(tmp_path, content=ORACLE_CONTENT_V2)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    amendment = {
        "id": "rec-am1",
        "lifecycle_state": "active",
        "payload": {
            "acceptance": "rec-ac1",
            "status": "requested",
            "old_hashes": ORACLE_HASHES_V1,
            "new_hashes": ORACLE_HASHES_V2,
            "effort": "effort-1",
        },
    }
    with pytest.raises(close_batch.CloseRefused, match="rec-ac1"):
        _build_oracle(
            _request(criteria=[entry]),
            cwd=repo,
            acceptance=_oracle_acceptance(oracle_hashes=ORACLE_HASHES_V1),
            amendments=[amendment],
        )


def test_oracle_legacy_without_freeze_fields_skips_gates(tmp_path):
    """Legacy acceptances without test_ids/oracle_hashes keep claim-witnesses path."""
    repo, green_sha = _oracle_repo(tmp_path)
    entry = _tdd_with_dirty_red(revision=green_sha)
    # Import-only red body would refuse if oracle gates ran; legacy skips them.
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        red_body=IMPORT_RED_BODY,
        red_failing_node_ids=json.dumps(["tests/test_oracle_probe.py"]),
    )
    acceptance = {
        "id": "rec-ac1",
        "payload": {"method": "tdd", "effort": "effort-1"},
    }
    ops = _build_oracle(
        _request(criteria=[entry]),
        cwd=repo,
        acceptance=acceptance,
    )
    assert ops[-1]["transition"] == "done"


# -- CLI: oracle freeze / assertion-level via real bin/aff close-batch ------


def _build_oracle_work_item_family(
    cli,
    defs,
    subject: str,
    effort: str,
    *,
    test_ids: str = ORACLE_NODE,
    oracle_hashes: str = ORACLE_HASHES_V1,
):
    """Work-item family whose acceptance carries oracle freeze fields."""
    phase = h.create_generic_record(cli, defs, "project:phase", extra_payload={"effort": effort})
    work_item = h.create_generic_record(
        cli,
        defs,
        "project:work-item",
        subject=subject,
        extra_payload={"effort": effort, "phase": phase["subject"], "kind": "deliver"},
    )
    work_item = h._apply_transition(
        cli, defs["project:work-item"], "project:work-item", work_item, "in_progress"
    )
    acceptance = h.create_generic_record(
        cli,
        defs,
        "project:acceptance",
        subject=subject,
        extra_payload={
            "effort": effort,
            "phase": phase["subject"],
            "method": "tdd",
            "test_ids": test_ids,
            "oracle_hashes": oracle_hashes,
        },
    )
    assignment = h.create_generic_record(
        cli,
        defs,
        "project:assignment",
        subject=subject,
        extra_payload={"effort": effort, "work_item": subject},
    )
    execution_report = h.create_generic_record(
        cli,
        defs,
        "project:execution-report",
        subject=subject,
        extra_payload={
            "work_item": subject,
            "assignment": assignment["subject"],
            "result": "pass",
            "verdict": "pass",
            "revision": "deadbeef",
        },
    )
    return work_item, acceptance, execution_report


def _oracle_cli_close_request(
    *,
    subject: str,
    effort: str,
    work_item_id: str,
    execution_report_id: str,
    acceptance_id: str,
    green_cr_id: str,
    green_revision: str,
    red_cr_id: str,
    red_diff_sha256: str,
):
    return {
        "subject": subject,
        "effort": effort,
        "work_item_id": work_item_id,
        "transition": "done",
        "execution_report_id": execution_report_id,
        "acceptance_ids": [acceptance_id],
        "criteria": [
            {
                "criterion_id": acceptance_id,
                "method": "tdd",
                "check_run_id": green_cr_id,
                "result": "pass",
                "revision": green_revision,
                "red_check_run_id": red_cr_id,
                "red_result": "fail",
                "red_revision": "dirty",
                "red_runner": RUNNER,
                "red_diff_sha256": red_diff_sha256,
            }
        ],
        "finding": None,
    }


def test_cli_oracle_freeze_happy_path_writes_batch(
    cli, store, resolved_contract, tmp_path
):
    """Real close-batch CLI accepts matching freeze hashes + assertion-level red."""
    repo, green_sha = _oracle_repo(tmp_path)
    defs = h.record_defs_by_id(resolved_contract)
    subject = "cli-oracle-happy"
    effort = "cli-oracle-effort"
    work_item, acceptance, execution_report = _build_oracle_work_item_family(
        cli, defs, subject, effort
    )
    red_digest = "c" * 64
    red_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="fail",
        revision="dirty",
        diff_sha256=red_digest,
        body=ASSERTION_RED_BODY,
        failing_node_ids=json.dumps([ORACLE_NODE]),
    )
    green_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="pass",
        revision=green_sha,
    )
    request = _oracle_cli_close_request(
        subject=subject,
        effort=effort,
        work_item_id=work_item["id"],
        execution_report_id=execution_report["id"],
        acceptance_id=acceptance["id"],
        green_cr_id=green_cr["id"],
        green_revision=green_sha,
        red_cr_id=red_cr["id"],
        red_diff_sha256=red_digest,
    )
    result, out_path = _run_script(request, tmp_path, cwd=repo, process_cwd=store)
    assert result.returncode == 0, result.stderr
    assert out_path.is_file()
    ops = [json.loads(line) for line in out_path.read_text().splitlines() if line.strip()]
    assert ops[-1]["transition"] == "done"


def test_cli_oracle_refuses_freeze_hash_drift_without_amendment(
    cli, store, resolved_contract, tmp_path
):
    """Real close-batch CLI refuses hash drift when no approved amendment exists."""
    repo, green_sha = _oracle_repo(tmp_path, content=ORACLE_CONTENT_V2)
    defs = h.record_defs_by_id(resolved_contract)
    subject = "cli-oracle-drift"
    effort = "cli-oracle-effort"
    work_item, acceptance, execution_report = _build_oracle_work_item_family(
        cli, defs, subject, effort, oracle_hashes=ORACLE_HASHES_V1
    )
    red_digest = "d" * 64
    red_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="fail",
        revision="dirty",
        diff_sha256=red_digest,
        body=ASSERTION_RED_BODY,
        failing_node_ids=json.dumps([ORACLE_NODE]),
    )
    green_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="pass",
        revision=green_sha,
    )
    request = _oracle_cli_close_request(
        subject=subject,
        effort=effort,
        work_item_id=work_item["id"],
        execution_report_id=execution_report["id"],
        acceptance_id=acceptance["id"],
        green_cr_id=green_cr["id"],
        green_revision=green_sha,
        red_cr_id=red_cr["id"],
        red_diff_sha256=red_digest,
    )
    result, out_path = _run_script(request, tmp_path, cwd=repo, process_cwd=store)
    assert result.returncode == 2
    assert not out_path.exists()
    msg = (result.stderr + result.stdout).lower()
    assert "hash" in msg or "oracle" in msg or "freeze" in msg


def test_cli_assertion_level_refuses_import_only_oracle_red(
    cli, store, resolved_contract, tmp_path
):
    """Real close-batch CLI refuses oracle-backed close with import-only red."""
    repo, green_sha = _oracle_repo(tmp_path)
    defs = h.record_defs_by_id(resolved_contract)
    subject = "cli-oracle-import-red"
    effort = "cli-oracle-effort"
    work_item, acceptance, execution_report = _build_oracle_work_item_family(
        cli, defs, subject, effort
    )
    red_digest = "e" * 64
    red_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="fail",
        revision="dirty",
        diff_sha256=red_digest,
        body=IMPORT_RED_BODY,
        failing_node_ids=json.dumps(["tests/test_oracle_probe.py"]),
    )
    green_cr = _seed_runner_check_run(
        cli,
        defs,
        subject,
        acceptance,
        execution_report,
        result="pass",
        revision=green_sha,
    )
    request = _oracle_cli_close_request(
        subject=subject,
        effort=effort,
        work_item_id=work_item["id"],
        execution_report_id=execution_report["id"],
        acceptance_id=acceptance["id"],
        green_cr_id=green_cr["id"],
        green_revision=green_sha,
        red_cr_id=red_cr["id"],
        red_diff_sha256=red_digest,
    )
    result, out_path = _run_script(request, tmp_path, cwd=repo, process_cwd=store)
    assert result.returncode == 2
    assert not out_path.exists()
    msg = (result.stderr + result.stdout).lower()
    assert "assertion" in msg or "oracle" in msg


# -- honest runner stamp (evidence-authority) -----------------------------


def test_close_batch_accepts_orchestra_runner_stamp():
    """R3: stored check-run is runner-produced only when runner is orchestra."""
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
                "runner": ORCHESTRA_RUNNER,
            }
        ]
    )
    refused: close_batch.CloseRefused | None = None
    ops: list | None = None
    try:
        ops = _build(request)
    except close_batch.CloseRefused as exc:
        refused = exc
    assert refused is None, f"orchestra runner must be runner-produced; refused: {refused}"
    assert ops is not None
    assert ops[-1]["transition"] == "done"


def test_close_batch_refuses_aff_runner_stamp():
    """R4: stored check-run with runner aff is not runner-produced."""
    request = _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
                "runner": "aff",
            }
        ]
    )
    with pytest.raises(close_batch.CloseRefused) as excinfo:
        _build(request)
    msg = str(excinfo.value).lower()
    assert "runner" in msg
    assert "aff" in msg or "not runner-produced" in msg


# -- claim gate: aff verdict / recheck (evidence-authority) ---------------


CLAIM_ID = "claim-widget"


def _write_manifest_claim(repo: Path, claim_id: str = CLAIM_ID) -> None:
    aff_dir = repo / ".affidavit"
    aff_dir.mkdir(parents=True, exist_ok=True)
    (aff_dir / "manifest.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "id": claim_id,
                        "text": "widget works",
                        "tests": ["tests/test_widget.py::test_widget"],
                        "oracle_hashes": {},
                    }
                ],
                "amendments": [],
            }
        ),
        encoding="utf-8",
    )


def _fake_aff_bin(tmp_path: Path, *, verdict_code: int, recheck_code: int) -> Path:
    bin_dir = tmp_path / "aff-bin"
    bin_dir.mkdir()
    script = bin_dir / "aff"
    script.write_text(
        "#!/bin/sh\n"
        'cmd="$1"\n'
        'case "$cmd" in\n'
        f"  verdict) exit {verdict_code} ;;\n"
        f"  recheck) exit {recheck_code} ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir


def _claim_gate_acceptance(claim_id: str = CLAIM_ID) -> dict:
    return {
        "id": "rec-ac1",
        "subject": claim_id,
        "payload": {
            "method": "check",
            "effort": "effort-1",
        },
    }


def _claim_gate_check_request() -> dict:
    # Use the currently accepted runner stamp so the claim gate is reachable
    # before R3/R4 land; after the marker flips to orchestra, helpers follow.
    return _request(
        criteria=[
            {
                "criterion_id": "rec-ac1",
                "method": "check",
                "check_run_id": "rec-runner-cr",
                "result": "pass",
            }
        ]
    )


def test_claim_gate_refuses_done_when_aff_verdict_nonzero(tmp_path, monkeypatch):
    """R5: manifest claim requires aff verdict exit 0 at close revision."""
    repo, _sha = _oracle_repo(tmp_path)
    _write_manifest_claim(repo)
    bin_dir = _fake_aff_bin(tmp_path, verdict_code=1, recheck_code=0)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    request = _claim_gate_check_request()
    with pytest.raises(close_batch.CloseRefused) as excinfo:
        _build(
            request,
            cwd=repo,
            load_acceptance=lambda _aid: _claim_gate_acceptance(),
        )
    msg = str(excinfo.value).lower()
    assert "verdict" in msg or CLAIM_ID in msg


def test_claim_gate_refuses_done_when_aff_recheck_nonzero(tmp_path, monkeypatch):
    """R6: manifest claim requires aff recheck exit 0."""
    repo, _sha = _oracle_repo(tmp_path)
    _write_manifest_claim(repo)
    bin_dir = _fake_aff_bin(tmp_path, verdict_code=0, recheck_code=1)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    request = _claim_gate_check_request()
    with pytest.raises(close_batch.CloseRefused) as excinfo:
        _build(
            request,
            cwd=repo,
            load_acceptance=lambda _aid: _claim_gate_acceptance(),
        )
    msg = str(excinfo.value).lower()
    assert "recheck" in msg or CLAIM_ID in msg


# -- oracle red via Affidavit CLI only (evidence-authority) ---------------


def test_oracle_backed_close_invokes_aff_cli_for_assertion_red(tmp_path, monkeypatch):
    """R9: assertion-level red classification comes from an Affidavit CLI call."""
    repo, green_sha = _oracle_repo(tmp_path)
    # Stamp with the currently accepted runner so the oracle gate is reached;
    # once RUNNER_MARKER is orchestra, helpers/defaults move with it.
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    request = _request(criteria=[entry])

    aff_calls: list[list[str]] = []
    real_run = subprocess.run

    def spy(cmd, **kwargs):
        argv = [str(c) for c in cmd] if not isinstance(cmd, (str, bytes)) else [str(cmd)]
        name = Path(argv[0]).name if argv else ""
        if name == "aff":
            aff_calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(close_batch.subprocess, "run", spy)

    ops = _build_oracle(request, cwd=repo)
    assert ops[-1]["transition"] == "done"
    assert aff_calls, "expected Affidavit CLI invocation for assertion-level red"


def test_oracle_red_refuses_when_aff_cli_classification_fails(tmp_path, monkeypatch):
    """R9: non-zero Affidavit CLI classification refuses oracle-backed done."""
    repo, green_sha = _oracle_repo(tmp_path)
    entry = _tdd_with_dirty_red(
        revision=green_sha,
        **_assertion_red_fields(),
    )
    request = _request(criteria=[entry])

    real_run = subprocess.run

    def spy(cmd, **kwargs):
        argv = [str(c) for c in cmd] if not isinstance(cmd, (str, bytes)) else [str(cmd)]
        name = Path(argv[0]).name if argv else ""
        if name == "aff":
            return subprocess.CompletedProcess(argv, 1, stdout="", stderr="not assertion")
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(close_batch.subprocess, "run", spy)

    with pytest.raises(close_batch.CloseRefused) as excinfo:
        _build_oracle(request, cwd=repo)
    msg = str(excinfo.value).lower()
    assert "assertion" in msg or "oracle" in msg or "aff" in msg
