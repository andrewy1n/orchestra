"""orchestra verify audit reverts diff blocks, labels them, and plants mutants in noticed blocks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
VERIFY = [sys.executable, str(REPO / "bin" / "orchestra"), "verify"]

BASE_APP = (
    "def add(a, b):\n"
    "    return a - b\n"
    "\n"
    "\n"
    "LIMIT = 1\n"
    "\n"
    "\n"
    "def mid():\n"
    "    return 0\n"
)
HEAD_APP = (
    "def add(a, b):\n"
    "    return a + b\n"
    "\n"
    "\n"
    "LIMIT = 2\n"
    "\n"
    "\n"
    "def mid():\n"
    "    return 0\n"
    "\n"
    "\n"
    "def extra():\n"
    "    return 5\n"
)
BASE_TEST = "def test_noop():\n    assert True\n"
HEAD_TEST = (
    "from app import add, extra\n"
    "\n"
    "\n"
    "def test_add():\n"
    "    assert add(1, 2) == 3\n"
    "\n"
    "\n"
    "def test_extra():\n"
    "    assert extra() == 5\n"
)
SYNTH_TESTS = ["tests/test_app.py::test_add", "tests/test_app.py::test_extra"]
PYTEST_INI = "[pytest]\npythonpath = .\n"


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise AssertionError(f"git {args!r} failed\n{result.stderr}")
    return result.stdout


def _init(root: Path) -> None:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").strip()


def _synthetic_repo(tmp_path: Path, extra_head: dict[str, str] | None = None):
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {
            "pytest.ini": PYTEST_INI,
            "app.py": BASE_APP,
            "tests/test_app.py": BASE_TEST,
            "README.md": "# app\n",
        },
    )
    base = _commit(root, "base")
    head_files = {
        "app.py": HEAD_APP,
        "tests/test_app.py": HEAD_TEST,
        "README.md": "# app\n\nNow with add and extra.\n",
    }
    head_files.update(extra_head or {})
    _write(root, head_files)
    head = _commit(root, "head")
    return root, base, head


def _no_store_env() -> dict[str, str]:
    """Audit records an observation in the cwd's store; aim it at a store that does not exist."""
    return dict(os.environ, CANON_STORE=tempfile.mkdtemp(prefix="no-store-"))


def _audit(
    cwd: Path,
    base: str,
    head: str,
    tests: list[str] | None = None,
    mutants: Path | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    argv = [
        *VERIFY,
        "audit",
        "--cwd",
        str(cwd),
        "--base",
        base,
        "--head",
        head,
    ]
    for node in tests or []:
        argv += ["--test", node]
    if mutants is not None:
        argv += ["--mutants", str(mutants)]
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=_no_store_env())


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.returncode == 0, proc.stderr or proc.stdout
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) >= 1
    return json.loads(proc.stdout)


def _is_test_path(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (
        "tests" in parts[:-1]
        or "test" in parts[:-1]
        or (name.startswith("test_") and name.endswith(".py"))
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


def test_r1_audit_labels_each_source_block(tmp_path: Path):
    """R1: audit splits the diff into blocks and labels each as noticed, not_noticed, or inconclusive."""
    root, base, head = _synthetic_repo(tmp_path)
    proc = _audit(root, base, head, tests=SYNTH_TESTS)
    payload = _payload(proc)
    assert payload["advisory"] is True
    assert payload["base"] == base
    assert payload["head"] == head
    assert isinstance(payload["mutants"], list)
    assert payload["survivors"] == []

    blocks = payload["blocks"]
    for block in blocks:
        assert {"file", "start", "end", "label", "text"} <= set(block)
        assert isinstance(block["start"], int) and isinstance(block["end"], int)
        assert block["end"] >= block["start"]
        assert block["label"] in {"noticed", "not_noticed", "inconclusive"}
    assert {b["file"] for b in blocks} == {"app.py"}

    by_text = {}
    for block in blocks:
        for key in ("return a + b", "LIMIT = 2", "def extra"):
            if key in block["text"]:
                by_text[key] = block
    assert set(by_text) == {"return a + b", "LIMIT = 2", "def extra"}
    assert by_text["return a + b"]["label"] == "noticed"
    assert by_text["return a + b"]["start"] == 2
    assert by_text["LIMIT = 2"]["label"] == "not_noticed"
    assert by_text["LIMIT = 2"]["start"] == 5
    assert by_text["def extra"]["label"] == "inconclusive"
    assert by_text["def extra"]["start"] >= 9
    assert len(blocks) == 3


def test_r1_audit_reads_claim_tests_from_manifest(tmp_path: Path):
    """R1: audit reruns tests of every claim in the head manifest through its runner."""
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {"pytest.ini": PYTEST_INI, "app.py": BASE_APP, "tests/test_app.py": BASE_TEST},
    )
    base = _commit(root, "base")
    manifest = {
        "claims": [
            {
                "id": "claim-add",
                "text": "add sums",
                "tests": ["tests/test_app.py::test_add"],
                "oracle_hashes": {},
            }
        ],
        "amendments": [],
    }
    _write(
        root,
        {
            "app.py": HEAD_APP,
            "tests/test_app.py": HEAD_TEST,
            ".tuner/manifest.json": json.dumps(manifest, indent=2) + "\n",
        },
    )
    head = _commit(root, "head")
    payload = _payload(_audit(root, base, head))
    labels = {
        key: block["label"]
        for block in payload["blocks"]
        for key in ("return a + b", "LIMIT = 2")
        if key in block["text"]
    }
    assert labels == {"return a + b": "noticed", "LIMIT = 2": "not_noticed"}
    assert all(b["file"] == "app.py" for b in payload["blocks"])


def test_r2_audit_never_reports_test_file_blocks(tmp_path: Path):
    """R2: audit never reports a test-file or prose block as a finding target."""
    extra = {
        "tests/test_x.py": "def test_x():\n    assert 1 == 1\n",
        "pkg/test_y.py": "def test_y():\n    assert 2 == 2\n",
        "pkg/z_test.py": "def test_z():\n    assert 3 == 3\n",
        "test/helper.py": "VALUE = 1\n",
        "conftest.py": "VALUE = 2\n",
        "docs/notes.py": "NOTE = 'prose'\n",
        "NOTES.txt": "plain notes\n",
        ".canon/state.json": '{"x": 1}\n',
    }
    root, base, head = _synthetic_repo(tmp_path, extra_head=extra)
    proc = _audit(root, base, head, tests=SYNTH_TESTS)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    files = [block["file"] for block in payload["blocks"]]
    assert files, "source block must still be reported"
    assert "app.py" in files
    for path in files:
        assert not _is_test_path(path), path
        assert not path.startswith(("docs/", ".canon/"))
        assert not path.endswith((".md", ".rst", ".txt"))
    assert set(files) == {"app.py"}
