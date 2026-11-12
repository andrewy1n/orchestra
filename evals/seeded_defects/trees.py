from __future__ import annotations

import subprocess
from pathlib import Path

_IDENTITY = ("-c", "user.name=case-tree", "-c", "user.email=case-tree@example.invalid")


class PatchDoesNotApply(Exception):
    def __init__(self, stderr: str) -> None:
        super().__init__(stderr)
        self.stderr = stderr


def _git(repo: Path, *args: str, stdin: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=stdin,
        capture_output=True,
        check=False,
    )


def _git_ok(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout.decode().strip()


def _apply(repo: Path, diff: bytes) -> None:
    result = _git(repo, "apply", "--binary", "-", stdin=diff)
    if result.returncode != 0:
        raise PatchDoesNotApply(result.stderr.decode(errors="replace"))


def build_case_tree(source_repo: Path, landing_commit: str, patch: Path | None, dest: Path) -> Path:
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(source_repo), str(dest)],
        check=True,
        capture_output=True,
    )
    landing = _git_ok(dest, "rev-parse", f"{landing_commit}^{{commit}}")
    parent = _git_ok(dest, "rev-parse", f"{landing}^")
    _git_ok(dest, "checkout", "--quiet", "--detach", parent)
    landed = _git(dest, "diff", "--binary", parent, landing)
    if landed.returncode != 0:
        raise RuntimeError(landed.stderr.decode(errors="replace"))
    _apply(dest, landed.stdout)
    if patch is not None:
        _apply(dest, patch.read_bytes())
    _git_ok(dest, "add", "-A")
    _git_ok(dest, *_IDENTITY, "commit", "--quiet", "--allow-empty", "-m", "case tree")
    for ref in _git_ok(dest, "for-each-ref", "--format=%(refname)").splitlines():
        _git_ok(dest, "update-ref", "-d", ref)
    _git_ok(dest, "remote", "remove", "origin")
    return dest
