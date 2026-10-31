import io
import json
import re

import pytest

from canon_support import create, make_project, seed_effort
from orchestra import cli, views
from orchestra.canon.project import Project
from orchestra.stage import hooks


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


def corrupt_reference(repo: Project, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    errors = ["invalid reference: ghost-effort"]
    monkeypatch.setattr(Project, "validate", lambda _project: list(errors))
    return errors


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
    corrupt_reference(repo, monkeypatch)
    code, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=claude_input(repo))
    assert code == 0
    assert out["decision"] == "block"
    assert "ghost-effort" in out["reason"]


def test_hook_stop_allows_errors_already_present_at_session_start(repo, monkeypatch, capsys):
    corrupt_reference(repo, monkeypatch)
    stdin = claude_input(repo)
    run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=stdin)
    code, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert (code, out) == (0, {})


def test_hook_stop_blocks_only_on_errors_new_since_session_start(repo, monkeypatch, capsys):
    errors = corrupt_reference(repo, monkeypatch)
    stdin = claude_input(repo)
    monkeypatch.setattr(
        hooks,
        "_load_baseline",
        lambda _root, _data: {"invalid reference: ghost-effort"},
    )
    errors[:] = ["invalid reference: ghost-effort", "invalid reference: another-ghost"]
    _, out = run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert out["decision"] == "block"
    assert "another-ghost" in out["reason"]
    assert "ghost-effort" not in out["reason"]
    assert "already present when this session started" in out["reason"]


def test_hook_stop_ignores_stop_hook_active_loop(repo, monkeypatch, capsys):
    corrupt_reference(repo, monkeypatch)
    stdin = claude_input(repo, stop_hook_active=True)
    assert run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin) == (0, {})


def test_hook_stop_plain_mode_returns_followup_message(repo, monkeypatch, capsys):
    corrupt_reference(repo, monkeypatch)
    stdin = {
        "workspace_roots": [str(repo.project_root)],
        "conversation_id": "c1",
        "status": "completed",
        "loop_count": 0,
    }
    _, out = run_hook(monkeypatch, capsys, "hook-stop", stdin=stdin)
    assert "ghost-effort" in out["followup_message"]


def test_hook_stop_plain_mode_skips_incomplete_session(repo, monkeypatch, capsys):
    corrupt_reference(repo, monkeypatch)
    stdin = {"workspace_roots": [str(repo.project_root)], "status": "aborted"}
    assert run_hook(monkeypatch, capsys, "hook-stop", stdin=stdin) == (0, {})


def test_hooks_never_write_records(repo, monkeypatch, capsys):
    def snapshot():
        return {
            str(p): p.read_bytes()
            for p in repo.store_path.rglob("*")
            if p.is_file() and "backups" not in p.parts
        }

    before = snapshot()
    stdin = claude_input(repo)
    run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=stdin)
    run_hook(monkeypatch, capsys, "hook-stop", "--claude", stdin=stdin)
    assert snapshot() == before


HOOK_BUDGET = 9000
LIVE_ROLES = {
    "Goal",
    "Position",
    "In Progress",
    "Blocking Question",
    "Needs Human",
    "Unsigned Manual Check",
}
CROWD = (
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
    "golf", "hotel", "india", "juliet", "kilo", "lima",
)
ID_LINK = re.compile(r"\(id: \[|\.canon/records/|rec-[0-9a-f]{8}-[0-9a-f]{4}-")


def phase_of(slug):
    return "p1" if slug == "alpha" else f"{slug}-p1"


def add_effort(project, slug):
    if slug != "alpha":
        seed_effort(project, slug, phase=phase_of(slug))


def fill_effort(project, slug, tasks=4):
    subjects = []
    for n in range(tasks):
        subject = f"{slug}-task-{n}"
        item = create(
            project,
            "score:work-item",
            subject,
            {
                "title": f"Title of {slug} task {n}: " + "detail " * 20,
                "phase": phase_of(slug),
                "kind": "deliver",
                "assignee": "",
                "effort": slug,
            },
        )
        project.update(item["id"], transition="in_progress")
        subjects.append(subject)
    create(
        project,
        "tuner:finding",
        f"{slug}-needs-human",
        {
            "claim": f"Claim about {slug}: " + "risk " * 20,
            "basis": "b",
            "invalidated_when": "never",
            "effort": slug,
            "needs": "human",
        },
    )
    create(
        project,
        "tuner:check-run",
        f"{slug}-manual-check",
        {
            "criterion_id": f"{slug}-manual-check",
            "revision": "r",
            "result": "pass",
            "effort": slug,
            "method": "manual",
            "signed_by": "",
        },
    )
    create(
        project,
        "conductor:proof-packet",
        f"{slug}-proof",
        {"phase": phase_of(slug), "effort": slug, "revision": "abc123", "base": "main", "kind": "demo"},
    )
    create(project, "composer:idea", f"{slug}-later-idea", {"effort": slug, "status": "open"})
    return subjects + [f"{slug}-needs-human", f"{slug}-manual-check"]


def crowd_store(project):
    owned = {}
    for slug in CROWD:
        add_effort(project, slug)
        owned[slug] = fill_effort(project, slug)
    return owned


def add_constraint(project, subject, statement, effort):
    create(
        project,
        "score:constraint",
        subject,
        {"statement": statement, "applies_to": "all", "effort": effort},
        body="## Basis\n\nWhy.",
    )


def close_effort(project, slug):
    goal = project.resolve("score:effort", slug)
    project.supersede(goal["id"], payload={**goal["payload"], "status": "closed"})
    position = project.resolve("score:position", slug)
    project.supersede(position["id"], payload={**position["payload"], "status": "closed"})


def claude_context(repo, monkeypatch, capsys):
    _, out = run_hook(monkeypatch, capsys, "hook-start", "--claude", stdin=claude_input(repo))
    return out["hookSpecificOutput"]["additionalContext"]


def plain_context(repo, monkeypatch, capsys):
    stdin = {"workspace_roots": [str(repo.project_root)], "conversation_id": "c1"}
    _, out = run_hook(monkeypatch, capsys, "hook-start", stdin=stdin)
    return out["additional_context"]


def full_handoff(repo):
    return views.render_view(views.HANDOFF, views.load_records(repo))


def effort_sections(ctx):
    sections = {}
    current = None
    for line in ctx.splitlines():
        if line.startswith("## "):
            words = line[3:].split()
            current = words[0] if words else ""
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines) for name, lines in sections.items()}


def section_start(ctx, slug):
    match = re.search(rf"^## {re.escape(slug)}\b", ctx, re.M)
    return match.start() if match else None


def constraints_block(ctx):
    assert "Active constraints:" in ctx
    rest = ctx[ctx.index("Active constraints:"):]
    match = re.search(r"^## ", rest, re.M)
    return rest[: match.start()] if match else rest


def test_r1_start_context_fits_nine_thousand_chars_when_full_handoff_exceeds_ten_thousand(
    repo, monkeypatch, capsys
):
    crowd_store(repo)
    assert len(full_handoff(repo)) > 10000
    assert len(claude_context(repo, monkeypatch, capsys)) <= HOOK_BUDGET


def test_r2_start_context_begins_with_protocol_text(repo, monkeypatch, capsys):
    crowd_store(repo)
    assert claude_context(repo, monkeypatch, capsys).startswith(hooks.PROTOCOL)


def test_r3_constraints_block_precedes_first_effort_section(repo, monkeypatch, capsys):
    add_constraint(repo, "stay-small", "Keep it small", "alpha")
    add_effort(repo, "bravo")
    ctx = claude_context(repo, monkeypatch, capsys)
    assert "Active constraints:" in ctx
    starts = [s for s in (section_start(ctx, slug) for slug in ("alpha", "bravo")) if s is not None]
    assert starts
    assert ctx.index("Active constraints:") < min(starts)


def test_r4_constraints_block_lists_constraints_from_every_live_effort(
    repo, monkeypatch, capsys
):
    add_effort(repo, "bravo")
    add_effort(repo, "charlie")
    add_constraint(repo, "alpha-rule", "Alpha stays small", "alpha")
    add_constraint(repo, "bravo-rule", "Bravo stays fast", "bravo")
    add_constraint(repo, "charlie-rule", "Charlie stays typed", "charlie")
    block = constraints_block(claude_context(repo, monkeypatch, capsys))
    assert "Alpha stays small" in block
    assert "Bravo stays fast" in block
    assert "Charlie stays typed" in block


def test_r5_constraints_block_omits_constraints_of_closed_efforts(repo, monkeypatch, capsys):
    add_effort(repo, "bravo")
    add_constraint(repo, "alpha-rule", "Alpha stays small", "alpha")
    add_constraint(repo, "bravo-rule", "Bravo stays fast", "bravo")
    close_effort(repo, "bravo")
    ctx = claude_context(repo, monkeypatch, capsys)
    assert "Alpha stays small" in constraints_block(ctx)
    assert "Bravo stays fast" not in ctx
    assert "bravo-rule" not in ctx


def test_r6_effort_sections_show_only_live_roles(repo, monkeypatch, capsys):
    fill_effort(repo, "alpha", tasks=1)
    create(
        repo,
        "score:continuity-question",
        "alpha",
        {"owner": "human", "blocking": True, "scope": "alpha"},
    )
    ctx = claude_context(repo, monkeypatch, capsys)
    sections = effort_sections(ctx)
    headings = {
        line[4:].strip()
        for body in sections.values()
        for line in body.splitlines()
        if line.startswith("### ")
    }
    assert headings <= LIVE_ROLES
    assert headings == LIVE_ROLES
    assert "### Blocking Question" in sections["alpha"]
    assert "alpha-proof" not in sections["alpha"]
    assert "alpha-later-idea" not in sections["alpha"]


def test_r7_start_context_has_no_record_id_links(repo, monkeypatch, capsys):
    fill_effort(repo, "alpha")
    add_constraint(repo, "stay-small", "Keep it small", "alpha")
    ctx = claude_context(repo, monkeypatch, capsys)
    assert ID_LINK.search(ctx) is None


def test_r8_over_budget_start_context_omits_whole_effort_sections_only(
    repo, monkeypatch, capsys
):
    owned = crowd_store(repo)
    ctx = claude_context(repo, monkeypatch, capsys)
    shown = effort_sections(ctx)
    included = [slug for slug in CROWD if slug in shown]
    omitted = [slug for slug in CROWD if slug not in shown]
    assert included
    assert omitted
    for slug in included:
        assert f"Goal of {slug}" in ctx
        assert [s for s in owned[slug] if s not in ctx] == []
    for slug in omitted:
        assert [s for s in owned[slug] if s in ctx] == []
        assert f"Goal of {slug}" not in ctx


def test_r9_each_omitted_effort_is_named_on_a_line_pointing_to_its_effort_handoff(
    repo, monkeypatch, capsys
):
    crowd_store(repo)
    ctx = claude_context(repo, monkeypatch, capsys)
    shown = effort_sections(ctx)
    omitted = [slug for slug in CROWD if slug not in shown]
    assert omitted
    lines = ctx.splitlines()
    for slug in omitted:
        pointers = [
            line
            for line in lines
            if re.search(rf"\b{re.escape(slug)}\b", line)
            and (
                f"orchestra handoff --effort {slug}" in line
                or "orchestra handoff --effort <slug>" in line
            )
        ]
        assert pointers, slug


def test_r10_effort_sections_follow_position_recorded_at_newest_first(
    tmp_path, monkeypatch, capsys
):
    project = make_project(tmp_path / "repo")
    stamps = iter(
        ("2026-01-02T00:00:00+00:00",) * 3
        + ("2026-01-01T00:00:00+00:00",) * 3
        + ("2026-01-03T00:00:00+00:00",) * 3
    )
    monkeypatch.setattr("orchestra.canon.record.now", lambda: next(stamps))
    for slug in ("alpha", "bravo", "charlie"):
        seed_effort(project, slug, phase=phase_of(slug))
    from orchestra.canon.record import now

    monkeypatch.setattr("orchestra.canon.record.now", now)
    monkeypatch.chdir(project.project_root)
    ctx = claude_context(project, monkeypatch, capsys)
    starts = [section_start(ctx, slug) for slug in ("charlie", "alpha", "bravo")]
    assert None not in starts
    assert starts == sorted(starts)


def test_r11_orchestra_handoff_keeps_every_effort_and_id_links_beyond_the_hook_budget(
    repo, monkeypatch, capsys
):
    crowd_store(repo)
    monkeypatch.chdir(repo.project_root)
    assert cli.main(["handoff"]) == 0
    text = capsys.readouterr().out
    assert len(text) > 10000
    assert all(section_start(text, slug) is not None for slug in CROWD)
    assert ID_LINK.search(text)
    assert "### Latest Proof" in text
    assert "### Backlog" in text


def test_r12_plain_start_context_matches_claude_budget_and_content(repo, monkeypatch, capsys):
    crowd_store(repo)
    claude = claude_context(repo, monkeypatch, capsys)
    plain = plain_context(repo, monkeypatch, capsys)
    assert plain == claude
    assert len(plain) <= HOOK_BUDGET
    assert ID_LINK.search(plain) is None
