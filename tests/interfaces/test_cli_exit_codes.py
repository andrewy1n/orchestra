"""Pin the exit code and output shape of every `orchestra` and `canon` verb."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from interfaces_support import invoke

NO_STORE = "No artifact store for"
NO_CONFIG = "required project config is missing"
ARGS_REQUIRED = "the following arguments are required"
EVIDENCE = json.dumps(
    {"subject": "a", "kind": "deliver", "result": "pass", "verdict": "pass", "evidence": "ran"}
)
START = ("suite", "start", "--phase", "p1")

Out = str | tuple[str, ...] | None


@dataclass(frozen=True)
class Case:
    name: str
    tool: str
    argv: tuple[str, ...]
    world: str
    code: int
    out: Out
    err: str
    before: tuple[tuple[str, ...], ...]
    files: tuple[tuple[str, str], ...]
    stdin: str


def orchestra(
    name: str,
    world: str,
    code: int,
    *argv: str,
    out: Out = None,
    err: str = "",
    before: tuple[tuple[str, ...], ...] = (),
    files: tuple[tuple[str, str], ...] = (),
    stdin: str = "",
) -> Case:
    return Case(name, "orchestra", argv, world, code, out, err, before, files, stdin)


def canon(
    name: str,
    world: str,
    code: int,
    *argv: str,
    out: Out = None,
    err: str = "",
    before: tuple[tuple[str, ...], ...] = (),
    files: tuple[tuple[str, str], ...] = (),
    stdin: str = "",
) -> Case:
    return Case(name, "canon", argv, world, code, out, err, before, files, stdin)


CONDUCTOR_SUITE_GATE = [
    orchestra("suite_policy_success", "shared", 0, "suite", "policy", out=()),
    orchestra("suite_policy_no_config", "bare", 2, "suite", "policy", err=NO_CONFIG),
    orchestra("suite_start_skipped", "fresh", 4, *START, out=()),
    orchestra("suite_start_no_config", "bare", 2, *START, err=NO_CONFIG),
    orchestra(
        "suite_poll_success", "fresh", 4, "suite", "poll", "--phase", "p1", before=(START,), out=()
    ),
    orchestra(
        "suite_poll_no_run", "fresh", 2, "suite", "poll", "--phase", "p1", err="no suite run found"
    ),
    orchestra("suite_poll_missing_phase", "shared", 2, "suite", "poll", err=ARGS_REQUIRED),
    orchestra(
        "suite_collect_success",
        "fresh",
        4,
        "suite",
        "collect",
        "--phase",
        "p1",
        before=(START,),
        out=(),
    ),
    orchestra(
        "suite_collect_no_run",
        "bare",
        2,
        "suite",
        "collect",
        "--phase",
        "p1",
        err="no suite run found",
    ),
    orchestra(
        "suite_cancel_success",
        "fresh",
        0,
        "suite",
        "cancel",
        "--phase",
        "p1",
        "--run-id",
        "x",
        before=(START,),
        out=(),
    ),
    orchestra(
        "suite_cancel_no_run",
        "bare",
        2,
        "suite",
        "cancel",
        "--phase",
        "p1",
        "--run-id",
        "x",
        err="no suite run found",
    ),
    orchestra(
        "suite_record_skipped",
        "fresh",
        4,
        "suite",
        "record",
        "--phase",
        "p1",
        "--effort",
        "alpha",
        before=(START,),
        err="suite skipped",
    ),
    orchestra(
        "suite_record_no_run",
        "bare",
        2,
        "suite",
        "record",
        "--phase",
        "p1",
        "--effort",
        "alpha",
        err="no suite run found",
    ),
    orchestra("gate_refusal", "shared", 1, "gate", "p1", out="p1: missing verification-task-done"),
    orchestra("gate_unknown_phase", "shared", 2, "gate", "nope", err="phase 'nope' not found"),
    orchestra("gate_no_store", "bare", 2, "gate", "p1", err=NO_STORE),
    orchestra(
        "analyze_json_success", "shared", 0, "analyze", "p1", "--stage", "plan", "--json", out=()
    ),
    orchestra(
        "analyze_text_success", "shared", 0, "analyze", "p1", "--stage", "plan", out="warning"
    ),
    orchestra(
        "analyze_refusal",
        "shared",
        1,
        "analyze",
        "p1",
        "--stage",
        "design",
        out="error active-design-required",
    ),
    orchestra(
        "analyze_unknown_phase", "shared", 2, "analyze", "nope", err="phase 'nope' not found"
    ),
    orchestra("analyze_no_store", "bare", 2, "analyze", "p1", err=NO_STORE),
    orchestra(
        "review_brief_success",
        "shared",
        0,
        "review-brief",
        "--phase",
        "p1",
        "--phase-head",
        "HEAD",
        "--out",
        "{root}/review.md",
        out="{root}/review.md",
    ),
]

CONDUCTOR_WAVE_TASK = [
    orchestra(
        "wave_start_success",
        "fresh",
        0,
        "wave",
        "start",
        "p1",
        out="## a (inline) {root}/.worktrees/p1--a",
    ),
    orchestra("wave_start_json_success", "fresh", 0, "wave", "start", "p1", "--json", out=()),
    orchestra("wave_start_refusal", "wave", 2, "wave", "start", "p1", err="no ready work-item"),
    orchestra("wave_start_no_store", "bare", 2, "wave", "start", "p1", err=NO_STORE),
    orchestra(
        "wave_end_success", "wave", 0, "wave", "end", "p1", out="skipped a: task is not closed"
    ),
    orchestra("wave_end_no_store", "bare", 2, "wave", "end", "p1", err=NO_STORE),
    orchestra(
        "wave_resolve_refusal",
        "wave",
        1,
        "wave",
        "resolve",
        "p1",
        "a",
        err="no open merge:a question",
    ),
    orchestra("wave_resolve_no_store", "bare", 2, "wave", "resolve", "p1", "a", err=NO_STORE),
    orchestra("task_land_schema", "bare", 0, "task", "land", "--schema", out=()),
    orchestra(
        "task_land_success",
        "wave",
        0,
        "task",
        "land",
        "a",
        "--evidence",
        "{root}/evidence.json",
        "--json",
        files=(("evidence.json", EVIDENCE),),
        out=(),
    ),
    orchestra(
        "task_land_missing_evidence",
        "wave",
        2,
        "task",
        "land",
        "a",
        err="a task and --evidence are required",
    ),
    orchestra(
        "task_land_unreadable_evidence",
        "wave",
        2,
        "task",
        "land",
        "a",
        "--evidence",
        "{root}/none.json",
        err="cannot read evidence",
    ),
    orchestra(
        "task_redispatch_refusal",
        "wave",
        2,
        "task",
        "redispatch",
        "zzz",
        "--expected-revision",
        "x",
        err="work-item 'zzz' not found",
    ),
    orchestra(
        "task_redispatch_missing_revision", "wave", 2, "task", "redispatch", "a", err=ARGS_REQUIRED
    ),
]

CONDUCTOR_LAND_CLOSE = [
    orchestra(
        "land_gate_refusal",
        "shared",
        5,
        "land",
        "--phase",
        "p1",
        err="missing verification-task-done",
    ),
    orchestra(
        "land_unknown_phase", "shared", 2, "land", "--phase", "nope", err="phase 'nope' not found"
    ),
    orchestra("land_no_config", "bare", 2, "land", "--phase", "p1", err=NO_CONFIG),
    orchestra("land_missing_phase", "shared", 2, "land", err=ARGS_REQUIRED),
    orchestra("close_all_success", "shared", 0, "close", "--all", out=()),
    orchestra(
        "close_no_landing",
        "shared",
        2,
        "close",
        "--phase",
        "p1",
        err="no landing record for phase 'p1'",
    ),
    orchestra(
        "close_needs_one_selector",
        "shared",
        2,
        "close",
        err="pass exactly one of --phase and --all",
    ),
    orchestra("close_no_store", "bare", 2, "close", "--phase", "p1", err=NO_STORE),
    orchestra(
        "close_batch_invalid_request",
        "shared",
        1,
        "close-batch",
        err="close-request is not valid JSON",
    ),
]

CONDUCTOR_WORKFLOW = [
    orchestra(
        "workflow_preview_json_success",
        "shared",
        0,
        "workflow",
        "preview",
        "alpha",
        "p1",
        "spec",
        "--json",
        out=(),
    ),
    orchestra(
        "workflow_preview_text_success",
        "shared",
        0,
        "workflow",
        "preview",
        "alpha",
        "p1",
        "spec",
        out="single-step: p1\nsteps: spec\nsnapshot: ",
    ),
    orchestra(
        "workflow_preview_unknown_phase",
        "shared",
        2,
        "workflow",
        "preview",
        "alpha",
        "nope",
        "spec",
        err="unknown phase selector 'nope'",
    ),
    orchestra(
        "workflow_preview_no_store",
        "bare",
        2,
        "workflow",
        "preview",
        "alpha",
        "p1",
        "spec",
        err=NO_STORE,
    ),
    orchestra(
        "workflow_start_stale_snapshot",
        "shared",
        2,
        "workflow",
        "start",
        "alpha",
        "p1",
        "spec",
        "--snapshot-token",
        "bad",
        err="snapshot changed",
    ),
    orchestra(
        "workflow_start_missing_token",
        "shared",
        2,
        "workflow",
        "start",
        "alpha",
        "p1",
        "spec",
        err=ARGS_REQUIRED,
    ),
    orchestra(
        "workflow_status_unknown_run",
        "shared",
        2,
        "workflow",
        "status",
        "nope",
        err="could not be read",
    ),
    orchestra("workflow_status_no_store", "bare", 2, "workflow", "status", "nope", err=NO_STORE),
    orchestra(
        "workflow_next_unknown_run", "shared", 2, "workflow", "next", "nope", err="unknown record"
    ),
    orchestra("workflow_brief_success", "shared", 0, "workflow", "brief", "p1", "spec", out="# "),
    orchestra(
        "workflow_brief_missing_step",
        "shared",
        2,
        "workflow",
        "brief",
        err="give --skill or both phase and step",
    ),
    orchestra(
        "workflow_brief_unknown_skill",
        "shared",
        2,
        "workflow",
        "brief",
        "--skill",
        "spec",
        err="unknown skill",
    ),
    orchestra(
        "workflow_review_unknown_artifact",
        "shared",
        2,
        "workflow",
        "review",
        "p1",
        "spec",
        "--artifact",
        "x",
        "--authority",
        "user-approval",
        "--basis",
        "b",
        err="unsafe record id 'x'",
    ),
    orchestra(
        "workflow_review_no_store",
        "bare",
        2,
        "workflow",
        "review",
        "p1",
        "spec",
        "--artifact",
        "x",
        "--authority",
        "user-approval",
        "--basis",
        "b",
        err=NO_STORE,
    ),
    orchestra(
        "workflow_amend_check_missing_change",
        "shared",
        2,
        "workflow",
        "amend-check",
        "a",
        "--expected-revision",
        "x",
        "--basis",
        "b",
        err="one of the arguments --equivalent-command --routine-check is required",
    ),
]

LIGHT_COMPONENTS = [
    orchestra("handoff_success", "shared", 0, "handoff", out="# Project Handoff\n"),
    orchestra("handoff_no_store", "bare", 1, "handoff", err=NO_STORE),
    orchestra("view_plan_success", "shared", 0, "view", "plan", out="# Project Plan\n"),
    orchestra("view_status_success", "shared", 0, "view", "status", out="# Project Status\n"),
    orchestra(
        "view_verification_success",
        "shared",
        0,
        "view",
        "verification",
        out="# Project Verification\n",
    ),
    orchestra("view_roadmap_success", "shared", 0, "view", "roadmap", out="# Project Roadmap\n"),
    orchestra("view_no_store", "bare", 1, "view", "plan", err=NO_STORE),
    orchestra("view_unknown_name", "shared", 2, "view", "nope", err="invalid choice"),
    orchestra("brief_success", "shared", 0, "brief", "a", out="# Brief: a\n"),
    orchestra(
        "brief_unknown_item",
        "shared",
        1,
        "brief",
        "nope",
        err="no work item found for subject 'nope'",
    ),
    orchestra("brief_no_store", "bare", 1, "brief", "a", err=NO_STORE),
    orchestra(
        "status_success", "shared", 0, "status", out="alpha: running 0, ready 1, needs-you 0\n"
    ),
    orchestra("status_count_success", "shared", 0, "status", "--count", out="0\n"),
    orchestra("status_no_store", "bare", 1, "status", err=NO_STORE),
    orchestra(
        "hook_start_cursor_success", "shared", 0, "hook-start", "--cursor", stdin="{}", out=()
    ),
    orchestra("hook_start_no_store", "bare", 0, "hook-start", "--cursor", stdin="{}", out=None),
    orchestra(
        "hook_start_invalid_input", "shared", 2, "hook-start", "--claude", err="invalid hook input"
    ),
    orchestra(
        "hook_stop_cursor_success", "shared", 0, "hook-stop", "--cursor", stdin="{}", out="{}\n"
    ),
    orchestra(
        "hook_stop_invalid_input", "shared", 2, "hook-stop", "--claude", err="invalid hook input"
    ),
    orchestra(
        "plugins_list_table_success",
        "bare",
        0,
        "plugins",
        "list",
        out="scope\tid\tapi\tdistribution\tversion\ttarget\n",
    ),
    orchestra(
        "plugins_list_json_success", "bare", 0, "plugins", "list", "--format", "json", out="[{"
    ),
    orchestra(
        "plugins_list_unknown_scope",
        "bare",
        2,
        "plugins",
        "list",
        "--scope",
        "nope",
        err="invalid choice",
    ),
    orchestra("metrics_phases_success", "shared", 0, "metrics", "phases", "--json", out="[]\n"),
    orchestra("metrics_phases_no_store", "bare", 1, "metrics", "phases", err=NO_STORE),
    orchestra(
        "metrics_compare_unknown_boundary",
        "shared",
        1,
        "metrics",
        "compare",
        "p1",
        err="no done phase named p1",
    ),
    orchestra(
        "metrics_repairs_missing_since", "shared", 2, "metrics", "repairs", err=ARGS_REQUIRED
    ),
    orchestra(
        "effort_autonomy_success",
        "fresh",
        0,
        "effort",
        "autonomy",
        "alpha",
        "gated",
        out="alpha: autonomy gated\n",
    ),
    orchestra(
        "effort_autonomy_json_success",
        "fresh",
        0,
        "effort",
        "autonomy",
        "alpha",
        "gated",
        "--json",
        out=(),
    ),
    orchestra(
        "effort_autonomy_migrate_dry_run",
        "shared",
        0,
        "effort",
        "autonomy",
        "--migrate",
        out="dry run; pass --apply to write\n",
    ),
    orchestra(
        "effort_autonomy_unknown_effort",
        "shared",
        2,
        "effort",
        "autonomy",
        "nope",
        "gated",
        err="unknown effort 'nope'",
    ),
    orchestra(
        "effort_autonomy_bad_level",
        "shared",
        2,
        "effort",
        "autonomy",
        "alpha",
        "bogus",
        err="autonomy must be one of",
    ),
    orchestra(
        "effort_autonomy_missing_level",
        "shared",
        2,
        "effort",
        "autonomy",
        "alpha",
        err="an effort and a level are required",
    ),
    orchestra(
        "effort_autonomy_no_store", "bare", 2, "effort", "autonomy", "alpha", "gated", err=NO_STORE
    ),
    orchestra("idea_success", "fresh", 0, "idea", "A thing", out="a-thing\n"),
    orchestra(
        "idea_unknown_area",
        "fresh",
        1,
        "idea",
        "Zed",
        "--area",
        "nope",
        err="no composer:area record with subject 'nope'",
    ),
    orchestra("idea_no_store", "bare", 1, "idea", "A thing", err=NO_STORE),
    orchestra(
        "place_unknown_area",
        "shared",
        1,
        "place",
        "alpha",
        "nope",
        err="composer:area 'nope' does not exist",
    ),
    orchestra("place_no_store", "bare", 1, "place", "alpha", "nope", err=NO_STORE),
    orchestra("store_path_success", "shared", 0, "store", "path", out="{root}/.canon\n"),
    orchestra("store_path_json_success", "shared", 0, "store", "path", "--json", out=()),
    orchestra("store_path_no_store", "bare", 2, "store", "path", err=NO_STORE),
    orchestra("store_scan_success", "shared", 0, "store", "scan", out=None),
    orchestra("store_scan_no_store", "bare", 2, "store", "scan", err=NO_STORE),
    orchestra("store_recover_evidence_success", "shared", 0, "store", "recover-evidence", out=()),
    orchestra(
        "store_recover_evidence_no_store", "bare", 2, "store", "recover-evidence", err=NO_STORE
    ),
    orchestra(
        "store_run_list_success",
        "shared",
        0,
        "store",
        "run",
        "--",
        "list",
        "--type",
        "score:effort",
        out="{",
    ),
    orchestra(
        "store_run_unsupported",
        "shared",
        2,
        "store",
        "run",
        "--",
        "bogus",
        err="unsupported store operation 'bogus'",
    ),
    orchestra(
        "store_run_no_store",
        "bare",
        2,
        "store",
        "run",
        "--",
        "list",
        "--type",
        "score:effort",
        err=NO_STORE,
    ),
    orchestra("store_ensure_success", "bare", 0, "store", "ensure", "--json", out=()),
    orchestra("store_ensure_idempotent", "shared", 0, "store", "ensure", out="{root}/.canon\n"),
]

TUNER_CANON_STAGE = [
    orchestra(
        "verify_runner_template_success",
        "bare",
        0,
        "verify",
        "runner-template",
        "unit",
        out='["python3"',
    ),
    orchestra(
        "verify_runner_template_unknown_kind",
        "bare",
        2,
        "verify",
        "runner-template",
        "pytest",
        err="invalid choice",
    ),
    orchestra(
        "verify_verdict_missing_manifest",
        "shared",
        2,
        "verify",
        "verdict",
        "--at",
        "HEAD",
        "X",
        err="missing .tuner/manifest.json",
    ),
    orchestra(
        "verify_verdict_not_a_repo",
        "bare",
        2,
        "verify",
        "verdict",
        "--at",
        "HEAD",
        "X",
        err="not a git repository",
    ),
    orchestra(
        "verify_freeze_missing_manifest",
        "shared",
        2,
        "verify",
        "freeze",
        err="missing .tuner/manifest.json",
    ),
    orchestra(
        "verify_lint_claims_missing_manifest",
        "shared",
        2,
        "verify",
        "lint",
        "claims",
        err="manifest.json",
    ),
    orchestra(
        "verify_lint_no_assert_flags_file",
        "shared",
        1,
        "verify",
        "lint",
        "no-assert",
        "{root}/base.txt",
        out="{root}/base.txt\n",
    ),
    orchestra(
        "verify_lint_no_assert_missing_path",
        "shared",
        2,
        "verify",
        "lint",
        "no-assert",
        err=ARGS_REQUIRED,
    ),
    orchestra("verify_trail_success", "shared", 0, "verify", "trail", out="[]\n"),
    orchestra("verify_trail_no_store", "bare", 2, "verify", "trail", err=NO_STORE),
    orchestra(
        "verify_recheck_no_binding",
        "shared",
        1,
        "verify",
        "recheck",
        "--claim",
        "X",
        err="no active binding for X",
    ),
    orchestra(
        "verify_recheck_no_store", "bare", 1, "verify", "recheck", "--claim", "X", err=NO_STORE
    ),
    orchestra(
        "verify_unbind_unknown",
        "shared",
        1,
        "verify",
        "unbind",
        "--id",
        "x",
        err="unsafe record id 'x'",
    ),
    orchestra("verify_bind_missing_args", "shared", 2, "verify", "bind", err=ARGS_REQUIRED),
    orchestra(
        "verify_attest_verify_missing_args",
        "shared",
        2,
        "verify",
        "attest",
        "verify",
        err=ARGS_REQUIRED,
    ),
    orchestra("verify_audit_missing_args", "shared", 2, "verify", "audit", err=ARGS_REQUIRED),
    orchestra(
        "verify_assertion_red_pass_result",
        "shared",
        1,
        "verify",
        "assertion-red",
        stdin='{"result": "pass"}',
        out=None,
    ),
    orchestra(
        "verify_assertion_red_invalid_json",
        "shared",
        2,
        "verify",
        "assertion-red",
        err="Expecting value",
    ),
    orchestra("verify_plugins_missing_args", "shared", 2, "verify", "plugins", err=ARGS_REQUIRED),
    orchestra(
        "check_unknown_acceptance",
        "shared",
        4,
        "check",
        "--acceptance",
        "nope",
        err="unsafe record id 'nope'",
    ),
    orchestra("check_no_store", "bare", 4, "check", "--acceptance", "nope", err=NO_STORE),
    orchestra("check_missing_acceptance", "shared", 2, "check", err=ARGS_REQUIRED),
    orchestra("install_list_success", "bare", 0, "install", "--list", out="ID "),
    orchestra("sessions_aggregate_success", "bare", 0, "sessions", "aggregate", out=()),
    orchestra(
        "sessions_report_empty_root",
        "bare",
        0,
        "sessions",
        "report",
        "--records",
        "{root}/none",
        out=None,
    ),
    canon("validate_success", "shared", 0, "validate", out=("status", "errors", "records")),
    canon("validate_no_store", "bare", 1, "validate", out=("error", "message")),
    canon("list_success", "shared", 0, "list", "--type", "score:effort", out=("records", "count")),
    canon(
        "list_table_success",
        "shared",
        0,
        "list",
        "--type",
        "score:effort",
        "--format",
        "table",
        out="id ",
    ),
    canon("get_unsafe_id", "shared", 1, "get", "--id", "nope", out=("error", "message")),
    canon("get_missing_id", "shared", 2, "get", err=ARGS_REQUIRED),
    canon(
        "create_success",
        "fresh",
        0,
        "create",
        "--type",
        "score:effort",
        "--subject",
        "zed",
        "--payload",
        '{"goal": "g", "kind": "deliver"}',
        out=("ok", "op", "record", "store"),
    ),
    canon(
        "create_unknown_type",
        "shared",
        4,
        "create",
        "--type",
        "nope:x",
        "--subject",
        "s",
        "--payload",
        "{}",
        out=("error", "message"),
    ),
    canon(
        "create_bad_json",
        "shared",
        1,
        "create",
        "--type",
        "score:effort",
        "--subject",
        "s",
        "--payload",
        "{",
        out=("error", "message"),
    ),
    canon(
        "create_read_only",
        "shared",
        1,
        "--read-only",
        "create",
        "--type",
        "score:effort",
        "--subject",
        "s",
        "--payload",
        "{}",
        out=("error", "message"),
    ),
    canon(
        "update_unsafe_id",
        "shared",
        1,
        "update",
        "--id",
        "nope",
        "--transition",
        "x",
        out=("error", "message"),
    ),
    canon(
        "supersede_unsafe_id", "shared", 1, "supersede", "--id", "nope", out=("error", "message")
    ),
    canon("correct_unsafe_id", "shared", 1, "correct", "--id", "nope", out=("error", "message")),
    canon(
        "apply_unknown_op",
        "shared",
        1,
        "apply",
        stdin='{"op": "bogus"}\n',
        out=("ok", "op", "applied", "failed", "results", "store"),
    ),
    canon(
        "apply_empty",
        "shared",
        0,
        "apply",
        stdin="",
        out=("ok", "op", "applied", "failed", "results", "store"),
    ),
    canon("init_idempotent", "shared", 0, "init", out=("status", "store")),
    canon("init_not_a_repo", "bare", 1, "init", out=("error", "message")),
    canon("backup_success", "fresh", 0, "backup", out=("backup",)),
    canon("backup_no_store", "bare", 1, "backup", out=("error", "message")),
    canon("export_success", "fresh", 0, "export", "--out", "{root}/ops.jsonl", out=("ops",)),
    canon("export_missing_out", "shared", 2, "export", err=ARGS_REQUIRED),
    canon("schemas_show_success", "shared", 0, "schemas", "show", out=("schemas",)),
    canon(
        "schemas_sync_success",
        "fresh",
        0,
        "schemas",
        "sync",
        out=("status", "schemas", "errors", "migrated_records"),
    ),
    canon(
        "schemas_add_unknown_module",
        "shared",
        4,
        "schemas",
        "add",
        "nope",
        out=("error", "message"),
    ),
    canon("schemas_no_store", "bare", 1, "schemas", "show", out=("error", "message")),
    canon("merge_not_a_store", "shared", 1, "merge", "{root}/missing", out=("error", "message")),
    canon("import_missing_source", "shared", 2, "import", err=ARGS_REQUIRED),
]

GROUPS: dict[str, list[Case]] = {
    "conductor_suite_gate": CONDUCTOR_SUITE_GATE,
    "conductor_wave_task": CONDUCTOR_WAVE_TASK,
    "conductor_land_close": CONDUCTOR_LAND_CLOSE,
    "conductor_workflow": CONDUCTOR_WORKFLOW,
    "light_components": LIGHT_COMPONENTS,
    "tuner_canon_stage": TUNER_CANON_STAGE,
}


@pytest.fixture
def worlds(
    shared_world: Path, fresh_world: Path, wave_world: Path, bare_dir: Path
) -> dict[str, Path]:
    return {"shared": shared_world, "fresh": fresh_world, "wave": wave_world, "bare": bare_dir}


def _format(text: str, root: Path) -> str:
    return text.replace("{root}", str(root))


def _params() -> list[object]:
    return [
        pytest.param(case, id=f"{group}-{case.name}")
        for group, cases in GROUPS.items()
        for case in cases
    ]


@pytest.mark.parametrize("case", _params())
def test_verb_exit_code_and_shape(case: Case, worlds: dict[str, Path]) -> None:
    root = worlds[case.world]
    for relative, text in case.files:
        (root / relative).write_text(text, encoding="utf-8")
    for step in case.before:
        invoke(case.tool, [_format(part, root) for part in step], root)
    result = invoke(
        case.tool, [_format(part, root) for part in case.argv], root, _format(case.stdin, root)
    )
    assert result.code == case.code, (result.out, result.err)
    if case.out is None:
        assert result.out == ""
    elif isinstance(case.out, tuple):
        if case.out:
            assert sorted(json.loads(result.out)) == sorted(case.out)
        else:
            assert isinstance(json.loads(result.out), dict)
    else:
        assert result.out.startswith(_format(case.out, root)), result.out
    if case.err:
        assert case.err in result.err, result.err
    else:
        assert result.err == ""
