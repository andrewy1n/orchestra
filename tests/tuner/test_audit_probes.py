"""bin/aff audit runs declared probes and reports unclaimed diffs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AFF = REPO / "bin" / "aff"

PYTEST_INI = "[pytest]\npythonpath = .\n"
BASE_APP = "VALUE = 1\n"
HEAD_APP = "VALUE = 2\n"
PROBE_CLI = {
    "probes": [
        {
            "id": "value-print",
            "kind": "cli",
            "argv": ["python3", "-c", "from app import VALUE; print(VALUE)"],
            "claims": [],
        }
    ]
}


def _init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "probe@test"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "probe"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _write(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _commit(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )


def _audit(cwd: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(AFF),
            "audit",
            "--cwd",
            str(cwd),
            "--base",
            base,
            "--head",
            head,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout)


def test_r1_audit_runs_declared_probes_at_base_and_head(tmp_path: Path):
    """R1: aff audit runs declared probes at base and at head and compares results."""
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {
            "pytest.ini": PYTEST_INI,
            "app.py": BASE_APP,
            ".affidavit/probes.json": json.dumps(PROBE_CLI, indent=2) + "\n",
        },
    )
    base = _commit(root, "base")
    _write(root, {"app.py": HEAD_APP})
    head = _commit(root, "head")
    payload = _payload(_audit(root, base, head))
    assert "diffs" in payload
    assert isinstance(payload["diffs"], list)
    assert any(d.get("probe") == "value-print" for d in payload["diffs"])


def test_r2_audit_reports_unclaimed_probe_difference(tmp_path: Path):
    """R2: the audit reports a difference that no cited claim id accounts for."""
    root = tmp_path / "repo"
    _init(root)
    _write(
        root,
        {
            "pytest.ini": PYTEST_INI,
            "app.py": BASE_APP,
            ".affidavit/probes.json": json.dumps(PROBE_CLI, indent=2) + "\n",
        },
    )
    base = _commit(root, "base")
    _write(root, {"app.py": HEAD_APP})
    head = _commit(root, "head")
    payload = _payload(_audit(root, base, head))
    assert "diffs" in payload
    diffs = [d for d in payload["diffs"] if d.get("probe") == "value-print"]
    assert len(diffs) == 1
    assert diffs[0]["base"]["stdout"].strip() == "1"
    assert diffs[0]["head"]["stdout"].strip() == "2"


def test_r3_audit_suppresses_diff_covered_by_cited_claim(tmp_path: Path):
    """R3: the audit does not report a difference covered by a cited claim id."""
    root = tmp_path / "repo"
    _init(root)
    probes = {
        "probes": [
            {
                "id": "value-print",
                "kind": "cli",
                "argv": ["python3", "-c", "from app import VALUE; print(VALUE)"],
                "claims": ["claim-value"],
            }
        ]
    }
    manifest = {
        "claims": [
            {
                "id": "claim-value",
                "text": "VALUE changes",
                "tests": [],
                "oracle_hashes": {},
            }
        ],
        "amendments": [],
    }
    _write(
        root,
        {
            "pytest.ini": PYTEST_INI,
            "app.py": BASE_APP,
            ".affidavit/probes.json": json.dumps(probes, indent=2) + "\n",
            ".affidavit/manifest.json": json.dumps(manifest, indent=2) + "\n",
        },
    )
    base = _commit(root, "base")
    _write(root, {"app.py": HEAD_APP})
    head = _commit(root, "head")
    payload = _payload(_audit(root, base, head))
    assert "diffs" in payload
    assert all(d.get("probe") != "value-print" for d in payload["diffs"])
