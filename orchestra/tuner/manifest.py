"""Read a committed claims manifest and allowlist from a git revision.

No test run and no signature check. A dirty worktree is ignored because
every read goes through ``git show`` of a commit.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

MANIFEST_PATH = ".affidavit/manifest.json"
ALLOWLIST_PATH = ".affidavit/allowed_signers"
DEFAULT_RUNNER = (
    "python3",
    "-m",
    "pytest",
    "-o",
    "junit_family=xunit1",
    "{tests}",
    "--junitxml={report}",
)

_HASH_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


class ManifestError(Exception):
    """The revision is not a commit, or the manifest blob cannot be parsed."""


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    tests: tuple[str, ...]
    oracle_hashes: dict[str, str]
    support_files: tuple[str, ...] = ()
    evidence_kind: str = "unit"
    witness: str = "tests"
    signature: str = ""


@dataclass(frozen=True)
class Manifest:
    claims: tuple[Claim, ...]
    amendments: tuple[dict[str, Any], ...]
    runner: tuple[str, ...]
    support_files: tuple[str, ...] = ()


def runner_digest(runner: Sequence[str]) -> str:
    """Return ``sha256:<hex>`` of canonical argv lines (one element per line)."""
    payload = ("\n".join(runner) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def frozen_support_files(manifest: Manifest, claim: Claim) -> tuple[str, ...]:
    """Union of manifest-global and claim-listed support paths, claim order last."""
    seen: list[str] = []
    for relpath in (*manifest.support_files, *claim.support_files):
        if relpath not in seen:
            seen.append(relpath)
    return tuple(seen)


def resolve_commit(cwd: Path | str, rev: str) -> str:
    """Return the commit SHA for ``rev``.

    Runs ``git rev-parse --verify <rev>^{commit}``. Raises ``ManifestError``
    when ``rev`` does not name a commit.
    """
    result = _run_git(cwd, "rev-parse", "--verify", f"{rev}^{{commit}}")
    return result.stdout.decode("utf-8").strip()


def merge_base(cwd: Path | str, at: str, main: str = "main") -> str:
    """Return ``git merge-base`` of ``at`` and ``main``."""
    result = _run_git(cwd, "merge-base", at, main)
    return result.stdout.decode("utf-8").strip()


def load_manifest(cwd: Path | str, revision: str) -> Manifest:
    """Load ``.affidavit/manifest.json`` from ``revision``.

    ``claims`` become ``Claim`` values (id, text, node-id tests, and
    ``oracle_hashes``). ``amendments`` are returned as parsed objects with
    no signature check. An absent ``runner`` is ``DEFAULT_RUNNER``. A present
    ``runner`` must be a non-empty argv list with ``{tests}`` and ``{report}``.
    A missing blob, invalid JSON, or bad runner raises ``ManifestError``.
    """
    commit = resolve_commit(cwd, revision)
    try:
        blob = _show_blob(cwd, commit, MANIFEST_PATH)
    except FileNotFoundError as exc:
        raise ManifestError(f"missing {MANIFEST_PATH} at {revision}") from exc
    try:
        parsed = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {MANIFEST_PATH} at {revision}") from exc
    return _parse_manifest(parsed)


def load_allowlist(cwd: Path | str, revision: str) -> bytes:
    """Return the raw ``.affidavit/allowed_signers`` blob at ``revision``."""
    commit = resolve_commit(cwd, revision)
    try:
        return _show_blob(cwd, commit, ALLOWLIST_PATH)
    except FileNotFoundError as exc:
        raise ManifestError(f"missing {ALLOWLIST_PATH} at {revision}") from exc


def hash_oracle_files(
    cwd: Path | str,
    revision: str,
    relpaths: Sequence[str],
) -> dict[str, str]:
    """Hash each path at ``revision`` via ``git show``.

    Values are ``sha256:<hex>`` of the blob bytes. A missing path raises
    ``FileNotFoundError``.
    """
    commit = resolve_commit(cwd, revision)
    out: dict[str, str] = {}
    for relpath in relpaths:
        blob = _show_blob(cwd, commit, relpath)
        out[relpath] = "sha256:" + hashlib.sha256(blob).hexdigest()
    return out


def _parse_manifest(parsed: Any) -> Manifest:
    if not isinstance(parsed, dict):
        raise ManifestError("manifest must be a JSON object")
    claims_raw = parsed.get("claims")
    if not isinstance(claims_raw, list):
        raise ManifestError("manifest claims must be a list")
    claims = tuple(_parse_claim(item, index) for index, item in enumerate(claims_raw))
    return Manifest(
        claims=claims,
        amendments=_parse_amendments(parsed.get("amendments")),
        runner=_parse_runner(parsed),
        support_files=_parse_support_files(parsed.get("support_files"), "support_files"),
    )


def _parse_runner(parsed: Mapping[str, Any]) -> tuple[str, ...]:
    if "runner" not in parsed:
        return DEFAULT_RUNNER
    raw = parsed["runner"]
    if (
        not isinstance(raw, list)
        or not raw
        or not all(isinstance(item, str) and item for item in raw)
        or sum(item == "{tests}" for item in raw) != 1
        or not any("{report}" in item for item in raw)
    ):
        raise ManifestError(
            "runner must be a non-empty argv list with {tests} and {report}"
        )
    return tuple(raw)


def _parse_support_files(raw: Any, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) and item for item in raw):
        raise ManifestError(f"{label} must be a list of paths")
    return tuple(raw)


def _parse_claim(raw: Any, index: int) -> Claim:
    if not isinstance(raw, dict):
        raise ManifestError(f"claims[{index}] is not an object")
    claim_id = raw.get("id")
    text = raw.get("text")
    tests = raw.get("tests")
    hashes = raw.get("oracle_hashes")
    if not isinstance(claim_id, str) or not claim_id:
        raise ManifestError(f"claims[{index}].id must be a non-empty string")
    if not isinstance(text, str):
        raise ManifestError(f"claims[{index}].text must be a string")
    if not isinstance(tests, list) or not all(isinstance(item, str) and item for item in tests):
        raise ManifestError(f"claims[{index}].tests must be a list of node ids")
    if not isinstance(hashes, dict):
        raise ManifestError(f"claims[{index}].oracle_hashes must be an object")
    from affidavit.evidence_kind import DEFAULT_KIND, KINDS

    kind = raw.get("evidence_kind", DEFAULT_KIND)
    if kind not in KINDS:
        raise ManifestError(
            f"claims[{index}].evidence_kind must be one of {', '.join(KINDS)}"
        )
    witness = raw.get("witness", "tests")
    if witness not in ("tests", "human"):
        raise ManifestError(f"claims[{index}].witness must be 'tests' or 'human'")
    signature = raw.get("signature", "")
    if signature is None:
        signature = ""
    if not isinstance(signature, str):
        raise ManifestError(f"claims[{index}].signature must be a string")
    return Claim(
        id=claim_id,
        text=text,
        tests=tuple(tests),
        oracle_hashes=_parse_hashes(hashes, index),
        support_files=_parse_support_files(
            raw.get("support_files"),
            f"claims[{index}].support_files",
        ),
        evidence_kind=kind,
        witness=witness,
        signature=signature,
    )


def _parse_hashes(hashes: Mapping[str, Any], index: int) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for relpath, digest in hashes.items():
        if not isinstance(relpath, str) or not relpath:
            raise ManifestError(f"claims[{index}].oracle_hashes has an empty path")
        if not isinstance(digest, str) or _HASH_RE.fullmatch(digest) is None:
            raise ManifestError(
                f"claims[{index}].oracle_hashes[{relpath!r}] must be sha256:<hex>"
            )
        parsed[relpath] = digest
    return parsed


def _parse_amendments(raw: Any) -> tuple[dict[str, Any], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManifestError("amendments must be a list")
    amendments: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ManifestError(f"amendments[{index}] is not an object")
        amendments.append(dict(item))
    return tuple(amendments)


def _show_blob(cwd: Path | str, revision: str, relpath: str) -> bytes:
    if not relpath or relpath.endswith("/"):
        raise FileNotFoundError(relpath)
    result = _run_git(cwd, "show", f"{revision}:{relpath}", check=False)
    if result.returncode != 0:
        raise FileNotFoundError(relpath)
    return result.stdout


def _run_git(
    cwd: Path | str,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "--no-pager", *args],
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ManifestError("git is not available") from exc
    if check and result.returncode != 0:
        err = result.stderr.decode("utf-8", "replace").strip()
        raise ManifestError(err or f"git {' '.join(args)} failed")
    return result
