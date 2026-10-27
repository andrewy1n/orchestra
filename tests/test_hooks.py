import io
import json

import pytest

from canon_support import create, make_project, point_effort_at, seed_effort
from orchestra import cli, hooks


@pytest.fixture(autouse=True)
def baseline_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.delenv("CANON_STORE", raising=False)


@pytest.fixture
def repo(tmp_path):
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def run_hook(monkeypatch, capsys, command, *flags, stdin):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin)))
    code = cli.main([command, *flags])
    out = capsys.readouterr().out
    return code, (json.loads(out) if out.strip() else None)


def claude_input(repo, **extra):
    return {"cwd": str(repo.project_root), "session_id": "s1", **extra}


def corrupt_reference(repo):
    point_effort_at(repo, "score:phase", "ghost-effort")


def test_hook_start_claude_wraps_protocol_and_handoff_in_additional_context(
    repo, monkeypatch, capsys
):
    code, out = run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=claude_input(repo))
    assert code == 0
    assert set(out) == {"hookSpecificOutput"}
    inner = out["hookSpecificOutput"]
    assert inner["hookEventName"] == "SessionStart"
    ctx = inner["additionalContext"]
    assert ctx.startswith(hooks.PROTOCOL)
    assert "# Project Handoff" in ctx
    assert "### Goal\n- **alpha**: Goal of alpha" in ctx


def test_hook_start_protocol_names_canon():
    text = hooks.PROTOCOL
    assert "v0.2" not in text
    assert "canon records" in text
    assert "orchestra handoff" in text
    assert "validate" in text


def test_hook_start_plain_mode_emits_additional_context_key(repo, monkeypatch, capsys):
    stdin = {"workspace_roots": [str(repo.project_root)], "conversation_id": "c1"}
    code, out = run_hook(monkeypatch, capsys, "hook-start", stdin=stdin)
    assert code == 0
    assert set(out) == {"additional_context"}
    assert "# Project Handoff" in out["additional_context"]


def test_hook_start_injects_active_constraints_for_focused_effort(repo, monkeypatch, capsys):
    create(
        repo,
        "score:constraint",
        "stay-small",
        {"statement": "Keep it small", "applies_to": "all", "effort": "alpha"},
        body="## Basis\n\nWhy.",
    )
    _, out = run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=claude_input(repo))
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "Active constraints:\n- **stay-small**: Keep it small" in ctx


def test_hook_start_truncates_oversized_handoff(repo, monkeypatch, capsys):
    for index in range(150):
        create(
            repo,
            "score:backlog-item",
            f"idea-{index:03d}-" + "x" * 80,
            {"effort": "alpha", "status": "open"},
        )
    _, out = run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=claude_input(repo))
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "handoff truncated" in ctx
    assert "orchestra handoff" in ctx


def test_hook_start_without_store_exits_silently(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    empty = tmp_path / "empty"
    empty.mkdir()
    code, out = run_hook(
        monkeypatch, capsys, "hook-start", "--claude", stdin={"cwd": str(empty), "session_id": "s"}
    )
    assert (code, out) == (0, None)


def test_hook_stop_without_store_exits_silently(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    empty = tmp_path / "empty"
    empty.mkdir()
    code, out = run_hook(
        monkeypatch, capsys, "hook-stop", "--claude", stdin={"cwd": str(empty), "session_id": "s"}
    )
    assert (code, out) == (0, None)


def test_hook_stop_allows_a_valid_store(repo, monkeypatch, capsys):
    code, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=claude_input(repo))
    assert (code, out) == (0, {})


def test_hook_stop_blocks_on_error_when_no_baseline_exists(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    code, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=claude_input(repo))
    assert code == 0
    assert out["decision"] == "block"
    assert "ghost-effort" in out["reason"]


def test_hook_stop_allows_errors_already_present_at_session_start(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    stdin = claude_input(repo)
    run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=stdin)
    code, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert (code, out) == (0, {})


def test_hook_stop_blocks_only_on_errors_new_since_session_start(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    stdin = claude_input(repo)
    run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=stdin)
    point_effort_at(repo, "score:position", "another-ghost")
    _, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert out["decision"] == "block"
    assert "another-ghost" in out["reason"]
    assert "ghost-effort" not in out["reason"]
    assert "already present when this session started" in out["reason"]


def test_hook_stop_ignores_stop_hook_active_loop(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    stdin = claude_input(repo, stop_hook_active=True)
    assert run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin) == (0, {})


def test_hook_stop_plain_mode_returns_followup_message(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    stdin = {
        "workspace_roots": [str(repo.project_root)],
        "conversation_id": "c1",
        "status": "completed",
        "loop_count": 0,
    }
    _, out = run_hook(monkeypatch, capsys, "hook-stop", stdin=stdin)
    assert "ghost-effort" in out["followup_message"]


def test_hook_stop_plain_mode_skips_incomplete_session(repo, monkeypatch, capsys):
    corrupt_reference(repo)
    stdin = {"workspace_roots": [str(repo.project_root)], "status": "aborted"}
    assert run_hook(monkeypatch, capsys, "hook-stop", stdin=stdin) == (0, {})


def test_hooks_never_write_records(repo, monkeypatch, capsys):
    def snapshot():
        return {
            str(p): p.read_bytes()
            for p in repo.store_path.rglob("*")
            if p.is_file()
        }

    before = snapshot()
    stdin = claude_input(repo)
    run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=stdin)
    run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert snapshot() == before
