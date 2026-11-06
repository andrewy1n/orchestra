"""Read committed claims and allowlist data from a git revision.

No test run and no signature check. A dirty worktree is ignored because
every read goes through ``git show`` of a commit.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from orchestra.canon.project_config import ProjectConfigError, load_project_config_at_revision
from orchestra.canon.types import JsonObject, JsonValue
from orchestra.tools.errors import ToolError
from orchestra.tools.git import Git

MANIFEST_PATH = ".tuner/manifest.json"
ALLOWLIST_PATH = ".tuner/allowed_signers"
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
EvidenceKind = Literal["unit", "integration", "interaction"]


class ManifestError(Exception):
    """The revision is not a commit, or the manifest blob cannot be parsed."""


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    tests: tuple[str, ...]
    oracle_hashes: dict[str, str]
    support_files: tuple[str, ...] = ()
    evidence_kind: EvidenceKind = "unit"
    witness: Literal["tests", "human"] = "tests"
    signature: str = ""


@dataclass(frozen=True)
class Manifest:
    claims: tuple[Claim, ...]
    amendments: tuple[JsonObject, ...]
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
    return _git_text(cwd, "rev-parse", "--verify", f"{rev}^{{commit}}")


def merge_base(cwd: Path | str, at: str, main: str = "main") -> str:
    """Return ``git merge-base`` of ``at`` and ``main``."""
    return _git_text(cwd, "merge-base", at, main)


def load_manifest(cwd: Path | str, revision: str) -> Manifest:
    """Load claims from `.tuner/manifest.json` and runner argv from orchestra.toml.

    ``claims`` become ``Claim`` values (id, text, node-id tests, and
    ``oracle_hashes``). ``amendments`` are returned as parsed objects with
    no signature check. A missing blob, invalid JSON, or invalid project config
    raises ``ManifestError``.
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
    try:
        config = load_project_config_at_revision(cwd, commit)
    except ProjectConfigError as exc:
        raise ManifestError(str(exc)) from exc
    return _parse_manifest(parsed, runner=config.runner)


def load_allowlist(cwd: Path | str, revision: str) -> bytes:
    """Return the raw ``.tuner/allowed_signers`` blob at ``revision``."""
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


def _parse_manifest(parsed: JsonValue, *, runner: tuple[str, ...]) -> Manifest:
    if not isinstance(parsed, dict):
        raise ManifestError("manifest must be a JSON object")
    claims_raw = parsed.get("claims")
    if not isinstance(claims_raw, list):
        raise ManifestError("manifest claims must be a list")
    claims = tuple(_parse_claim(item, index) for index, item in enumerate(claims_raw))
    return Manifest(
        claims=claims,
        amendments=_parse_amendments(parsed.get("amendments")),
        runner=runner,
        support_files=_parse_support_files(parsed.get("support_files"), "support_files"),
    )


def _parse_support_files(raw: JsonValue, label: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    values = _string_items(raw)
    if values is None:
        raise ManifestError(f"{label} must be a list of paths")
    return values


def _parse_claim(raw: JsonValue, index: int) -> Claim:
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
    test_ids = _string_items(tests)
    if test_ids is None:
        raise ManifestError(f"claims[{index}].tests must be a list of node ids")
    if not isinstance(hashes, dict):
        raise ManifestError(f"claims[{index}].oracle_hashes must be an object")
    from orchestra.tuner.evidence_kind import DEFAULT_KIND, KINDS

    kind = raw.get("evidence_kind", DEFAULT_KIND)
    if not isinstance(kind, str) or kind not in KINDS:
        raise ManifestError(f"claims[{index}].evidence_kind must be one of {', '.join(KINDS)}")
    evidence_kind = _parse_evidence_kind(kind)
    witness = raw.get("witness", "tests")
    if witness not in ("tests", "human"):
        raise ManifestError(f"claims[{index}].witness must be 'tests' or 'human'")
    typed_witness: Literal["tests", "human"] = witness
    signature = raw.get("signature", "")
    if signature is None:
        signature = ""
    if not isinstance(signature, str):
        raise ManifestError(f"claims[{index}].signature must be a string")
    return Claim(
        id=claim_id,
        text=text,
        tests=test_ids,
        oracle_hashes=_parse_hashes(hashes, index),
        support_files=_parse_support_files(
            raw.get("support_files"),
            f"claims[{index}].support_files",
        ),
        evidence_kind=evidence_kind,
        witness=typed_witness,
        signature=signature,
    )


def _parse_hashes(hashes: Mapping[str, JsonValue], index: int) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for relpath, digest in hashes.items():
        if not relpath:
            raise ManifestError(f"claims[{index}].oracle_hashes has an empty path")
        if not isinstance(digest, str) or _HASH_RE.fullmatch(digest) is None:
            raise ManifestError(f"claims[{index}].oracle_hashes[{relpath!r}] must be sha256:<hex>")
        parsed[relpath] = digest
    return parsed


def _parse_amendments(raw: JsonValue) -> tuple[JsonObject, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManifestError("amendments must be a list")
    amendments: list[JsonObject] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ManifestError(f"amendments[{index}] is not an object")
        amendments.append(dict(item))
    return tuple(amendments)


def _string_items(raw: JsonValue) -> tuple[str, ...] | None:
    if not isinstance(raw, list):
        return None
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            return None
        values.append(item)
    return tuple(values)


def _parse_evidence_kind(value: str) -> EvidenceKind:
    if value == "unit":
        return "unit"
    if value == "integration":
        return "integration"
    if value == "interaction":
        return "interaction"
    raise AssertionError("evidence kind was validated")


def _show_blob(cwd: Path | str, revision: str, relpath: str) -> bytes:
    if not relpath or relpath.endswith("/"):
        raise FileNotFoundError(relpath)
    try:
        blob = Git(Path(cwd)).show_bytes(revision, relpath)
    except ToolError as exc:
        raise ManifestError("git is not available") from exc
    if blob is None:
        raise FileNotFoundError(relpath)
    return blob


def _git_text(cwd: Path | str, *args: str) -> str:
    try:
        result = Git(Path(cwd)).run("--no-pager", *args)
    except ToolError as exc:
        raise ManifestError("git is not available") from exc
    if result.returncode != 0:
        raise ManifestError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()
