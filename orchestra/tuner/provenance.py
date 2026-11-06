"""Git provenance rules for a claim's frozen oracle.

Git is the only authority. No record store is read.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from orchestra.tools.git import Git, GitResult
from orchestra.tuner.manifest import (
    ALLOWLIST_PATH,
    MANIFEST_PATH,
    Claim,
    Manifest,
    frozen_support_files,
)

AFTER = "provenance: oracle after implementation"
NON_ORACLE = "provenance: oracle commit touches non-oracle paths"
SHARED_SIGNER = "provenance: shared signer"


def check_provenance(
    cwd: Path | str,
    at_commit: str,
    base_commit: str,
    manifest: Manifest,
    claim: Claim,
    allowlist: bytes,
) -> str | None:
    """Return the failure reason for ``claim``, or ``None`` when provenance holds."""
    git = Git(Path(cwd))
    oracle = _oracle_commit(git, at_commit, list(claim.oracle_hashes))
    if oracle is None or oracle == at_commit or not _is_ancestor(git, oracle, base_commit):
        return AFTER
    allowed = {
        *claim.oracle_hashes,
        *frozen_support_files(manifest, claim),
        MANIFEST_PATH,
        ALLOWLIST_PATH,
    }
    if not set(_changed_paths(git, oracle)) <= allowed:
        return NON_ORACLE
    if _shares_signer(git, at_commit, base_commit, oracle, allowlist):
        return SHARED_SIGNER
    return None


def _run(git: Git, *args: str, config: tuple[str, ...] = ()) -> GitResult:
    prefix: list[str] = []
    for item in config:
        prefix.extend(["-c", item])
    return git.run("--no-pager", *prefix, *args)


def _oracle_commit(git: Git, at_commit: str, relpaths: list[str]) -> str | None:
    if not relpaths:
        return None
    listed = _run(git, "rev-list", at_commit)
    if listed.returncode != 0:
        return None
    order = {sha: index for index, sha in enumerate(listed.stdout.split())}
    newest: str | None = None
    for relpath in relpaths:
        added = _run(
            git,
            "log",
            "--no-renames",
            "--diff-filter=A",
            "--reverse",
            "--format=%H",
            at_commit,
            "--",
            relpath,
        )
        first = added.stdout.split()[:1]
        if added.returncode != 0 or not first:
            return None
        if newest is None or order[first[0]] < order[newest]:
            newest = first[0]
    return newest


def _is_ancestor(git: Git, ancestor: str, descendant: str) -> bool:
    return _run(git, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _changed_paths(git: Git, commit: str) -> list[str]:
    result = _run(git, "diff-tree", "--root", "-r", "--name-only", "--no-commit-id", "-z", commit)
    return [item for item in result.stdout.split("\0") if item]


def _shares_signer(
    git: Git,
    at_commit: str,
    base_commit: str,
    oracle: str,
    allowlist: bytes,
) -> bool:
    handle, name = tempfile.mkstemp(prefix="aff-signers-")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(allowlist)
        config = (f"gpg.ssh.allowedSignersFile={name}",)
        oracle_signers = _principals(git, config, "-1", oracle)
        if not oracle_signers:
            return False
        impl_signers = _principals(git, config, f"{base_commit}..{at_commit}")
        return bool(oracle_signers & impl_signers)
    finally:
        os.unlink(name)


def _principals(git: Git, config: tuple[str, ...], *revs: str) -> set[str]:
    result = _run(git, "log", "--format=%G?%x09%GS", *revs, config=config)
    principals: set[str] = set()
    for line in result.stdout.splitlines():
        status, _, principal = line.partition("\t")
        if status == "G" and principal:
            principals.add(principal)
    return principals
