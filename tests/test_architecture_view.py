from __future__ import annotations

import subprocess
from pathlib import Path

from canon_support import make_project
from interfaces.interfaces_support import invoke

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.composer.architecture import Scope
from orchestra.conductor.verification.standing_constraints import criterion_id
from orchestra.views.architecture import architecture_view, render_architecture

HEAD = "a" * 40
EFFORT = "arch-effort"


def _project(root: Path) -> Project:
    project = make_project(root)
    project.create(
        record_type="score:effort", subject=EFFORT, payload={"goal": "Arch", "kind": "deliver"}
    )
    return project


def _component(project: Project, name: str, area: str = "composer") -> Record:
    return project.create(
        record_type="composer:component",
        subject=name,
        payload={"area": area},
        body=f"## Responsibility\nOwns {name} data.\n",
    )


def _interface(project: Project, name: str, connects: list[str]) -> Record:
    return project.create(
        record_type="composer:interface",
        subject=name,
        payload={"connects": list(connects)},
        body=f"## Provides\nServes {name} callers.\n",
    )


def _decision(
    project: Project,
    title: str,
    affects: list[str],
    status: str = "accepted",
    rationale: str = "Keeps reads cheap.",
    enforced_by: list[str] | None = None,
) -> Record:
    payload: JsonObject = {"status": status, "affects": list(affects)}
    if enforced_by:
        payload["enforced_by"] = list(enforced_by)
    return project.create(
        record_type="composer:architecture-decision",
        subject=title,
        payload=payload,
        body=f"## Rationale\n{rationale}\n",
    )


def _constraint(project: Project, name: str, targets: list[str]) -> Record:
    return project.create(
        record_type="score:standing-constraint",
        subject=name,
        payload={
            "area": "composer",
            "rule": "Only adapters touch the store.",
            "check": "scripts/check-adapters",
            "targets": list(targets),
        },
        body="## Basis\nIsolation.\n",
    )


def _run(project: Project, constraint: Record, result: str) -> Record:
    return project.create(
        record_type="tuner:check-run",
        subject=f"{constraint['subject']}-check",
        payload={
            "criterion_id": criterion_id(constraint["id"]),
            "revision": HEAD,
            "result": result,
            "effort": EFFORT,
            "method": "check",
            "runner": "orchestra",
            "signed_by": "",
        },
    )


def _text(project: Project, scope: Scope | None = None) -> str:
    view = architecture_view(project.records(), scope, HEAD)
    return render_architecture(view)


def test_lists_each_component_and_interface_with_description(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _component(project, "views", area="interfaces")
    _interface(project, "record-api", ["records"])

    text = _text(project)

    assert "records" in text
    assert "Owns records data." in text
    assert "views" in text
    assert "Owns views data." in text
    assert "record-api" in text
    assert "Serves record-api callers." in text


def test_lists_components_grouped_by_area(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _component(project, "views", area="interfaces")

    text = _text(project)

    assert text.index("composer") < text.index("records") < text.index("interfaces")
    assert text.index("interfaces") < text.index("views")


def test_lists_accepted_decision_with_rationale_under_component(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _decision(project, "typed-records", ["records"], rationale="Keeps reads cheap.")

    text = _text(project)

    assert "typed-records" in text
    assert "Keeps reads cheap." in text
    assert "proposed" not in text


def test_lists_proposed_decision_marked_proposed(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _decision(project, "shard-records", ["records"], status="proposed", rationale="Scale later.")

    text = _text(project)

    line = next(line for line in text.splitlines() if "shard-records" in line)
    assert "proposed" in line
    assert "Scale later." in text


def test_lists_decision_under_interface(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _interface(project, "record-api", ["records"])
    _decision(project, "versioned-api", ["record-api"], rationale="Clients pin versions.")

    text = _text(project)

    assert text.index("record-api") < text.index("versioned-api")
    assert "Clients pin versions." in text


def test_lists_constraint_with_rule_check_outcome_version_and_revision(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    constraint = _constraint(project, "adapters-only", ["records"])
    _run(project, constraint, "pass")

    text = _text(project)

    assert "adapters-only" in text
    assert "Only adapters touch the store." in text
    assert "scripts/check-adapters" in text
    assert "verified" in text
    assert constraint["id"] in text
    assert HEAD in text


def test_lists_failing_constraint_as_violated(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    constraint = _constraint(project, "adapters-only", ["records"])
    _run(project, constraint, "fail")

    assert "violated" in _text(project)


def test_lists_constraint_without_check_run_as_unverified(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _constraint(project, "adapters-only", ["records"])

    text = _text(project)

    assert "unverified" in text
    assert "verified" not in text.replace("unverified", "")


def test_lists_constraint_enforcing_a_decision_under_that_component(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    constraint = _constraint(project, "adapters-only", [])
    _decision(project, "typed-records", ["records"], enforced_by=["adapters-only"])
    _run(project, constraint, "pass")

    text = _text(project)

    assert text.index("typed-records") < text.index("adapters-only")
    assert "verified" in text


def test_lists_only_scoped_component_when_scope_given(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")
    _component(project, "views", area="interfaces")

    text = _text(project, Scope("component", "views"))

    assert "views" in text
    assert "records" not in text


def test_lists_data_structure_usable_without_rendering(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _component(project, "records")

    view = architecture_view(project.records(), None, HEAD)

    assert view.get("revision") == HEAD
    areas = view["areas"]
    assert isinstance(areas, list)
    assert [area["name"] for area in areas if isinstance(area, dict)] == ["composer"]


def test_no_component_says_none_exists(tmp_path: Path) -> None:
    project = _project(tmp_path)

    text = _text(project)

    assert "no component" in text.lower()


def test_no_component_prints_only_that_line(tmp_path: Path) -> None:
    project = _project(tmp_path)

    text = _text(project)

    assert len([line for line in text.splitlines() if line.strip()]) == 1


def test_no_component_invents_no_interface_decision_or_constraint(tmp_path: Path) -> None:
    project = _project(tmp_path)

    text = _text(project).lower()

    for word in ("interface", "decision", "constraint", "proposed", "verified"):
        assert word not in text


def test_no_component_data_structure_is_empty(tmp_path: Path) -> None:
    project = _project(tmp_path)

    view = architecture_view(project.records(), None, HEAD)

    assert view.get("areas") == []
    assert view.get("interfaces") == []


def _committed_project(root: Path) -> Project:
    project = _project(root)
    (root / "base.txt").write_text("base\n")
    for args in (["add", "base.txt"], ["commit", "-qm", "base"]):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    return project


def test_lists_components_through_orchestra_view_command(tmp_path: Path) -> None:
    project = _committed_project(tmp_path)
    root = tmp_path
    _component(project, "records")
    _decision(project, "typed-records", ["records"], status="proposed")

    result = invoke("orchestra", ["view", "architecture", "--component", "records"], root)

    assert result.code == 0, result.err
    assert "Owns records data." in result.out
    assert "**typed-records** (proposed)" in result.out


def test_no_component_through_orchestra_view_command(tmp_path: Path) -> None:
    _committed_project(tmp_path)
    root = tmp_path

    result = invoke("orchestra", ["view", "architecture"], root)

    assert result.code == 0, result.err
    assert result.out == "No component exists.\n"


def _interface_scope_project(root: Path) -> Project:
    project = _project(root)
    _component(project, "records")
    _component(project, "views", area="interfaces")
    _interface(project, "record-api", ["records", "views"])
    _decision(project, "versioned-api", ["record-api"], rationale="Clients pin versions.")
    _constraint(project, "adapters-only", ["record-api"])
    return project


def test_interface_scope_lists_interface_decision_constraint_and_components(
    tmp_path: Path,
) -> None:
    project = _interface_scope_project(tmp_path)

    text = _text(project, Scope("interface", "record-api"))

    assert "Serves record-api callers." in text
    assert "versioned-api" in text
    assert "Clients pin versions." in text
    assert "adapters-only" in text
    assert "Only adapters touch the store." in text
    assert "records" in text
    assert "views" in text
    assert "No component exists." not in text


def test_interface_scope_through_orchestra_view_command(tmp_path: Path) -> None:
    project = _committed_project(tmp_path)
    _component(project, "records")
    _interface(project, "record-api", ["records"])
    _decision(project, "versioned-api", ["record-api"], rationale="Clients pin versions.")

    result = invoke("orchestra", ["view", "architecture", "--interface", "record-api"], tmp_path)

    assert result.code == 0, result.err
    assert "Serves record-api callers." in result.out
    assert "**versioned-api**: Clients pin versions." in result.out
    assert "records" in result.out
    assert "No component exists." not in result.out
