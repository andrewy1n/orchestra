from pathlib import Path

import pytest

from orchestra.canon.types import JsonValue
from orchestra.conductor.github_evidence import GitHubActionsAdapter
from orchestra.conductor.github_pr import GitHubGh
from orchestra.conductor.merge_evidence import EvidenceRequest
from orchestra.tools import ToolError

HEAD = "a" * 40
NEXT = "b" * 40
LINK = "https://github.com/owner/repo/actions/runs/42/job/43"


def _read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    conclusion: str | None = None,
    include_run: bool = True,
    changed_head: bool = False,
    lookup_fails: bool = False,
    app: int = 42,
    merge_commit: bool = False,
    rules_changed: bool = False,
) -> tuple[str, str, str]:
    heads = iter((HEAD, NEXT if changed_head else HEAD))
    rule_sets: list[JsonValue] = [
        [[]],
        [
            [
                {
                    "type": "required_status_checks",
                    "parameters": {"required_status_checks": [{"context": "new"}]},
                }
            ]
        ]
        if rules_changed
        else [[]],
    ]

    def api(_self: GitHubGh, *args: str) -> JsonValue:
        if "graphql" in args:
            return {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "state": "OPEN",
                            "headRefOid": next(heads),
                            "baseRefName": "main",
                            "potentialMergeCommit": {"oid": NEXT} if merge_commit else None,
                            "baseRef": {
                                "branchProtectionRule": {
                                    "requiresStatusChecks": True,
                                    "requiredStatusChecks": [
                                        {"context": "test", "app": {"databaseId": 42}}
                                    ],
                                }
                            },
                        }
                    }
                }
            }
        if args[-1].endswith("/rules/branches/main"):
            if lookup_fails:
                raise ToolError("gh failed", args, 1, "rules lookup denied")
            return rule_sets.pop(0)
        if "/check-runs?" in args[-1]:
            revision = NEXT if f"/{NEXT}/" in args[-1] else HEAD
            runs: list[JsonValue] = (
                [
                    {
                        "id": 43,
                        "name": "test",
                        "head_sha": revision,
                        "app": {"id": app},
                        "conclusion": conclusion,
                        "status": "completed" if conclusion else "in_progress",
                        "details_url": LINK,
                    }
                ]
                if include_run and (not merge_commit or revision == NEXT)
                else []
            )
            return [{"check_runs": runs}]
        if "/status?" in args[-1]:
            return [{"statuses": []}]
        raise AssertionError(args)

    monkeypatch.setattr(GitHubGh, "_json", api)
    snapshot = GitHubActionsAdapter().read(
        EvidenceRequest(tmp_path, "https://github.com/owner/repo/pull/2", {})
    )
    result = snapshot.results[0] if snapshot.results else None
    return (result.state if result else "", result.run_url if result else "", snapshot.unresolved)


@pytest.mark.parametrize(
    ("conclusion", "expected"), [(None, "pending"), ("failure", "fail"), ("success", "pass")]
)
def test_required_check_state_and_run_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, conclusion: str | None, expected: str
) -> None:
    assert _read(tmp_path, monkeypatch, conclusion=conclusion) == (expected, LINK, "")


def test_required_check_without_a_result_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _read(tmp_path, monkeypatch, include_run=False) == ("missing", "", "")


def test_a_result_from_another_app_cannot_satisfy_a_required_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _read(tmp_path, monkeypatch, conclusion="success", app=99) == ("missing", "", "")


def test_head_change_leaves_ci_unresolved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert "head changed" in _read(tmp_path, monkeypatch, changed_head=True)[2]


def test_lookup_failure_leaves_ci_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert "rules lookup denied" in _read(tmp_path, monkeypatch, lookup_fails=True)[2]


def test_result_on_test_merge_commit_leaves_ci_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert _read(tmp_path, monkeypatch, conclusion="success", merge_commit=True) == (
        "pass",
        LINK,
        "required checks report on GitHub's test merge commit",
    )


def test_ruleset_change_leaves_ci_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert (
        "required checks changed"
        in _read(tmp_path, monkeypatch, conclusion="success", rules_changed=True)[2]
    )
