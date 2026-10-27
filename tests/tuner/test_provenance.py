"""bin/aff verdict --provenance checks who wrote the oracle, and when."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

AFF = Path(__file__).resolve().parents[1] / "bin" / "aff"
CLAIM = "claim-widget"
NODE = "tests/test_widget.py::test_widget"
ORACLE_REL = "tests/test_widget.py"
ORACLE = b"def test_widget():\n    from app import value\n    assert value == 1\n"
APP_RED = b"value = 0\n"
APP_RED_TOUCHED = b"value = 0\n# touched\n"
APP_GREEN = b"value = 1\n"


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *args: str, config: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    prefix: list[str] = []
    for item in config:
        prefix.extend(["-c", item])
    result = subprocess.run(
        ["git", "-C", str(cwd), *prefix, *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args!r} failed\n{result.stderr}")
    return result


def _generate_key(directory: Path, name: str) -> tuple[Path, str]:
    key_path = directory / name
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key_path), "-q"],
        check=True,
        capture_output=True,
    )
    public = subprocess.check_output(
        ["ssh-keygen", "-y", "-f", str(key_path)],
        text=True,
    ).strip()
    return key_path, " ".join(public.split()[:2])


def _allowlist(signers: dict[str, str]) -> bytes:
    return "".join(
        f'{principal} namespaces="git,affidavit-amendment" {blob}\n'
        for principal, blob in signers.items()
    ).encode()


def _manifest() -> bytes:
    document = {
        "claims": [
            {
                "id": CLAIM,
                "text": "value is one",
                "tests": [NODE],
                "oracle_hashes": {ORACLE_REL: _sha256(ORACLE)},
            }
        ],
        "amendments": [],
    }
    return (json.dumps(document, indent=2) + "\n").encode()


def _write(root: Path, files: dict[str, bytes]) -> None:
    for relpath, data in files.items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _commit(root: Path, message: str, key: Path | None = None) -> str:
    _git(root, "add", "-A")
    if key is None:
        _git(root, "commit", "-qm", message)
    else:
        _git(
            root,
            "commit",
            "-q",
            "-S",
            "-m",
            message,
            config=("gpg.format=ssh", f"user.signingkey={key}"),
        )
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _init(root: Path) -> None:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "commit.gpgsign", "false")
    _git(root, "config", "gpg.format", "ssh")
    _git(root, "config", "gpg.ssh.allowedSignersFile", str(root / ".affidavit" / "allowed_signers"))


def _oracle_files(allow: bytes) -> dict[str, bytes]:
    return {
        ORACLE_REL: ORACLE,
        ".affidavit/manifest.json": _manifest(),
        ".affidavit/allowed_signers": allow,
    }


def _run(root: Path, at: str, base: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(AFF), "verdict", "--provenance", "--at", at, "--base", base, CLAIM],
        cwd=str(root),
        capture_output=True,
        text=True,
    )


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def _assert_fail(proc: subprocess.CompletedProcess[str], reason: str) -> None:
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": reason}]


def _keys(tmp_path: Path) -> tuple[Path, Path, bytes]:
    key_a, blob_a = _generate_key(tmp_path, "key_a")
    key_b, blob_b = _generate_key(tmp_path, "key_b")
    return key_a, key_b, _allowlist({"principal-a": blob_a, "principal-b": blob_b})


def test_r1_oracle_after_implementation_fails(tmp_path: Path) -> None:
    """R1: oracle commit that is not an ancestor of the implementation fails."""
    key_a, key_b, allow = _keys(tmp_path)
    root = tmp_path / "repo"
    _init(root)
    _write(root, {"app.py": APP_RED, "pytest.ini": b"[pytest]\n"})
    _write(root, {k: v for k, v in _oracle_files(allow).items() if k != ORACLE_REL})
    base = _commit(root, "non-oracle files")
    _write(root, {"app.py": APP_GREEN})
    _commit(root, "implementation", key_b)
    _write(root, {ORACLE_REL: ORACLE})
    oracle = _commit(root, "oracle", key_a)

    _assert_fail(_run(root, oracle, base), "provenance: oracle after implementation")

    _write(root, {"NOTES.md": b"later\n"})
    later = _commit(root, "later non-oracle change", key_b)
    _assert_fail(_run(root, later, base), "provenance: oracle after implementation")


def test_r2_oracle_commit_touches_non_oracle_paths_fails(tmp_path: Path) -> None:
    """R2: oracle commit that also edits app source fails."""
    key_a, key_b, allow = _keys(tmp_path)
    root = tmp_path / "repo"
    _init(root)
    _write(root, {"app.py": APP_RED, "pytest.ini": b"[pytest]\n"})
    _commit(root, "non-oracle files")
    _write(root, _oracle_files(allow))
    _write(root, {"app.py": APP_RED_TOUCHED})
    base = _commit(root, "oracle plus app edit", key_a)
    _write(root, {"app.py": APP_GREEN})
    head = _commit(root, "implementation", key_b)

    _assert_fail(_run(root, head, base), "provenance: oracle commit touches non-oracle paths")


def test_r3_shared_signer_fails(tmp_path: Path) -> None:
    """R3: oracle and implementation commits signed by one principal fail."""
    key_a, _key_b, allow = _keys(tmp_path)
    root = tmp_path / "repo"
    _init(root)
    _write(root, {"app.py": APP_RED, "pytest.ini": b"[pytest]\n"})
    _commit(root, "non-oracle files")
    _write(root, _oracle_files(allow))
    base = _commit(root, "oracle", key_a)
    _write(root, {"app.py": APP_GREEN})
    head = _commit(root, "implementation", key_a)

    _assert_fail(_run(root, head, base), "provenance: shared signer")


def test_r4_ordered_oracle_only_distinct_signers_passes(tmp_path: Path) -> None:
    """R4: ordered history, oracle-only commit, distinct signers passes."""
    key_a, key_b, allow = _keys(tmp_path)
    root = tmp_path / "repo"
    _init(root)
    _write(root, {"app.py": APP_RED, "pytest.ini": b"[pytest]\n"})
    _commit(root, "non-oracle files")
    _write(root, _oracle_files(allow))
    base = _commit(root, "oracle", key_a)
    _write(root, {"app.py": APP_GREEN})
    head = _commit(root, "implementation", key_b)

    proc = _run(root, head, base)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc) == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}
