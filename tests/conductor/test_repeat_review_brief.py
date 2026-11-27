from __future__ import annotations

from pathlib import Path

import pytest
from conftest import git, make_git_repo

from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.verification.review import repeat_review
from orchestra.conductor.verification.review.review_brief import build_review_brief

PHASE = "p1"
FINDING_TEXT = "PRIOR-FINDING-MARKER handler skips the permission check"
EXEC_MARKER = "EXEC-REPORT-MARKER"
ASSESS_MARKER = "ASSESSMENT-MARKER"
ASSIGN_MARKER = "ASSIGNMENT-MARKER"


class FakeProject:
    def __init__(self, rows: dict[str, list[Record]]) -> None:
        self.rows = rows

    def list(self, record_type: str) -> list[Record]:
        return list(self.rows.get(record_type, []))

    def records(self) -> list[Record]:
        return [row for rows in self.rows.values() for row in rows]


def record(record_type: str, subject: str, payload: JsonObject, body: str = "") -> Record:
    return {
        "id": f"rec-{record_type}-{subject}-{len(body)}",
        "record_type": record_type,
        "subject": subject,
        "payload": payload,
        "body": body,
        "lifecycle_state": "active",
        "relationships": {},
        "revision": "sha256:0",
        "recorded_at": "2026-11-07T00:00:00+00:00",
    }


def review_run(revision: str, result: str = "fail", criterion: str = f"{PHASE}-review") -> Record:
    return record(
        "tuner:check-run",
        criterion,
        {
            "criterion_id": criterion,
            "revision": revision,
            "result": result,
            "method": "review",
            "signed_by": "",
            "evidence_kind": "review",
        },
        body=FINDING_TEXT,
    )


def finding() -> Record:
    return record(
        "tuner:finding",
        "review-finding",
        {"claim": FINDING_TEXT, "phase": PHASE, "needs": "human"},
        body=FINDING_TEXT,
    )


def project_with(*runs: Record, findings: bool = True) -> FakeProject:
    return FakeProject(
        {
            "score:work-item": [
                record("score:work-item", "task-a", {"phase": PHASE}, "Build the handler.")
            ],
            "conductor:execution-report": [
                record("conductor:execution-report", "task-a", {"phase": PHASE}, EXEC_MARKER)
            ],
            "conductor:assessment": [
                record("conductor:assessment", "task-a", {"phase": PHASE}, ASSESS_MARKER)
            ],
            "conductor:assignment": [
                record("conductor:assignment", "task-a", {"phase": PHASE}, ASSIGN_MARKER)
            ],
            "tuner:check-run": list(runs),
            "tuner:finding": [finding()] if findings else [],
        }
    )


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def repo() -> Path:
    root = make_git_repo()
    write(root, "lib/__init__.py", "")
    write(root, "lib/shared.py", "VALUE = 1\n")
    write(root, "app/__init__.py", "")
    write(root, "app/main.py", "from lib import shared\n\nprint(shared.VALUE)\n")
    write(root, "app/other.py", "import lib.shared\n")
    write(root, "cli/__init__.py", "")
    write(root, "cli/run.py", "from lib.shared import VALUE\n")
    write(root, "tools/unrelated.py", "import os\n")
    return root


def brief(root: Path, project: FakeProject, *, base: str, head: str) -> str:
    return build_review_brief(
        project,  # pyright: ignore[reportArgumentType]
        root,
        base=base,
        phase_head=head,
        phase=PHASE,
        suite_refusal="",
        architecture_review=lambda *_: "",
    )


def repaired(root: Path, path: str, text: str) -> tuple[str, str, str]:
    base = commit(root, "base")
    reviewed = commit_change(root, "reviewed.txt", "reviewed\n", "reviewed")
    write(root, path, text)
    head = commit(root, "repair")
    return base, reviewed, head


def section_of(text: str, heading: str) -> str:
    assert heading in text
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def commit_change(root: Path, path: str, text: str, message: str) -> str:
    write(root, path, text)
    return commit(root, message)


def test_prior_failed_review_returns_latest_failed_phase_review(repo: Path) -> None:
    failed = review_run("abc123")
    project = project_with(
        review_run("abc000", "pass"), failed, review_run("zzz", "fail", "other-review")
    )
    found = repeat_review.prior_failed_review(project, PHASE)  # pyright: ignore[reportArgumentType]
    assert found is not None
    assert found["payload"]["revision"] == "abc123"


def test_prior_failed_review_is_none_when_reviews_pass(repo: Path) -> None:
    project = project_with(review_run("abc123", "pass"))
    assert repeat_review.prior_failed_review(project, PHASE) is None  # pyright: ignore[reportArgumentType]


def test_affected_callers_lists_importers_of_changed_module(repo: Path) -> None:
    callers = repeat_review.affected_callers(repo, ["lib/shared.py"])
    assert sorted(callers) == ["app/main.py", "app/other.py", "cli/run.py"]


def test_affected_callers_excludes_files_that_do_not_import_the_module(repo: Path) -> None:
    callers = repeat_review.affected_callers(repo, ["lib/shared.py"])
    assert "tools/unrelated.py" not in callers


def test_affected_callers_ignores_non_python_changes(repo: Path) -> None:
    assert repeat_review.affected_callers(repo, ["README.md"]) == []


def test_needs_expansion_for_module_imported_from_two_packages(repo: Path) -> None:
    assert repeat_review.needs_expansion(repo, ["lib/shared.py"]) is True


def test_needs_expansion_false_for_module_with_callers_in_one_package(repo: Path) -> None:
    write(repo, "lib/local.py", "X = 1\n")
    write(repo, "app/uses_local.py", "from lib import local\n")
    write(repo, "app/also_local.py", "import lib.local\n")
    assert repeat_review.needs_expansion(repo, ["lib/local.py"]) is False


def test_needs_expansion_ignores_test_importers(repo: Path) -> None:
    write(repo, "lib/local.py", "X = 1\n")
    write(repo, "app/uses_local.py", "from lib import local\n")
    write(repo, "tests/test_local.py", "from lib import local\n")
    assert repeat_review.needs_expansion(repo, ["lib/local.py"]) is False


def test_needs_expansion_for_schema_snapshot(repo: Path) -> None:
    assert repeat_review.needs_expansion(repo, ["orchestra/schemas/score.json"]) is True


def test_needs_expansion_for_landing_module(repo: Path) -> None:
    assert repeat_review.needs_expansion(repo, ["orchestra/conductor/landing/gate.py"]) is True


def test_needs_expansion_false_for_unrelated_file(repo: Path) -> None:
    assert repeat_review.needs_expansion(repo, ["tools/unrelated.py"]) is False


def test_repeat_brief_includes_prior_review_with_findings_and_revision(repo: Path) -> None:
    base = commit(repo, "base")
    reviewed = commit_change(repo, "reviewed.txt", "r\n", "reviewed")
    head = commit_change(repo, "tools/unrelated.py", "import sys\n", "repair")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Prior review" in text
    assert FINDING_TEXT in text
    assert reviewed in text


def test_repeat_brief_repair_diff_spans_reviewed_revision_to_head(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "tools/unrelated.py", "import sys\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    section = section_of(text, "## Repair diff")
    assert "+import sys" in section
    assert "reviewed.txt" not in section


def test_repeat_brief_fails_when_the_reviewed_revision_is_unknown(repo: Path) -> None:
    base, _, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    unknown = "0" * 40
    with pytest.raises(RuntimeError, match="repair diff"):
        brief(repo, project_with(review_run(unknown)), base=base, head=head)


def test_repeat_brief_lists_affected_callers(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    section = section_of(text, "## Affected callers")
    assert "app/main.py" in section
    assert "cli/run.py" in section
    assert "tools/unrelated.py" not in section


def test_repeat_brief_excludes_execution_assessment_and_assignment_text(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    for marker in (EXEC_MARKER, ASSESS_MARKER, ASSIGN_MARKER):
        assert marker not in text


def test_first_review_brief_has_no_repeat_sections(repo: Path) -> None:
    base, _reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    text = brief(repo, project_with(), base=base, head=head)
    for heading in (
        "## Prior review",
        "## Repair diff",
        "## Affected callers",
        "## Expanded review",
    ):
        assert heading not in text


def test_brief_without_failed_review_equals_brief_with_only_passed_review(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    plain = brief(repo, project_with(), base=base, head=head)
    passed = brief(repo, project_with(review_run(reviewed, "pass")), base=base, head=head)
    assert passed == plain


def test_repeat_brief_keeps_phase_diff_section(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Phase diff" in text


def test_repeat_brief_expands_for_shared_module_change(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "lib/shared.py", "VALUE = 2\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Expanded review" in text


def test_repeat_brief_expands_for_schema_snapshot_change(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "pkg/schemas/thing.json", "{}\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Expanded review" in text


def test_repeat_brief_expands_for_landing_change(repo: Path) -> None:
    base, reviewed, head = repaired(repo, "orchestra/conductor/landing/gate.py", "X = 1\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Expanded review" in text


def test_repeat_brief_does_not_expand_for_single_package_module(repo: Path) -> None:
    write(repo, "lib/local.py", "X = 1\n")
    write(repo, "app/uses_local.py", "from lib import local\n")
    base, reviewed, head = repaired(repo, "lib/local.py", "X = 2\n")
    text = brief(repo, project_with(review_run(reviewed)), base=base, head=head)
    assert "## Prior review" in text
    assert "## Expanded review" not in text
