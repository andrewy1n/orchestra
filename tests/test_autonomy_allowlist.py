from __future__ import annotations

from pathlib import Path

import pytest
from canon_support import create, make_project

from orchestra.conductor import autonomy

CURLY = chr(0x2019)
UNRECOGNISED = [
    "Plan-review gates are preauthorized only when tests pass.",
    "Plan-review gates are preauthorized, but stop at every push.",
    "Plan-review gates are preauthorized for light phases.",
    "Plan-review gates are preauthorized for phase one alone.",
    "Plan-review gates are preauthorized if the phase is light.",
    "Plan and promote each next phase without asking when the phase is light.",
    "Plan and promote each next phase without asking until the beta ships.",
    "Plan and promote each next phase without asking, but only after a green check.",
    "Plan and promote each next phase without asking, otherwise ask.",
    "Only plan-review gates are preauthorized.",
    "Plan-review gates are preauthorized; wait for me before pushing.",
    "Plan-review gates are preauthorized; the user shouldn't be asked about merges.",
    f"Plan-review gates are preauthorized; don{CURLY}t wait for me.",
    "Do not promote the next phase without asking.",
    "Plan-review gates are not preauthorized.",
    "Never plan and promote each next phase without asking; ask first.",
    "Plan-review gates are preauthorized for the login phase only.",
]


@pytest.mark.parametrize("statement", UNRECOGNISED)
def test_r07_allowlist_a_restricted_or_scoped_statement_grants_nothing(statement: str) -> None:
    assert autonomy.classify(statement) is None


@pytest.mark.parametrize(
    ("statement", "level"),
    [
        ("Plan-review gates are pre-authorized by the user.", "auto-plan"),
        ("Plan-review gates for each phase are preauthorized.", "auto-plan"),
        ("Plan and execute each phase without asking.", "auto-plan"),
        (
            "Plan each phase and automatically execute through access-layer, db-backend, "
            "importer and cutover. PR merges still require approval.",
            "auto-plan",
        ),
        (
            "Plan and promote each next phase without asking once the current one closes; stop "
            "only for failures, needs-human findings, or a push or merge",
            "auto-phases",
        ),
        (
            "Plan-review gates are preauthorized; plan and promote each next phase without asking.",
            "auto-phases",
        ),
    ],
)
def test_r07_allowlist_a_fully_recognised_grant_maps(statement: str, level: str) -> None:
    assert autonomy.classify(statement) == level


def test_r08_allowlist_an_unrecognised_autonomy_constraint_is_reported_and_left_active(
    tmp_path: Path,
) -> None:
    project = make_project(tmp_path)
    create(project, "score:effort", "alpha", {"goal": "g", "kind": "deliver"})
    create(
        project,
        "score:constraint",
        "alpha-scoped",
        {
            "statement": "Plan-review gates are preauthorized for light phases.",
            "applies_to": "alpha",
            "effort": "alpha",
        },
    )
    mappings, notes = autonomy.plan_migration(project)
    assert mappings == []
    assert notes == ["alpha-scoped: mentions autonomy but is not a recognised grant; left alone"]
    autonomy.apply_migration(project, mappings)
    assert project.resolve("score:constraint", "alpha-scoped")["lifecycle_state"] == "active"
    assert project.resolve("score:effort", "alpha")["payload"].get("autonomy") is None


STRICT_EXECUTE_THROUGH = [
    "Plan each phase and automatically execute through a, b, but only after tests pass",
    "Plan each phase and automatically execute through x, and ask before every push",
    "Plan each phase and automatically execute through x unless a check fails",
    "Plan each phase and automatically execute through x, never on fridays",
    "Plan each phase and automatically execute through x, never",
    "Plan each phase and automatically execute through x and only",
]


@pytest.mark.parametrize("statement", STRICT_EXECUTE_THROUGH)
def test_r07_allowlist_strict_the_execute_through_list_holds_slugs_only(statement: str) -> None:
    assert autonomy.classify(statement) is None


@pytest.mark.parametrize(
    "statement",
    [
        "Plan-review gates for each light phase are preauthorized.",
        "Plan-review gates for every login phase are preauthorized.",
        "Plan and execute each login phase without asking.",
        "Plan and execute each light phase without asking.",
    ],
)
def test_r07_allowlist_strict_a_qualified_phase_is_not_a_blanket_grant(statement: str) -> None:
    assert autonomy.classify(statement, "record-diet") is None


def test_r07_allowlist_strict_only_the_effort_slug_may_qualify_a_phase() -> None:
    statement = "Plan-review gates for every record-diet phase are preauthorized by the user."
    assert autonomy.classify(statement, "record-diet") == "auto-plan"
    assert autonomy.classify(statement, "other-effort") is None
    assert autonomy.classify(statement) is None
