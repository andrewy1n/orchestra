"""Tests for orchestra check: policy, CLI integration, install packaging."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from conductor_support import _commit_all, _seed_acceptance
from conftest import REPO_ROOT, git, run_cli

from orchestra.conductor.close_batch import build_batch
from orchestra.conductor.policy import (
    dirty_pass_decision,
    manual_refuse_message,
    map_process_outcome,
)

BIN = REPO_ROOT / "bin" / "orchestra"


def _cli_env() -> dict[str, str]:
    env = dict(os.environ)
    return env


def _run_tuner(*args: str, cwd: Path, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(BIN), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_cli_env(),
        timeout=timeout,
    )


def _list_check_runs(store: Path) -> list[dict]:
    result = run_cli("list", "--type", "tuner:check-run", root=store)
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    return payload.get("records") or payload.get("items") or []


def _parse_check_stdout(result: subprocess.CompletedProcess) -> dict:
    assert result.stdout.strip(), result.stderr
    return json.loads(result.stdout)["record"]


# --- unit policy -----------------------------------------------------------


def test_map_process_outcome_pass_fail_blocked():
    assert map_process_outcome(exit_code=0) == "pass"
    assert map_process_outcome(exit_code=1) == "fail"
    assert map_process_outcome(exit_code=None, timed_out=True) == "blocked"
    assert map_process_outcome(exit_code=None, missing=True) == "blocked"
    assert map_process_outcome(exit_code=127, missing=True) == "blocked"


def test_dirty_pass_policy_refuses_without_allow():
    decision = dirty_pass_decision(
        dirty=True,
        result="pass",
        head="abc123",
        diff_sha256="deadbeef",
        allow_dirty=False,
    )
    assert decision.refuse is True
    assert "allow-dirty" in decision.refuse_message


def test_dirty_pass_policy_allow_dirty_records_dirty_revision():
    decision = dirty_pass_decision(
        dirty=True,
        result="pass",
        head="abc123",
        diff_sha256="deadbeef",
        allow_dirty=True,
    )
    assert decision.refuse is False
    assert decision.revision == "dirty"
    assert decision.diff_sha256 == "deadbeef"


def test_dirty_fail_may_be_dirty_without_override():
    decision = dirty_pass_decision(
        dirty=True,
        result="fail",
        head="abc123",
        diff_sha256="diffhash",
        allow_dirty=False,
    )
    assert decision.refuse is False
    assert decision.revision == "dirty"
    assert decision.diff_sha256 == "diffhash"


def test_clean_tree_uses_head_revision():
    decision = dirty_pass_decision(
        dirty=False,
        result="pass",
        head="abc123",
        diff_sha256=None,
        allow_dirty=False,
    )
    assert decision.revision == "abc123"
    assert decision.diff_sha256 is None


def test_manual_refuse_message_mentions_sign_off():
    text = manual_refuse_message()
    assert "manual" in text.lower()
    assert "signed_by" in text


# --- CLI integration (throwaway store) -------------------------------------


def test_cli_integration_pass_check_run(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="pass-task",
        verify_command="true",
    )
    head = git(store, "rev-parse", "HEAD").stdout.strip()
    assert not git(store, "status", "--porcelain").stdout.strip()
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "pass"
    assert record["payload"]["revision"] == head
    assert record["payload"]["runner"] == "orchestra"
    assert record["payload"]["exit_code"] == 0
    assert "duration_s" in record["payload"]
    assert "output_sha256" in record["payload"]
    assert acceptance["id"] in record["payload"].get("informed_by", [])


def test_check_writes_runner_orchestra(store, cli, resolved_contract):
    """R1: orchestra check stamps payload.runner as orchestra."""
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="runner-orchestra-task",
        verify_command="true",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["runner"] == "orchestra"


def test_cli_integration_fail_check_run(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="fail-task",
        verify_command="false",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 1, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "fail"
    assert record["payload"]["exit_code"] != 0
    assert record["payload"]["runner"] == "orchestra"


def test_cli_blocked_missing_command(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="blocked-task",
        verify_command="orchestra-definitely-missing-binary-xyz",
        method="check",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 2, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "blocked"


def test_dirty_pass_refused_without_allow_dirty(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="dirty-refuse",
        verify_command="true",
    )
    (store / "dirt.txt").write_text("dirty\n")
    before = _list_check_runs(store)
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 3, result.stdout + result.stderr
    assert "dirty" in (result.stderr + result.stdout).lower()
    after = _list_check_runs(store)
    assert len(after) == len(before)


def test_dirty_pass_with_allow_dirty_sets_revision_and_diff(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="dirty-allow",
        verify_command="true",
    )
    (store / "dirt.txt").write_text("dirty\n")
    result = _run_tuner(
        "check",
        "--acceptance",
        acceptance["id"],
        "--allow-dirty",
        cwd=store,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "pass"
    assert record["payload"]["revision"] == "dirty"
    assert record["payload"].get("diff_sha256")
    assert len(record["payload"]["diff_sha256"]) == 64


def test_dirty_fail_may_be_recorded(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="dirty-fail",
        verify_command="false",
    )
    (store / "dirt.txt").write_text("dirty\n")
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 1, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "fail"
    assert record["payload"]["revision"] == "dirty"
    assert record["payload"].get("diff_sha256")


def test_manual_acceptance_refused_no_check_run(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="manual-task",
        verify_command="",
        method="manual",
    )
    before = _list_check_runs(store)
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 3, result.stdout + result.stderr
    combined = result.stderr + result.stdout
    assert "manual" in combined.lower()
    assert "signed_by" in combined
    after = _list_check_runs(store)
    assert len(after) == len(before)


def test_runner_fields_and_metadata_on_pass(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="meta-task",
        verify_command="true",
        requirement="R9",
        method="check",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    payload = record["payload"]
    assert payload["result"] == "pass"
    assert payload["exit_code"] == 0
    assert isinstance(payload["duration_s"], (int, float))
    assert payload["duration_s"] >= 0
    assert len(payload["output_sha256"]) == 64
    assert payload["runner"] == "orchestra"
    assert payload["requirement"] == "R9"
    assert payload["method"] == "check"
    assert payload["revision"]
    assert payload["signed_by"] == ""


def test_exit_code_field_matches_process_for_fail(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="exit-code-task",
        verify_command="sh -c 'exit 7'",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 1
    record = _parse_check_stdout(result)
    assert record["payload"]["exit_code"] == 7
    assert record["payload"]["result"] == "fail"


def test_failing_node_ids_recorded_on_pytest_assertion_fail(
    store,
    cli,
    resolved_contract,
):
    """R2: orchestra check fail from pytest assert → payload failing_node_ids JSON list."""
    probe = store / "probe_oracle_assert.py"
    probe.write_text(
        "def test_oracle_assertion_red_probe():\n    assert False\n",
        encoding="utf-8",
    )
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="failing-node-task",
        verify_command=f"python3 -m pytest {probe.name} -q",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 1, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "fail"
    raw = record["payload"].get("failing_node_ids")
    assert raw, "expected failing_node_ids on fail"
    nodes = raw
    assert isinstance(nodes, list) and nodes
    assert any("test_oracle_assertion_red_probe" in n for n in nodes)


def test_failing_node_ids_absent_on_pass(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="pass-no-nodes",
        verify_command="true",
    )
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert "failing_node_ids" not in record["payload"]


# --- worktree / --cwd / store discovery / mutant killers -------------------


def _linked_phase_worktree(primary: Path, tmp_path: Path) -> tuple[Path, str, str]:
    """Primary store checkout + linked worktree with a distinct HEAD.

    Acceptance / check-run records are written only on the primary working
    tree after the worktree is created, so store-from-``--cwd`` mutants miss
    them when they resolve the store from the worktree snapshot.
    """
    primary_head = git(primary, "rev-parse", "HEAD").stdout.strip()
    worktree = tmp_path / "phase-worktree"
    added = git(primary, "worktree", "add", "-b", "phase/verify-path", str(worktree))
    assert added.returncode == 0, added.stderr + added.stdout
    (worktree / "worktree-only.txt").write_text("phase worktree\n")
    git(worktree, "add", "worktree-only.txt")
    committed = git(worktree, "commit", "-qm", "worktree head")
    assert committed.returncode == 0, committed.stderr
    worktree_head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    assert git(primary, "rev-parse", "HEAD").stdout.strip() == primary_head
    assert worktree_head != primary_head
    assert not git(worktree, "status", "--porcelain").stdout.strip()
    return worktree, primary_head, worktree_head


def test_check_worktree_cwd_primary_store_revision_from_worktree(
    store,
    cli,
    resolved_contract,
    tmp_path,
):
    """R5: --cwd=worktree, process cwd=primary → revision from worktree, write to primary."""
    worktree, primary_head, worktree_head = _linked_phase_worktree(store, tmp_path)
    # Seed after worktree exists so the acceptance lives only on primary.
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="wt-check-task",
        verify_command="true",
    )
    before_primary = _list_check_runs(store)

    result = _run_tuner(
        "check",
        "--acceptance",
        acceptance["id"],
        "--cwd",
        str(worktree),
        cwd=store,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["revision"] == worktree_head
    assert record["payload"]["revision"] != primary_head

    after_primary = _list_check_runs(store)
    assert len(after_primary) == len(before_primary) + 1
    assert record["id"] in {r["id"] for r in after_primary}
    # Worktree checkout must not gain the new check-run record file.
    wt_check_runs = (
        list((worktree / ".canon" / "records").rglob("*check-run*"))
        if (worktree / ".canon" / "records").exists()
        else []
    )
    assert record["id"] not in "".join(str(p) for p in wt_check_runs)


def test_check_store_cwd_discovery_ignores_worktree(
    store,
    cli,
    resolved_contract,
    tmp_path,
):
    """R5/R6: store discovery must use process cwd, not --cwd worktree."""
    worktree, _primary_head, worktree_head = _linked_phase_worktree(store, tmp_path)
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="store-cwd-task",
        verify_command="true",
    )

    result = _run_tuner(
        "check",
        "--acceptance",
        acceptance["id"],
        "--cwd",
        str(worktree),
        cwd=store,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["revision"] == worktree_head
    stored = run_cli("get", "--type", "tuner:check-run", "--id", record["id"], root=store)
    assert stored.returncode == 0, stored.stdout + stored.stderr


def test_cli_cwd_forwarded_uses_worktree_head(
    store,
    cli,
    resolved_contract,
    tmp_path,
):
    """R6 b-cli-cwd-not-forwarded: CLI --cwd must reach run_check, not Path.cwd()."""
    worktree, primary_head, worktree_head = _linked_phase_worktree(store, tmp_path)
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="cwd-fwd-task",
        verify_command="true",
    )

    result = _run_tuner(
        "check",
        "--acceptance",
        acceptance["id"],
        "--cwd",
        str(worktree),
        cwd=store,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["revision"] == worktree_head
    assert record["payload"]["revision"] != primary_head


def test_cli_timeout_maps_to_blocked_timeout(store, cli, resolved_contract):
    """R6 b-check-timeout-not-blocked: slow verify → result=blocked, exit 2."""
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="timeout-task",
        verify_command="sleep 2",
        method="check",
    )
    result = _run_tuner(
        "check",
        "--acceptance",
        acceptance["id"],
        "--timeout",
        "0.5",
        cwd=store,
        timeout=30,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    record = _parse_check_stdout(result)
    assert record["payload"]["result"] == "blocked"


def test_empty_verify_command_refused_no_record(store, cli, resolved_contract):
    """R6 b-check-empty-verify-ok: blank verify_command → exit 4, no check-run."""
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="empty-verify-task",
        verify_command="",
        method="tdd",
    )
    before = _list_check_runs(store)
    result = _run_tuner("check", "--acceptance", acceptance["id"], cwd=store)
    assert result.returncode == 4, result.stdout + result.stderr
    combined = (result.stderr + result.stdout).lower()
    assert "empty" in combined or "verify_command" in combined
    after = _list_check_runs(store)
    assert len(after) == len(before)


# --- check-run reuse ---------------------------------------------------------


def _untrack_store_db(store: Path) -> None:
    result = git(store, "update-index", "--assume-unchanged", ".canon/canon.db")
    assert result.returncode == 0, result.stderr


def _flag_command(flag: Path) -> str:
    return f"test -f {flag}"


def _run_check_json(store: Path, acceptance_id: str) -> tuple[int, dict]:
    _untrack_store_db(store)
    result = _run_tuner("check", "--acceptance", acceptance_id, cwd=store)
    assert result.stdout.strip(), result.stderr
    return result.returncode, json.loads(result.stdout)


def test_check_reuses_identical_check_run(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store, cli, resolved_contract, subject="reuse-task", verify_command="true"
    )
    code_first, first = _run_check_json(store, acceptance["id"])
    assert code_first == 0
    assert first["reused"] is False
    before = _list_check_runs(store)
    code_second, second = _run_check_json(store, acceptance["id"])
    assert code_second == 0
    assert second["reused"] is True
    assert second["record"]["id"] == first["record"]["id"]
    assert len(_list_check_runs(store)) == len(before)


def test_check_reuses_identical_failing_check_run(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store, cli, resolved_contract, subject="reuse-fail-task", verify_command="false"
    )
    code_first, first = _run_check_json(store, acceptance["id"])
    code_second, second = _run_check_json(store, acceptance["id"])
    assert code_first == code_second == 1
    assert second["reused"] is True
    assert second["record"]["id"] == first["record"]["id"]
    assert len(_list_check_runs(store)) == 1


def test_check_writes_for_dirty_revision_every_time(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store, cli, resolved_contract, subject="dirty-no-reuse", verify_command="false"
    )
    (store / "dirt.txt").write_text("dirty\n")
    _, first = _run_check_json(store, acceptance["id"])
    _, second = _run_check_json(store, acceptance["id"])
    assert first["record"]["payload"]["revision"] == "dirty"
    assert second["reused"] is False
    assert second["record"]["id"] != first["record"]["id"]
    assert len(_list_check_runs(store)) == 2


def test_check_writes_for_new_revision(store, cli, resolved_contract):
    acceptance = _seed_acceptance(
        store, cli, resolved_contract, subject="new-revision-task", verify_command="true"
    )
    _, first = _run_check_json(store, acceptance["id"])
    (store / "next.txt").write_text("next\n")
    new_head = _commit_all(store, "next revision")
    code, second = _run_check_json(store, acceptance["id"])
    assert code == 0
    assert second["reused"] is False
    assert second["record"]["id"] != first["record"]["id"]
    assert second["record"]["payload"]["revision"] == new_head
    assert len(_list_check_runs(store)) == 2


def test_check_writes_for_changed_result(store, cli, resolved_contract, tmp_path):
    flag = tmp_path / "flag"
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="changed-result-task",
        verify_command=_flag_command(flag),
    )
    code_red, red = _run_check_json(store, acceptance["id"])
    flag.write_text("ok\n")
    code_green, green = _run_check_json(store, acceptance["id"])
    assert code_red == 1
    assert code_green == 0
    assert green["reused"] is False
    assert green["record"]["id"] != red["record"]["id"]
    assert green["record"]["payload"]["revision"] == red["record"]["payload"]["revision"]
    assert green["record"]["payload"]["result"] == "pass"
    assert len(_list_check_runs(store)) == 2


def test_check_writes_when_latest_result_differs(store, cli, resolved_contract, tmp_path):
    flag = tmp_path / "flag"
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="pass-fail-pass-task",
        verify_command=_flag_command(flag),
    )
    flag.write_text("ok\n")
    _, first_pass = _run_check_json(store, acceptance["id"])
    time.sleep(1.1)
    flag.unlink()
    _, fail = _run_check_json(store, acceptance["id"])
    time.sleep(1.1)
    flag.write_text("ok\n")
    code, second_pass = _run_check_json(store, acceptance["id"])
    assert code == 0
    assert fail["reused"] is False
    assert second_pass["reused"] is False
    assert second_pass["record"]["id"] not in {first_pass["record"]["id"], fail["record"]["id"]}
    assert len(_list_check_runs(store)) == 3
    time.sleep(1.1)
    _, again = _run_check_json(store, acceptance["id"])
    assert again["reused"] is True
    assert again["record"]["id"] == second_pass["record"]["id"]


def test_red_first_gate_after_reuse(store, cli, resolved_contract, tmp_path):
    flag = tmp_path / "flag"
    probe = store / "probe_red_first_reuse.py"
    probe.write_text(
        "from pathlib import Path\n\n\n"
        "def test_red_first_reuse_probe():\n"
        f"    assert Path({str(flag)!r}).exists()\n",
        encoding="utf-8",
    )
    node = f"{probe.name}::test_red_first_reuse_probe"
    digest = hashlib.sha256(probe.read_bytes()).hexdigest()
    acceptance = _seed_acceptance(
        store,
        cli,
        resolved_contract,
        subject="red-first-reuse-task",
        verify_command=f"python3 -B -m pytest -p no:cacheprovider {probe.name} -q",
        extra_payload={"test_ids": [node], "oracle_hashes": [f"{probe.name}:sha256:{digest}"]},
    )
    _, red = _run_check_json(store, acceptance["id"])
    _, red_again = _run_check_json(store, acceptance["id"])
    assert red["record"]["payload"]["result"] == "fail"
    assert red_again["reused"] is True
    flag.write_text("ok\n")
    _, green = _run_check_json(store, acceptance["id"])
    assert green["reused"] is False
    revision = green["record"]["payload"]["revision"]
    request = {
        "subject": "red-first-reuse-task",
        "effort": "workflow-loop",
        "work_item_id": "rec-wi",
        "transition": "done",
        "execution_report_id": None,
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "tdd",
                "check_run_id": green["record"]["id"],
                "result": "pass",
                "revision": revision,
                "red_check_run_id": red_again["record"]["id"],
                "red_result": "fail",
                "red_revision": revision,
                "red_runner": "orchestra",
            }
        ],
        "finding": None,
    }
    ops = build_batch(request, cwd=store, store_root=store)
    assert ops[-1]["transition"] == "done"
    assert red_again["record"]["id"] == red["record"]["id"]


# --- entry / bin -------------------------------------------------------------


def test_bin_tuner_entry_exists_and_is_executable():
    assert BIN.is_file()
    assert os.access(BIN, os.X_OK)
    result = subprocess.run(
        [sys.executable, str(BIN), "--help"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=_cli_env(),
    )
    assert result.returncode == 0
    assert "check" in result.stdout


def test_orchestra_subcommand_help():
    for subcommand in ("check", "close-batch"):
        result = subprocess.run(
            [sys.executable, str(BIN), subcommand, "--help"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=_cli_env(),
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_readme_documents_bin_tuner_entry():
    text = (REPO_ROOT / "README.md").read_text()
    assert "orchestra verify" in text
    assert "bin/orchestra check" in text or "orchestra check" in text
