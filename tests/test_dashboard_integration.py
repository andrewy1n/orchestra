"""Drive one effort through its lifecycle via the CLI and check the dashboard after each step."""

from __future__ import annotations

import json
import os
import subprocess
import sys


import helpers as h
from conftest import REPO_ROOT, git

EFFORT = "flow"
PHASE = "flow-phase-1"

def _work_item(cli, defs, subject: str, *rels: str) -> dict:
    payload = {"title": f"title of {subject}", "phase": PHASE, "kind": "deliver", "assignee": "", "effort": EFFORT}
    h.ensure_refs(cli, defs, defs["plan:work-item"], payload)
    args = ["create", "--type", "plan:work-item", "--subject", subject, "--payload", json.dumps(h.with_rels(cli, payload, rels))]
    result = cli(*args, "--body", h.generic_body(defs["plan:work-item"]))
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)["record"]


def test_once_prints_the_selector_line_and_wave_strip(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    h.create_generic_record(
        cli, defs, "plan:effort", subject=EFFORT,
        extra_payload={"goal": "ship the flow", "kind": "deliver"},
    )
    phase = h.create_generic_record(
        cli, defs, "plan:phase", subject=PHASE,
        extra_payload={"title": "first phase", "ordinal": 1, "effort": EFFORT},
    )
    h.transition(cli, "plan:phase", phase, "in_progress")
    _work_item(cli, defs, "item-a")
    script = REPO_ROOT / "dashboard" / "__main__.py"
    result = subprocess.run(
        [sys.executable, str(script), "--once"],
        capture_output=True, text=True, cwd=str(store),
    )
    assert result.returncode == 0, result.stderr
    assert "All phases" in result.stdout
    assert "● first phase" in result.stdout
    assert "w1" in result.stdout


def test_gates_once_shows_action_verbs_next_step_and_landing(store, cli, resolved_contract):
    defs = h.record_defs_by_id(resolved_contract)
    phase_slug = "gates-phase"
    branch = f"phase/{phase_slug}"
    git(store, "branch", "-M", "main")
    git(store, "checkout", "-qb", branch)
    (store / "gates-landing.txt").write_text("ahead\n")
    git(store, "add", "gates-landing.txt")
    git(store, "commit", "-qm", "landing-ahead")
    git(store, "checkout", "-q", "main")

    h.create_generic_record(
        cli, defs, "plan:effort", subject=EFFORT,
        extra_payload={"goal": "ship human gates", "kind": "deliver"},
    )
    body = (
        "## Problem\n\nNeed human gates.\n\n"
        "## Approach\n\nShow verbs, next step, and landing.\n\n"
        f"## Landing\n\n- Branch: `{branch}`\n"
        f"- Worktree: `/tmp/example--{phase_slug}`\n"
        "- Base: `main`\n\n"
        "## Exit criteria\n\nSelector shows landing.\n"
    )
    result = cli(
        "create", "--type", "plan:phase", "--subject", phase_slug,
        "--payload", json.dumps({"title": "Gates phase", "ordinal": 1, "effort": EFFORT}),
        "--body", body,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    phase = json.loads(result.stdout)["record"]
    h.transition(cli, "plan:phase", phase, "in_progress")

    payload = {
        "title": "quiet runner", "phase": phase_slug, "kind": "deliver",
        "assignee": "", "effort": EFFORT, "estimate_minutes": 10,
    }
    result = cli(
        "create", "--type", "plan:work-item", "--subject", "quiet-run",
        "--payload", json.dumps(payload),
        "--body", h.generic_body(defs["plan:work-item"]),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    task = json.loads(result.stdout)["record"]
    h.transition(cli, "plan:work-item", task, "in_progress")
    h.run_cli_48h_ago(
        store, "create", "--type", "run:assignment", "--subject", "quiet-run",
        "--payload", json.dumps({"work_item": task["subject"], "executor": "agent", "effort": EFFORT}),
        "--body", h.generic_body(defs["run:assignment"]),
    )
    h.create_generic_record(
        cli, defs, "plan:continuity-question", subject=EFFORT,
        extra_payload={"blocking": True, "scope": f"plan-review:{phase_slug}"},
    )

    script = REPO_ROOT / "dashboard" / "__main__.py"
    result = subprocess.run(
        [sys.executable, str(script), "--once"],
        capture_output=True, text=True, cwd=str(store),
        env={**os.environ, "COLUMNS": "120"},
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Review plan" in out
    assert "next: review the gates-phase plan (plan-phase)" in out
    selector = next(line for line in out.splitlines() if "Gates phase" in line)
    assert branch in selector
    assert "1 ahead" in selector
    assert "not merged" in selector
    assert "quiet" in out
