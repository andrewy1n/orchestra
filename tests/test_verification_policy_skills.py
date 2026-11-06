from __future__ import annotations

from pathlib import Path

from conftest import REPO_ROOT
from helpers import skill_text
from skill_extraction import extract_invocations

POLICY = REPO_ROOT / "skills/plan-phase/references/verification-policy.md"


def test_planning_examples_record_policy_separately_from_method() -> None:
    invocations = extract_invocations(skill_text("plan-phase"))
    acceptances = [
        inv["payload"]
        for inv in invocations
        if inv["type"] == "score:acceptance" and inv["subcommand"] == "create"
    ]
    assert acceptances
    assert all(payload["oracle_policy"] in ("none", "frozen") for payload in acceptances)
    assert any(
        payload["method"] == "tdd"
        and payload["oracle_policy"] == "none"
        and not payload.get("oracle_hashes")
        for payload in acceptances
    )
    assert any(
        payload["oracle_policy"] == "frozen" and payload["test_ids"] and payload["oracle_hashes"]
        for payload in acceptances
    )


def test_verification_examples_own_distinct_exit_requirements() -> None:
    text = (REPO_ROOT / "skills/plan-phase/references/task-shapes.md").read_text()
    implementation, verification = text.split("## Verification task")

    def requirements(section: str) -> set[str]:
        return {
            rid
            for inv in extract_invocations(section)
            if inv["type"] == "score:work-item" and inv["payload"]
            for rid in inv["payload"].get("requirements", [])
        }

    assert requirements(implementation).isdisjoint(requirements(verification))
    methods = [
        inv["payload"]["method"]
        for inv in extract_invocations(verification)
        if inv["type"] == "score:acceptance" and inv["payload"]
    ]
    assert methods and set(methods) == {"check"}


def test_policy_preserves_ordinary_tdd_and_parent_change_approval() -> None:
    text = POLICY.read_text()
    assert "Stamp the resolved `oracle_policy` on every new acceptance." in text
    assert "Require explicit parent approval before changing" in text
    assert "Its tests need not exist during planning." in text
    assert "Skip oracle authoring when no acceptance selects `frozen`." in text
    assert "Frozen file changes use the existing oracle amendment approval path." in text


def test_policy_covers_the_automated_method_policy_matrix() -> None:
    text = POLICY.read_text()
    for method in ("tdd", "check"):
        for policy in ("none", "frozen"):
            assert f"| `{method}` | `{policy}` |" in text
    assert "`manual` with `frozen` is invalid." in text


def test_all_workflow_stages_reference_the_same_policy() -> None:
    for name in ("settle-phase", "plan-phase", "execute-phase", "verify-work"):
        path: Path = REPO_ROOT / "skills" / name / "SKILL.md"
        assert "verification-policy.md" in path.read_text()
