"""Re-execute frozen oracle tests at two revisions.

Reads manifests, allowlists, and oracle blobs from git. Does not read a
record store.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from affidavit.amendment import authorize
from affidavit.evidence_kind import kind_allows_runner
from affidavit.human_claim import verify_claim_signature
from affidavit.manifest import (
    Claim,
    Manifest,
    frozen_support_files,
    hash_oracle_files,
    load_allowlist,
    load_manifest,
    merge_base,
    resolve_commit,
    runner_digest,
)
from affidavit.provenance import check_provenance
from affidavit.runner import run_tests


def run_verdict(
    cwd: Path | str,
    at: str,
    base: str | None,
    claim_ids: Sequence[str],
    provenance: bool = False,
) -> dict[str, Any]:
    """Judge ``claim_ids`` by re-executing their oracle tests.

    When ``base`` is omitted, the base revision is ``merge_base(cwd, at)``.
    A claim passes only when the allowlists match, amendments authorize any
    test-id or hash change, oracle blobs hash to that revision's
    ``oracle_hashes``, every base witness is ``assertion_failed``, every head
    witness is ``passed``, and a confirmation run in the same worktree agrees.
    """
    root = Path(cwd)
    base_rev = base if base else merge_base(root, at)
    at_commit = resolve_commit(root, at)
    base_commit = resolve_commit(root, base_rev)
    at_manifest = load_manifest(root, at_commit)
    base_manifest = load_manifest(root, base_commit)
    at_allow = load_allowlist(root, at_commit)
    base_allow = load_allowlist(root, base_commit)
    at_by_id = {claim.id: claim for claim in at_manifest.claims}
    base_by_id = {claim.id: claim for claim in base_manifest.claims}

    provenance_fails: dict[str, str] = {}
    if provenance:
        for claim_id in claim_ids:
            head_claim = at_by_id.get(claim_id)
            if head_claim is None:
                continue
            reason = check_provenance(
                root, at_commit, base_commit, at_manifest, head_claim, at_allow
            )
            if reason is not None:
                provenance_fails[claim_id] = reason

    if base_allow != at_allow:
        claims = [
            _fail(claim_id, provenance_fails.get(claim_id, "allowlist changed"))
            for claim_id in claim_ids
        ]
        return _payload(claims)

    base_runner_digest = runner_digest(base_manifest.runner)
    head_runner_digest = runner_digest(at_manifest.runner)

    verdicts: list[dict[str, str] | None] = [None] * len(claim_ids)
    pending: list[tuple[int, str, Claim, Claim]] = []
    for index, claim_id in enumerate(claim_ids):
        if claim_id in provenance_fails:
            verdicts[index] = _fail(claim_id, provenance_fails[claim_id])
            continue
        base_claim = base_by_id.get(claim_id)
        head_claim = at_by_id.get(claim_id)
        if head_claim is not None and head_claim.witness == "human":
            verdicts[index] = _human_verdict(head_claim, at_allow)
            continue
        if base_claim is None or head_claim is None:
            verdicts[index] = _fail(claim_id, "missing claim")
            continue
        if not (
            kind_allows_runner(head_claim.evidence_kind, base_manifest.runner)
            and kind_allows_runner(head_claim.evidence_kind, at_manifest.runner)
        ):
            verdicts[index] = _fail(
                claim_id,
                f"evidence_kind: {head_claim.evidence_kind} requires an "
                f"{head_claim.evidence_kind} runner template",
            )
            continue
        try:
            base_support = _support_hashes(root, base_commit, base_manifest, base_claim)
            head_support = _support_hashes(root, at_commit, at_manifest, head_claim)
        except FileNotFoundError:
            verdicts[index] = _fail(claim_id, "hash mismatch")
            continue
        allowed, reason = authorize(
            _mapping(base_claim, base_support, base_runner_digest),
            _mapping(head_claim, head_support, head_runner_digest),
            at_manifest.amendments,
            base_allow,
            at_allow,
        )
        if not allowed:
            verdicts[index] = _fail(claim_id, reason)
            continue
        if not _hashes_match(root, base_commit, base_claim) or not _hashes_match(
            root, at_commit, head_claim
        ):
            verdicts[index] = _fail(claim_id, "hash mismatch")
            continue
        pending.append((index, claim_id, base_claim, head_claim))

    if pending:
        _judge_pending(
            root,
            base_commit,
            at_commit,
            base_manifest.runner,
            at_manifest.runner,
            pending,
            verdicts,
        )

    claims = [item for item in verdicts if item is not None]
    return _payload(claims)


def _payload(claims: list[dict[str, str]]) -> dict[str, Any]:
    if any(item["result"] == "fail" for item in claims):
        result = "fail"
    elif any(item["result"] == "unstable" for item in claims):
        result = "unstable"
    else:
        result = "pass"
    return {"result": result, "claims": claims}


def _fail(claim_id: str, reason: str) -> dict[str, str]:
    return {"id": claim_id, "result": "fail", "reason": reason}


def _human_verdict(claim: Claim, allowlist: bytes) -> dict[str, str]:
    if not claim.signature:
        return _fail(claim.id, "human signature missing")
    if not verify_claim_signature(claim.id, claim.text, claim.signature, allowlist):
        return _fail(claim.id, "human signature invalid")
    return {"id": claim.id, "result": "pass"}


def _mapping(
    claim: Claim,
    support_hashes: dict[str, str],
    digest: str,
) -> dict[str, Any]:
    return {
        "id": claim.id,
        "tests": list(claim.tests),
        "oracle_hashes": dict(claim.oracle_hashes),
        "support_hashes": dict(support_hashes),
        "runner_digest": digest,
    }


def _support_hashes(
    cwd: Path,
    revision: str,
    manifest: Manifest,
    claim: Claim,
) -> dict[str, str]:
    relpaths = frozen_support_files(manifest, claim)
    if not relpaths:
        return {}
    return hash_oracle_files(cwd, revision, relpaths)


def _hashes_match(cwd: Path, revision: str, claim: Claim) -> bool:
    relpaths = list(claim.oracle_hashes)
    try:
        actual = hash_oracle_files(cwd, revision, relpaths)
    except FileNotFoundError:
        return False
    return actual == claim.oracle_hashes


def _union(groups: Any) -> list[str]:
    nodes: list[str] = []
    for group in groups:
        for node in group:
            if node not in nodes:
                nodes.append(node)
    return nodes


def _judge_pending(
    root: Path,
    base_commit: str,
    head_commit: str,
    base_runner: Sequence[str],
    head_runner: Sequence[str],
    pending: Sequence[tuple[int, str, Claim, Claim]],
    verdicts: list[dict[str, str] | None],
) -> None:
    base_ids = _union(claim.tests for _, _, claim, _ in pending)
    head_ids = _union(claim.tests for _, _, _, claim in pending)
    base_tree = _checkout(root, base_commit)
    head_tree = _checkout(root, head_commit)
    try:
        base_first = _outcomes(_worktree(base_tree), base_ids, base_runner)
        head_first = _outcomes(_worktree(head_tree), head_ids, head_runner)
        viable: list[tuple[int, str, Claim, Claim]] = []
        for index, claim_id, base_claim, head_claim in pending:
            if _viable(base_claim.tests, head_claim.tests, base_first, head_first):
                viable.append((index, claim_id, base_claim, head_claim))
            elif not _assertion_red(base_claim.tests, base_first):
                verdicts[index] = _fail(claim_id, "not assertion")
            else:
                verdicts[index] = _fail(claim_id, "tests failed")
        if not viable:
            return
        confirm_base = _union(claim.tests for _, _, claim, _ in viable)
        confirm_head = _union(claim.tests for _, _, _, claim in viable)
        base_second = _outcomes(_worktree(base_tree), confirm_base, base_runner)
        head_second = _outcomes(_worktree(head_tree), confirm_head, head_runner)
        for index, claim_id, base_claim, head_claim in viable:
            if _disagrees(base_claim.tests, base_first, base_second) or _disagrees(
                head_claim.tests, head_first, head_second
            ):
                verdicts[index] = {"id": claim_id, "result": "unstable"}
            else:
                verdicts[index] = {"id": claim_id, "result": "pass"}
    finally:
        _remove(root, base_tree)
        _remove(root, head_tree)


def _outcomes(
    worktree: Path | None,
    test_ids: Sequence[str],
    runner: Sequence[str],
) -> dict[str, str]:
    if worktree is None:
        return {test_id: "not_run" for test_id in test_ids}
    if not test_ids:
        return {}
    with _silence_stdio():
        return run_tests(worktree, test_ids, runner)


@contextmanager
def _silence_stdio() -> Iterator[None]:
    devnull = os.open(os.devnull, os.O_WRONLY)
    saved_out = os.dup(1)
    saved_err = os.dup(2)
    try:
        os.dup2(devnull, 1)
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(saved_out)
        os.close(saved_err)
        os.close(devnull)


def _assertion_red(tests: Sequence[str], outcomes: dict[str, str]) -> bool:
    return bool(tests) and all(
        outcomes.get(test_id) == "assertion_failed" for test_id in tests
    )


def _head_passed(tests: Sequence[str], outcomes: dict[str, str]) -> bool:
    return bool(tests) and all(outcomes.get(test_id) == "passed" for test_id in tests)


def _viable(
    base_tests: Sequence[str],
    head_tests: Sequence[str],
    base_outcomes: dict[str, str],
    head_outcomes: dict[str, str],
) -> bool:
    return _assertion_red(base_tests, base_outcomes) and _head_passed(
        head_tests, head_outcomes
    )


def _disagrees(
    tests: Sequence[str],
    first: dict[str, str],
    second: dict[str, str],
) -> bool:
    return any(second.get(test_id) != first.get(test_id) for test_id in tests)


def _checkout(cwd: Path, commit: str) -> tuple[Path, Path] | None:
    parent = Path(tempfile.mkdtemp(prefix="aff-verdict-"))
    worktree = parent / "wt"
    added = subprocess.run(
        ["git", "-C", str(cwd), "worktree", "add", "--detach", str(worktree), commit],
        capture_output=True,
    )
    if added.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        return None
    return parent, worktree


def _worktree(checked: tuple[Path, Path] | None) -> Path | None:
    if checked is None:
        return None
    return checked[1]


def _remove(cwd: Path, checked: tuple[Path, Path] | None) -> None:
    if checked is None:
        return
    parent, worktree = checked
    subprocess.run(
        ["git", "-C", str(cwd), "worktree", "remove", "--force", str(worktree)],
        capture_output=True,
    )
    shutil.rmtree(parent, ignore_errors=True)
