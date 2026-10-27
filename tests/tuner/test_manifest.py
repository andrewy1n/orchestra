"""Committed manifest, allowlist, and oracle hashes from a git revision."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from affidavit.manifest import (
    ManifestError,
    frozen_support_files,
    hash_oracle_files,
    load_allowlist,
    load_manifest,
    merge_base,
    resolve_commit,
    runner_digest,
)

ORACLE_REL = "tests/test_oracle.py"
ORACLE_V1 = b"def test_one():\n    assert True\n"
ORACLE_V2 = b"def test_one():\n    assert 1 == 1\n"
ALLOWLIST_V1 = b"alice ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOne\n"
ALLOWLIST_V2 = b"alice ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyTwo\n"
NODE_ID = "tests/test_oracle.py::test_one"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


_OMIT = object()


def _manifest_doc(
    oracle: bytes,
    *,
    claim_id: str = "claim-widget",
    runner: object = _OMIT,
    support_files: object = _OMIT,
    claim_support_files: object = _OMIT,
) -> dict:
    claim: dict = {
        "id": claim_id,
        "text": "The widget returns one.",
        "tests": [NODE_ID],
        "oracle_hashes": {ORACLE_REL: _sha256(oracle)},
    }
    if claim_support_files is not _OMIT:
        claim["support_files"] = claim_support_files
    doc = {
        "claims": [claim],
        "amendments": [
            {
                "id": "amend-1",
                "claim_id": claim_id,
                "signature": "not-a-real-signature",
            }
        ],
    }
    if runner is not _OMIT:
        doc["runner"] = runner
    if support_files is not _OMIT:
        doc["support_files"] = support_files
    return doc


def _init(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    return root


def _write_tree(
    root: Path,
    oracle: bytes,
    allowlist: bytes,
    claim_id: str = "claim-widget",
    runner: object = _OMIT,
    support_files: object = _OMIT,
    claim_support_files: object = _OMIT,
) -> None:
    affidavit = root / ".affidavit"
    affidavit.mkdir(exist_ok=True)
    (affidavit / "manifest.json").write_text(
        json.dumps(
            _manifest_doc(
                oracle,
                claim_id=claim_id,
                runner=runner,
                support_files=support_files,
                claim_support_files=claim_support_files,
            ),
            indent=2,
        )
        + "\n"
    )
    (affidavit / "allowed_signers").write_bytes(allowlist)
    oracle_path = root / ORACLE_REL
    oracle_path.parent.mkdir(parents=True, exist_ok=True)
    oracle_path.write_bytes(oracle)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", ".")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _blob(root: Path, revision: str, relpath: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "cat-file", "-p", f"{revision}:{relpath}"],
        check=True,
        capture_output=True,
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> dict[str, Path | str]:
    root = _init(tmp_path)
    _write_tree(root, ORACLE_V1, ALLOWLIST_V1)
    first = _commit(root, "freeze oracles")
    _write_tree(root, ORACLE_V2, ALLOWLIST_V2)
    second = _commit(root, "update allowlist")
    return {"root": root, "first": first, "second": second}


def test_load_manifest_round_trip(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    loaded = load_manifest(root, str(repo["first"]))
    assert len(loaded.claims) == 1
    claim = loaded.claims[0]
    assert claim.id == "claim-widget"
    assert claim.text == "The widget returns one."
    assert claim.tests == (NODE_ID,)
    assert claim.oracle_hashes == {ORACLE_REL: _sha256(ORACLE_V1)}
    assert loaded.amendments == (
        {
            "id": "amend-1",
            "claim_id": "claim-widget",
            "signature": "not-a-real-signature",
        },
    )


def test_hash_oracle_files_matches_blob(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    first = str(repo["first"])
    blob = _blob(root, first, ORACLE_REL)
    digest = _sha256(blob)
    assert hash_oracle_files(root, first, [ORACLE_REL]) == {ORACLE_REL: digest}
    assert load_manifest(root, first).claims[0].oracle_hashes[ORACLE_REL] == digest


def test_allowlist_bytes_change_between_commits(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    first = load_allowlist(root, str(repo["first"]))
    second = load_allowlist(root, str(repo["second"]))
    assert first == ALLOWLIST_V1
    assert second == ALLOWLIST_V2
    assert first != second


def test_non_commit_revision_fails(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    tree = _git(root, "rev-parse", f"{repo['first']}^{{tree}}").stdout.strip()
    with pytest.raises(ManifestError):
        resolve_commit(root, tree)
    with pytest.raises(ManifestError):
        load_manifest(root, tree)
    with pytest.raises(ManifestError):
        load_allowlist(root, tree)
    with pytest.raises(ManifestError):
        hash_oracle_files(root, tree, [ORACLE_REL])


def test_dirty_worktree_is_ignored(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    second = str(repo["second"])
    expected_hashes = hash_oracle_files(root, second, [ORACLE_REL])
    expected_allowlist = load_allowlist(root, second)
    expected_manifest = load_manifest(root, second)

    (root / ORACLE_REL).write_bytes(b"dirty oracle\n")
    (root / ".affidavit" / "allowed_signers").write_bytes(b"dirty allowlist\n")
    (root / ".affidavit" / "manifest.json").write_text("{not json")

    assert hash_oracle_files(root, second, [ORACLE_REL]) == expected_hashes
    assert expected_hashes[ORACLE_REL] != _sha256(b"dirty oracle\n")
    assert load_allowlist(root, second) == expected_allowlist
    assert load_manifest(root, second) == expected_manifest


def test_merge_base_of_ancestor(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    assert merge_base(root, str(repo["first"])) == repo["first"]
    assert merge_base(root, "HEAD", main="main") == repo["second"]


def test_missing_oracle_path_raises(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    with pytest.raises(FileNotFoundError):
        hash_oracle_files(root, str(repo["first"]), ["no/such.py"])


def test_missing_manifest_raises(tmp_path: Path) -> None:
    root = _init(tmp_path)
    (root / "README").write_text("x\n")
    revision = _commit(root, "no manifest")
    with pytest.raises(ManifestError):
        load_manifest(root, revision)


def test_manifest_runner_absent_is_pytest_template(repo: dict[str, Path | str]) -> None:
    from affidavit.manifest import DEFAULT_RUNNER

    root = repo["root"]
    assert isinstance(root, Path)
    loaded = load_manifest(root, str(repo["first"]))
    shipped = (
        "python3",
        "-m",
        "pytest",
        "-o",
        "junit_family=xunit1",
        "{tests}",
        "--junitxml={report}",
    )
    assert DEFAULT_RUNNER == shipped
    assert loaded.runner == DEFAULT_RUNNER

    explicit = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]
    _write_tree(root, ORACLE_V1, ALLOWLIST_V1, runner=explicit)
    revision = _commit(root, "explicit runner")
    assert load_manifest(root, revision).runner == tuple(explicit)


@pytest.mark.parametrize(
    "runner",
    [
        pytest.param("python3", id="non-list"),
        pytest.param([], id="empty"),
        pytest.param(
            ["python3", 1, "{tests}", "--junitxml={report}"],
            id="non-string",
        ),
        pytest.param(
            ["python3", "prefix{tests}", "--junitxml={report}"],
            id="tests-glued",
        ),
        pytest.param(["python3", "--junitxml={report}"], id="omits-tests"),
        pytest.param(["python3", "{tests}"], id="omits-report"),
    ],
)
def test_manifest_runner_invalid_shape(tmp_path: Path, runner: object) -> None:
    root = _init(tmp_path)
    _write_tree(root, ORACLE_V1, ALLOWLIST_V1, runner=runner)
    revision = _commit(root, "invalid runner")
    with pytest.raises(ManifestError):
        load_manifest(root, revision)


def test_invalid_manifest_json_raises(tmp_path: Path) -> None:
    root = _init(tmp_path)
    affidavit = root / ".affidavit"
    affidavit.mkdir()
    (affidavit / "manifest.json").write_text("{")
    (affidavit / "allowed_signers").write_bytes(ALLOWLIST_V1)
    revision = _commit(root, "bad manifest")
    with pytest.raises(ManifestError):
        load_manifest(root, revision)


def test_runner_digest_is_sha256_of_argv_lines() -> None:
    argv = ("python3", "-m", "pytest", "{tests}", "--junitxml={report}")
    expected = _sha256(("\n".join(argv) + "\n").encode("utf-8"))
    assert runner_digest(argv) == expected
    assert runner_digest(argv) != runner_digest((*argv[:2], "-q", *argv[2:]))


def test_manifest_support_files_absent_is_empty(repo: dict[str, Path | str]) -> None:
    root = repo["root"]
    assert isinstance(root, Path)
    loaded = load_manifest(root, str(repo["first"]))
    assert loaded.support_files == ()
    assert loaded.claims[0].support_files == ()
    assert frozen_support_files(loaded, loaded.claims[0]) == ()


def test_manifest_and_claim_support_files_union(tmp_path: Path) -> None:
    root = _init(tmp_path)
    _write_tree(
        root,
        ORACLE_V1,
        ALLOWLIST_V1,
        support_files=["tests/conftest.py", "pytest.ini"],
        claim_support_files=["pytest.ini", "tests/helpers.py"],
    )
    revision = _commit(root, "support files")
    loaded = load_manifest(root, revision)
    assert loaded.support_files == ("tests/conftest.py", "pytest.ini")
    assert loaded.claims[0].support_files == ("pytest.ini", "tests/helpers.py")
    assert frozen_support_files(loaded, loaded.claims[0]) == (
        "tests/conftest.py",
        "pytest.ini",
        "tests/helpers.py",
    )
