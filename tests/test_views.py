import pytest

from canon_support import create, make_project, seed_effort
from orchestra import views


@pytest.fixture
def project(tmp_path):
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    return project


def work_item(project, subject, state_payload=None, **extra):
    payload = {
        "title": f"Title of {subject}",
        "phase": "p1",
        "kind": "deliver",
        "assignee": "",
        "effort": "alpha",
        **extra,
    }
    return create(project, "score:work-item", subject, payload)


def render(project, view, **kwargs):
    return views.render_view(views.VIEWS[view], views.load_records(project), **kwargs)


def test_handoff_has_goal_and_position_under_effort_heading(project):
    text = render(project, "handoff")
    assert text.startswith("# Project Handoff")
    assert "## alpha" in text
    assert "### Goal\n- **alpha**: Goal of alpha; deliver" in text
    assert "### Position\n- **alpha**: midway; effort" in text


def test_handoff_references_record_ids_without_file_links(project):
    text = render(project, "handoff")
    assert project.resolve("score:effort", "alpha")["id"] in text
    assert ".canon/" not in text
    assert "](" not in text


def test_handoff_has_no_store_state_line(project):
    assert "Store state" not in render(project, "handoff")


def test_handoff_lists_in_progress_work_item(project):
    item = work_item(project, "build-it")
    project.update(item["id"], transition="in_progress")
    text = render(project, "handoff")
    assert "### In Progress\n- **build-it**: Title of build-it; p1; deliver; alpha" in text


def test_handoff_omits_planned_work_item_from_in_progress(project):
    work_item(project, "later")
    assert "In Progress" not in render(project, "handoff")


def test_handoff_shows_blocking_question_only_when_blocking(project):
    create(
        project,
        "score:continuity-question",
        "which-db",
        {"owner": "human", "blocking": True, "scope": "alpha"},
    )
    create(
        project,
        "score:continuity-question",
        "naming",
        {"owner": "human", "blocking": False, "scope": "alpha"},
    )
    text = render(project, "handoff")
    assert "### Blocking Question" in text
    assert "which-db" in text
    assert "naming" not in text


def test_handoff_lists_latest_proof_and_open_backlog(project):
    create(
        project,
        "conductor:proof-packet",
        "p1",
        {"phase": "p1", "effort": "alpha", "revision": "abc123", "base": "main", "kind": "demo"},
    )
    create(project, "composer:idea", "later-idea", {"effort": "alpha", "status": "open"})
    create(project, "composer:idea", "done-idea", {"effort": "alpha", "status": "dismissed"})
    create(project, "composer:idea", "unplaced-idea", {"status": "open"})
    text = render(project, "handoff")
    assert "### Latest Proof\n- **p1**: p1; alpha; abc123; demo" in text
    assert "### Backlog\n- **later-idea**: alpha; open" in text
    assert "done-idea" not in text
    assert "unplaced-idea" not in text


def test_handoff_lists_needs_human_findings_and_unsigned_manual_checks(project):
    create(
        project,
        "tuner:finding",
        "risky",
        {
            "claim": "It is risky",
            "basis": "b",
            "invalidated_when": "never",
            "effort": "alpha",
            "needs": "human",
        },
    )
    create(
        project,
        "tuner:check-run",
        "ac-1",
        {
            "criterion_id": "ac-1",
            "revision": "r",
            "result": "pass",
            "effort": "alpha",
            "method": "manual",
            "signed_by": "",
        },
    )
    text = render(project, "handoff")
    assert "### Needs Human\n- **risky**: It is risky; human" in text
    assert "### Unsigned Manual Check\n- **ac-1**: ac-1; pass; manual" in text


def test_handoff_effort_flag_keeps_only_that_effort(project):
    seed_effort(project, "beta")
    text = render(project, "handoff", effort="beta")
    assert "## beta" in text
    assert "## alpha" not in text


def test_handoff_closed_effort_is_hidden(project):
    project.supersede(
        project.resolve("score:effort", "alpha")["id"],
        payload={"goal": "Goal of alpha", "kind": "deliver", "status": "closed"},
    )
    assert "### Goal" not in render(project, "handoff")


def test_empty_store_renders_no_matching_records(tmp_path):
    project = make_project(tmp_path / "empty")
    assert "_No matching records._" in render(project, "handoff")


def test_plan_groups_by_phase_and_lists_work_and_acceptance(project):
    work_item(project, "build-it")
    create(
        project,
        "score:acceptance",
        "build-it-ac1",
        {
            "method": "tdd",
            "phase": "p1",
            "effort": "alpha",
            "verify_command": "pytest -q",
            "requirement": "R1",
        },
    )
    text = render(project, "plan")
    assert text.startswith("# Project Plan")
    assert "## p1" in text
    assert "### Phase\n- **p1**: Phase one; 1; alpha" in text
    assert "### Work\n- **build-it**: Title of build-it; p1; deliver; alpha" in text
    assert "### Acceptance\n- **build-it-ac1**: R1; tdd; alpha; pytest -q" in text


def test_plan_orders_phases_by_ordinal(project):
    create(project, "score:phase", "a-late", {"title": "Late", "ordinal": 3, "effort": "alpha"})
    create(project, "score:phase", "z-early", {"title": "Early", "ordinal": 2, "effort": "alpha"})
    text = render(project, "plan")
    assert text.index("## p1") < text.index("## z-early") < text.index("## a-late")


def test_plan_effort_flag_filters_other_efforts(project):
    seed_effort(project, "beta", phase="b1")
    text = render(project, "plan", effort="beta")
    assert "## b1" in text
    assert "## p1" not in text


def test_status_shows_state_ready_wave_and_check_tally(project):
    first = work_item(project, "first")
    work_item(project, "second", depends_on=["first"])
    project.update(first["id"], transition="in_progress")
    project.update(first["id"], transition="done")
    for subject, result in (("first-ac1", "pass"), ("first-ac2", "fail")):
        create(
            project,
            "tuner:check-run",
            subject,
            {
                "criterion_id": subject,
                "revision": "r",
                "result": result,
                "effort": "alpha",
                "method": "check",
                "signed_by": "",
            },
        )
    text = render(project, "status")
    assert (
        "**first**: Title of first; p1; deliver; alpha; state: done; ready: True; wave: 1; criteria: 1 pass / 1 fail"
        in text
    )
    assert (
        "**second**: Title of second; p1; deliver; alpha; state: planned; ready: True; wave: 2; criteria: 0 pass / 0 fail"
        in text
    )


def test_status_marks_blocked_work_not_ready(project):
    work_item(project, "first")
    work_item(project, "second", depends_on=["first"])
    assert "state: planned; ready: False; wave: 2" in render(project, "status")


def test_verification_groups_by_subject_with_checks_and_findings(project):
    create(
        project,
        "score:acceptance",
        "ac-1",
        {
            "method": "check",
            "phase": "p1",
            "effort": "alpha",
            "verify_command": "true",
            "requirement": "R1",
        },
    )
    create(
        project,
        "tuner:check-run",
        "ac-1",
        {
            "criterion_id": "ac-1",
            "revision": "rev1",
            "result": "pass",
            "effort": "alpha",
            "method": "check",
            "signed_by": "",
        },
    )
    create(
        project,
        "tuner:finding",
        "f-1",
        {"claim": "c", "basis": "b", "invalidated_when": "w", "effort": "alpha", "needs": "none"},
    )
    text = render(project, "verification")
    assert text.startswith("# Project Verification")
    assert "## ac-1\n\n### Acceptance\n- **ac-1**: R1; check; alpha; true" in text
    assert "### Check\n- **ac-1**: ac-1; rev1; pass; check" in text
    assert "## f-1\n\n### Finding\n- **f-1**: c; b; w; none" in text


def test_brief_collects_work_item_acceptance_constraints_and_position(project):
    work_item(project, "build-it")
    create(
        project,
        "score:acceptance",
        "build-it-ac1",
        {
            "method": "tdd",
            "phase": "p1",
            "effort": "alpha",
            "verify_command": "pytest",
            "criterion": "It works",
        },
        body="Verbatim criterion text.",
    )
    create(
        project,
        "score:constraint",
        "stay-small",
        {"statement": "Keep it small", "applies_to": "all", "effort": "alpha"},
        body="## Basis\n\nConstraint basis.",
    )
    create(
        project,
        "score:acceptance",
        "other-ac1",
        {"method": "tdd", "phase": "p1", "effort": "alpha", "verify_command": "x"},
    )
    text = views.render_brief("build-it", views.load_records(project))
    assert text.startswith("# Brief: build-it")
    assert "## Work Item\n\n### build-it\n**title**: Title of build-it" in text
    assert "state: planned" in text
    assert "### build-it-ac1" in text
    assert "Verbatim criterion text." in text
    assert "### stay-small\n**statement**: Keep it small" in text
    assert "Constraint basis." in text
    assert "## Position" in text and "midway" in text
    assert "other-ac1" not in text
    assert "## Findings\n\n_None._" in text
    assert "## Unapplied Amendments\n\n_None._" in text


def test_brief_unknown_work_item_raises(project):
    with pytest.raises(views.ViewError, match="no work item found"):
        views.render_brief("ghost", views.load_records(project))


def run_cli(monkeypatch, capsys, project, *argv):
    from orchestra import cli

    monkeypatch.chdir(project.project_root)
    monkeypatch.delenv("CANON_STORE", raising=False)
    code = cli.main(list(argv))
    return code, capsys.readouterr()


def test_cli_handoff_prints_markdown(project, monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, project, "handoff")
    assert code == 0
    assert out.out.startswith("# Project Handoff")


def test_cli_view_effort_flag(project, monkeypatch, capsys):
    seed_effort(project, "beta", phase="b1")
    code, out = run_cli(monkeypatch, capsys, project, "view", "plan", "--effort", "beta")
    assert code == 0
    assert "## b1" in out.out and "## p1" not in out.out


def test_roadmap_effort_flag_filters_ideas(project):
    create(project, "composer:idea", "alpha-idea", {"status": "open", "effort": "alpha"})
    seed_effort(project, "beta")
    create(project, "composer:idea", "beta-idea", {"status": "open", "effort": "beta"})
    text = render(project, "roadmap", effort="alpha")
    assert "**alpha-idea**" in text
    assert "beta-idea" not in text


def test_roadmap_heads_each_group_with_its_area_and_collects_arealess_ideas(project):
    create(project, "composer:area", "dash", {"title": "Dashboard"}, "## Scope\n\nThe dashboard.")
    create(project, "composer:idea", "placed", {"status": "open", "area": "dash"})
    create(project, "composer:idea", "loose", {"status": "open"})
    text = render(project, "roadmap")
    assert "## dash\n\n### Area\n- **dash**: Dashboard" in text
    assert "## untriaged\n\n### Idea\n- **loose**" in text
    assert "### Area\n- **dash**" not in text.split("## untriaged")[1]


def test_group_key_keeps_empty_values_when_a_view_has_no_group_default():
    record = {"subject": "incidental-task", "payload": {"phase": ""}}
    assert views._group_key(record, views.PLAN, views.PLAN.roles[0]) == ""
    assert (
        views._group_key({"subject": "x", "payload": {}}, views.ROADMAP, views.ROADMAP.roles[1])
        == "untriaged"
    )


def test_cli_brief_unknown_subject_fails_on_stderr(project, monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, project, "brief", "ghost")
    assert code == 1
    assert "no work item found" in out.err
    assert out.out == ""


def test_cli_view_without_store_fails_cleanly(tmp_path, monkeypatch, capsys):
    from orchestra import cli

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CANON_STORE", raising=False)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["handoff"]) == 1
    assert "No artifact store" in capsys.readouterr().err


def test_r11_cli_handoff_keeps_ids_latest_proof_and_backlog(project, monkeypatch, capsys):
    create(
        project,
        "conductor:proof-packet",
        "p1",
        {"phase": "p1", "effort": "alpha", "revision": "abc123", "base": "main", "kind": "demo"},
    )
    create(project, "composer:idea", "later-idea", {"effort": "alpha", "status": "open"})
    code, out = run_cli(monkeypatch, capsys, project, "handoff")
    assert code == 0
    assert "### Latest Proof\n- **p1**: p1; alpha; abc123; demo _(id: rec-" in out.out
    assert "### Backlog\n- **later-idea**: alpha; open _(id: rec-" in out.out
    assert ".canon/" not in out.out
