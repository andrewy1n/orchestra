import pytest

from canon_support import create, make_project, seed_effort
from test_hooks import (
    add_constraint,
    add_effort,
    claude_context,
    constraints_block,
    crowd_store,
    full_handoff,
)


@pytest.fixture(autouse=True)
def baseline_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ORCHESTRA_BASELINE_DIR", str(tmp_path / "baselines"))
    monkeypatch.delenv("CANON_STORE", raising=False)


@pytest.fixture
def repo(tmp_path):
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def close_effort_goal_only(project, slug):
    goal = project.resolve("score:effort", slug)
    project.supersede(goal["id"], payload={**goal["payload"], "status": "closed"})


def not_shown_line(ctx):
    lines = [line for line in ctx.splitlines() if "Not shown:" in line]
    return lines[0] if lines else ""


def test_r14_needs_human_finding_without_effort_reaches_start_context(
    repo, monkeypatch, capsys
):
    create(
        repo,
        "tuner:finding",
        "orphan-risk",
        {
            "claim": "Orphan claim needing a person",
            "basis": "b",
            "invalidated_when": "never",
            "effort": "",
            "needs": "human",
        },
    )
    assert "orphan-risk" in full_handoff(repo)
    ctx = claude_context(repo, monkeypatch, capsys)
    assert "orphan-risk" in ctx or "orphan-risk" in not_shown_line(ctx)


def test_r14_blocking_question_with_non_effort_subject_reaches_start_context(
    repo, monkeypatch, capsys
):
    create(
        repo,
        "score:continuity-question",
        "q-1",
        {"owner": "human", "blocking": True, "scope": "alpha"},
    )
    assert "q-1" in full_handoff(repo)
    ctx = claude_context(repo, monkeypatch, capsys)
    assert "q-1" in ctx or "q-1" in not_shown_line(ctx)


def test_r14_effortless_items_reach_start_context_when_efforts_are_crowded_out(
    repo, monkeypatch, capsys
):
    crowd_store(repo)
    create(
        repo,
        "tuner:finding",
        "orphan-risk",
        {
            "claim": "Orphan claim needing a person",
            "basis": "b",
            "invalidated_when": "never",
            "effort": "",
            "needs": "human",
        },
    )
    create(
        repo,
        "score:continuity-question",
        "q-1",
        {"owner": "human", "blocking": True, "scope": "alpha"},
    )
    handoff = full_handoff(repo)
    assert "orphan-risk" in handoff
    assert "q-1" in handoff
    ctx = claude_context(repo, monkeypatch, capsys)
    named = not_shown_line(ctx)
    assert "orphan-risk" in ctx or "orphan-risk" in named
    assert "q-1" in ctx or "q-1" in named


def test_r5_constraints_block_omits_constraints_when_goal_closed_position_open(
    repo, monkeypatch, capsys
):
    add_effort(repo, "bravo")
    add_constraint(repo, "alpha-rule", "Alpha stays small", "alpha")
    add_constraint(repo, "bravo-rule", "Bravo stays fast", "bravo")
    close_effort_goal_only(repo, "bravo")
    position = repo.resolve("score:position", "bravo")
    assert position["payload"].get("status") != "closed"
    ctx = claude_context(repo, monkeypatch, capsys)
    assert "Alpha stays small" in constraints_block(ctx)
    assert "Bravo stays fast" not in ctx
    assert "bravo-rule" not in ctx
