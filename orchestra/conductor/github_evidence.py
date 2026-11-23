from __future__ import annotations

import re
from dataclasses import dataclass

from orchestra.canon.types import JsonObject, JsonValue
from orchestra.conductor.merge_evidence import (
    CheckEvidence,
    CheckState,
    EvidenceError,
    EvidenceRequest,
    EvidenceSnapshot,
    RequiredCheck,
)
from orchestra.tools import ToolError, ToolTimeoutError
from orchestra.tools.github import GitHubGh
from orchestra.tools.github_urls import branch_rules_endpoint, pull_request_coordinates

_SHA = re.compile(r"[0-9a-f]{40}")
_TRANSIENT_LOOKUP = re.compile(
    r"\(HTTP (?:429|5[0-9]{2})\)|rate limit (?:already )?exceeded|exceeded a secondary rate limit"
    r"|connection reset by peer|network is unreachable|temporary failure in name resolution"
    r"|TLS handshake timeout|i/o timeout|unexpected EOF",
    re.IGNORECASE,
)
_PULL_REQUEST = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      state headRefOid baseRefName potentialMergeCommit { oid }
      baseRef {
        branchProtectionRule {
          requiresStatusChecks
          requiredStatusChecks { context app { databaseId } }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class _PullRequest:
    head: str
    base: str
    merge_commit: str | None
    protected_checks: tuple[RequiredCheck, ...]


def _object(value: JsonValue) -> JsonObject:
    if not isinstance(value, dict):
        raise EvidenceError("GitHub returned invalid CI evidence")
    return value


def _array(value: JsonValue) -> list[JsonValue]:
    if not isinstance(value, list):
        raise EvidenceError("GitHub returned an incomplete CI evidence list")
    return value


def _string(value: JsonValue) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError("GitHub returned an invalid CI evidence field")
    return value


def _revision(value: JsonValue) -> str:
    revision = _string(value)
    if not _SHA.fullmatch(revision):
        raise EvidenceError("GitHub returned an invalid commit SHA")
    return revision


def _source(value: JsonValue) -> str:
    if value is None or (type(value) is int and value == -1):
        return ""
    if type(value) is not int or value <= 0:
        raise EvidenceError("GitHub returned an invalid check source")
    return str(value)


class _GitHubEvidenceClient(GitHubGh):
    def pull(self, host: str, owner: str, repo: str, number: str) -> _PullRequest:
        payload = _object(
            self._json(
                "api",
                "--hostname",
                host,
                "graphql",
                "-f",
                f"query={_PULL_REQUEST}",
                "-f",
                f"owner={owner}",
                "-f",
                f"name={repo}",
                "-F",
                f"number={number}",
            )
        )
        if payload.get("errors"):
            raise EvidenceError("GitHub could not resolve pull request policy")
        repository = _object(_object(payload.get("data")).get("repository"))
        pull = _object(repository.get("pullRequest"))
        if pull.get("state") != "OPEN":
            raise EvidenceError("GitHub pull request is not open")
        protection = _object(pull.get("baseRef")).get("branchProtectionRule")
        checks: list[RequiredCheck] = []
        if protection is not None:
            rule = _object(protection)
            if rule.get("requiresStatusChecks") is True:
                for row in _array(rule.get("requiredStatusChecks")):
                    check = _object(row)
                    app = check.get("app")
                    source = _source(_object(app).get("databaseId")) if app is not None else ""
                    checks.append(RequiredCheck(_string(check.get("context")), source))
            elif rule.get("requiresStatusChecks") is not False:
                raise EvidenceError("GitHub could not resolve branch protection")
        merge = pull.get("potentialMergeCommit")
        return _PullRequest(
            _revision(pull.get("headRefOid")),
            _string(pull.get("baseRefName")),
            _revision(_object(merge).get("oid")) if merge is not None else None,
            tuple(checks),
        )

    def pages(self, host: str, path: str) -> list[JsonValue]:
        return _array(self._json("api", "--hostname", host, "--paginate", "--slurp", path))

    def rules(self, host: str, repository: str, branch: str) -> tuple[RequiredCheck, ...]:
        checks: list[RequiredCheck] = []
        for page in self.pages(host, branch_rules_endpoint(repository, branch)):
            for row in _array(page):
                rule = _object(row)
                kind = _string(rule.get("type"))
                if kind in ("workflows", "required_workflows", "required_workflow_status_checks"):
                    raise EvidenceError(
                        "GitHub rules require workflow evidence without a check context"
                    )
                if kind == "required_status_checks":
                    parameters = _object(rule.get("parameters"))
                    for entry in _array(parameters.get("required_status_checks")):
                        check = _object(entry)
                        checks.append(
                            RequiredCheck(
                                _string(check.get("context")), _source(check.get("integration_id"))
                            )
                        )
        return tuple(checks)

    def results(
        self, host: str, repository: str, revision: str, required: tuple[RequiredCheck, ...]
    ) -> dict[RequiredCheck, CheckEvidence]:
        if not required:
            return {}
        candidates: dict[RequiredCheck, list[CheckEvidence]] = {check: [] for check in required}
        base = f"{repository}/commits/{revision}"
        for page in self.pages(host, f"{base}/check-runs?filter=latest&per_page=100"):
            for row in _array(_object(page).get("check_runs")):
                run = _object(row)
                name = _string(run.get("name"))
                matching = [check for check in required if check.name == name]
                if not matching:
                    continue
                source = _source(_object(run.get("app")).get("id"))
                sha = _revision(run.get("head_sha"))
                if sha != revision:
                    raise EvidenceError("GitHub returned a check run for a different revision")
                link = run.get("details_url") or run.get("html_url")
                conclusion = run.get("conclusion")
                state: CheckState = "pending"
                if run.get("status") == "completed":
                    state = "pass" if conclusion in ("success", "neutral", "skipped") else "fail"
                for check in matching:
                    if not check.source or check.source == source:
                        candidates[check].append(
                            CheckEvidence(check, state, sha, _string(link) if link else "")
                        )
        for page in self.pages(host, f"{base}/status?per_page=100"):
            for row in _array(_object(page).get("statuses")):
                status = _object(row)
                name = _string(status.get("context"))
                for check in required:
                    if name != check.name:
                        continue
                    if check.source:
                        raise EvidenceError(f"GitHub cannot confirm the app for status {name!r}")
                    value = status.get("state")
                    state = (
                        "pass"
                        if value == "success"
                        else "pending"
                        if value == "pending"
                        else "fail"
                    )
                    target = status.get("target_url")
                    candidates[check].append(
                        CheckEvidence(check, state, revision, _string(target) if target else "")
                    )
        priority = {"fail": 0, "pending": 1, "pass": 2, "missing": 3}
        return {
            check: min(observations, key=lambda entry: priority[entry.state])
            for check, observations in candidates.items()
            if observations
        }


class GitHubActionsAdapter:
    def read(self, request: EvidenceRequest) -> EvidenceSnapshot:
        try:
            return self._read(request)
        except ToolError as error:
            if isinstance(error, ToolTimeoutError) or _TRANSIENT_LOOKUP.search(error.stderr):
                return EvidenceSnapshot(
                    "", unresolved=f"GitHub CI lookup failed: {error.stderr.strip() or error}"
                )
            raise

    def _read(self, request: EvidenceRequest) -> EvidenceSnapshot:
        host, owner, repo, number = pull_request_coordinates(request.pull_request_url)
        repository = f"repos/{owner}/{repo}"
        client = _GitHubEvidenceClient(request.root)
        pull = client.pull(host, owner, repo, number)
        head = pull.head
        required = tuple(
            dict.fromkeys((*pull.protected_checks, *client.rules(host, repository, pull.base)))
        )
        observed = client.results(host, repository, head, required) if required else {}
        at_merge = (
            client.results(host, repository, pull.merge_commit, required)
            if required and pull.merge_commit and pull.merge_commit != head
            else {}
        )
        latest_rules = client.rules(host, repository, pull.base)
        latest = client.pull(host, owner, repo, number)
        if latest.head != head:
            return EvidenceSnapshot(head, unresolved="pull request head changed during refresh")
        if latest != pull:
            return EvidenceSnapshot(
                head, unresolved="pull request base or test merge commit changed during refresh"
            )
        if set(required) != {*latest.protected_checks, *latest_rules}:
            return EvidenceSnapshot(
                head, unresolved="GitHub required checks changed during refresh"
            )
        if not required:
            return EvidenceSnapshot(
                head, unresolved=f"no required CI checks are configured for {pull.base}"
            )
        if at_merge:
            return EvidenceSnapshot(
                head,
                required,
                tuple(
                    at_merge.get(check)
                    or observed.get(check)
                    or CheckEvidence(check, "missing", head)
                    for check in required
                ),
                "required checks report on GitHub's test merge commit, which this adapter does not support",
            )
        results = tuple(
            observed.get(check, CheckEvidence(check, "missing", head)) for check in required
        )
        return EvidenceSnapshot(head, required, results)
