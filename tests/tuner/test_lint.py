"""Witness lint: no-assert sources and new skips between revisions (R3, R4)."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from pathlib import Path

import pytest

CLAIM = "claim-widget"
NODE = "tests/test_widget.py::test_widget"
ORACLE_REL = "tests/test_widget.py"
ORACLE_ASSERT = b"def test_widget():\n    from app import value\n    assert value == 1\n"
ORACLE_NO_ASSERT = b"def test_widget():\n    from app import value\n    value\n"
ORACLE_BASE = b"def test_widget():\n    from app import value\n    assert value == 1\n"
ORACLE_HEAD_SKIP = (
    b"import pytest\n"
    b"\n"
    b"@pytest.mark.skip(reason='deferred')\n"
    b"def test_widget():\n"
    b"    from app import value\n"
    b"    assert value == 1\n"
)
APP_GREEN = b"value = 1\n"
ALLOW = (
    b'owner namespaces="affidavit-amendment" '
    b"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKeyOneaaaaaaaaaaaaaaaaaaa\n"
)


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args!r} failed\n{result.stderr}")
    return result


def _init(root: Path) -> None:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "core.autocrlf", "false")
    _git(root, "config", "commit.gpgsign", "false")


def _manifest(oracle: bytes) -> dict:
    return {
        "claims": [
            {
                "id": CLAIM,
                "text": "value is one",
                "tests": [NODE],
                "oracle_hashes": {ORACLE_REL: _sha256(oracle)},
            }
        ],
        "amendments": [],
    }


def _write_tree(root: Path, *, oracle: bytes, app: bytes) -> None:
    affidavit = root / ".affidavit"
    affidavit.mkdir(exist_ok=True)
    (affidavit / "manifest.json").write_text(
        json.dumps(_manifest(oracle), indent=2) + "\n"
    )
    (affidavit / "allowed_signers").write_bytes(ALLOW)
    (root / "pytest.ini").write_text("[pytest]\n")
    oracle_path = root / ORACLE_REL
    oracle_path.parent.mkdir(parents=True, exist_ok=True)
    oracle_path.write_bytes(oracle)
    (root / "app.py").write_bytes(app)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _lint():
    try:
        return importlib.import_module("affidavit.lint")
    except ModuleNotFoundError:
        return None


def test_lint_reports_no_assert_witness(tmp_path: Path) -> None:
    """R3: a witness with no assertion (or equivalent outcome signal) is reported."""
    lint = _lint()
    assert lint is not None, "affidavit.lint must exist"
    witness = tmp_path / "test_no_assert.py"
    witness.write_bytes(ORACLE_NO_ASSERT)
    findings = lint.find_no_assert([witness])
    assert findings, "expected at least one no-assert finding"
    joined = " ".join(str(item) for item in findings)
    assert "test_widget" in joined or str(witness) in joined or "test_no_assert" in joined


def test_lint_ignores_asserting_witness(tmp_path: Path) -> None:
    lint = _lint()
    assert lint is not None, "affidavit.lint must exist"
    witness = tmp_path / "test_with_assert.py"
    witness.write_bytes(ORACLE_ASSERT)
    findings = lint.find_no_assert([witness])
    assert findings == []


def test_lint_reports_new_skip_between_base_and_head(tmp_path: Path) -> None:
    """R4: a witness skipped at head but not at base is reported."""
    lint = _lint()
    assert lint is not None, "affidavit.lint must exist"
    root = tmp_path / "repo"
    _init(root)
    _write_tree(root, oracle=ORACLE_BASE, app=APP_GREEN)
    base = _commit(root, "base runs")
    _write_tree(root, oracle=ORACLE_HEAD_SKIP, app=APP_GREEN)
    head = _commit(root, "head skips")
    findings = lint.find_new_skips(root, base, head, claim_id=CLAIM)
    assert NODE in findings
