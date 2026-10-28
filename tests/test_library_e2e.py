"""Oracle for a claim-gated close on one generated repository."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from orchestra.canon.project import open_store
from orchestra.conductor import close_batch

CLAIM_ID = "claim-widget"
CLAIM_TEXT = "widget works"
_CLOSE_MUST_NOT_START = {"aff", "canon"}


def _env() -> dict[str, str]:
    return os.environ.copy()


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, env=env)


def _git(repo: Path, *args: str) -> str:
    result = _run(["git", "-C", str(repo), *args], repo)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _sign_claim(key: Path) -> str:
    payload = f"tuner-claim v1\nclaim: {CLAIM_ID}\ntext: {CLAIM_TEXT}\n".encode()
    result = subprocess.run(
        ["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", "tuner-claim"],
        input=payload,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode() or "ssh-keygen sign failed")
    return result.stdout.decode()


def _allowlist(key: Path) -> bytes:
    public = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(key)],
        capture_output=True,
        text=True,
        check=False,
    )
    if public.returncode != 0:
        raise RuntimeError(public.stderr.strip() or "ssh-keygen -y failed")
    blob = " ".join(public.stdout.split()[:2])
    return f'reviewer namespaces="tuner-claim" {blob}\n'.encode()


def _init_store(repo: Path, env: dict[str, str]) -> None:
    initialized = _run(["canon", "init", "--schemas", "score,conductor,tuner"], repo, env)
    if initialized.returncode != 0:
        raise RuntimeError(initialized.stdout + initialized.stderr)
    _create(repo, env, "score:effort", "library-boundary", {"goal": "library boundary", "kind": "deliver"})
    _create(
        repo, env, "score:phase", "library-e2e",
        {"title": "Library e2e", "ordinal": 1, "effort": "library-boundary"},
        "## Problem\n\np\n\n## Approach\n\na\n\n## Exit criteria\n\ne\n",
    )


def _create(
    repo: Path, env: dict[str, str], record_type: str, subject: str, payload: dict, body: str | None = None
) -> dict:
    result = _run(
        [
            "canon",
            "create",
            "--type",
            record_type,
            "--subject",
            subject,
            "--payload",
            json.dumps(payload),
            *(["--body", body] if body else []),
        ],
        repo,
        env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    body = json.loads(result.stdout)
    record = body.get("record") if isinstance(body, dict) else None
    if not isinstance(record, dict):
        raise RuntimeError(result.stdout or "create did not return a record")
    return record


def _repository(directory: Path) -> tuple[Path, dict]:
    """Temporary git repository with a local store and one manifest claim."""
    env = _env()
    repo = directory / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "commit.gpgsign", "false")

    key_dir = directory / "keys"
    key_dir.mkdir()
    key = key_dir / "reviewer_key"
    generated = subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key), "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if generated.returncode != 0:
        raise RuntimeError(generated.stderr.strip() or "ssh-keygen failed")

    tuner = repo / ".tuner"
    tuner.mkdir()
    (tuner / "allowed_signers").write_bytes(_allowlist(key))
    (tuner / "manifest.json").write_text(
        json.dumps({"claims": [], "amendments": []}) + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")

    claim = {
        "id": CLAIM_ID,
        "text": CLAIM_TEXT,
        "tests": ["tests/test_widget.py::test_widget"],
        "oracle_hashes": {},
        "witness": "human",
        "signature": _sign_claim(key),
    }
    (tuner / "manifest.json").write_text(
        json.dumps({"claims": [claim], "amendments": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "claim")
    head = _git(repo, "rev-parse", "HEAD")
    _init_store(repo, env)

    acceptance = _create(
        repo,
        env,
        "score:acceptance",
        CLAIM_ID,
        {
            "method": "check",
            "phase": "library-e2e",
            "effort": "library-boundary",
            "verify_command": "python3 -m pytest -q",
            "claim": CLAIM_ID,
        },
    )
    check_run = _create(
        repo,
        env,
        "tuner:check-run",
        "close-check",
        {
            "criterion_id": acceptance["id"],
            "revision": head,
            "result": "pass",
            "effort": "library-boundary",
            "method": "check",
            "signed_by": "orchestra",
            "runner": "orchestra",
        },
    )
    from orchestra.tuner.binding import bind_observation

    bind_observation(
        repo,
        observation_id="obs-library-e2e",
        claim_id=CLAIM_ID,
        base_rev=base,
        head_rev=head,
    )

    request = {
        "subject": "library-fixture",
        "effort": "library-boundary",
        "work_item_id": "rec-library-fixture",
        "transition": "done",
        "acceptance_ids": [acceptance["id"]],
        "criteria": [
            {
                "criterion_id": acceptance["id"],
                "method": "check",
                "check_run_id": check_run["id"],
                "result": "pass",
            }
        ],
    }
    return repo, request


def _close_command(repo: Path, request: dict) -> tuple[int, str]:
    command = str(Path(__file__).resolve().parents[1] / "bin" / "orchestra")
    path = repo / "close-request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    out = repo / "close-batch.ndjson"
    result = _run(
        [sys.executable, command, "close-batch", "--input", str(path), "--out", str(out), "--cwd", str(repo)],
        repo,
        _env(),
    )
    return result.returncode, (result.stderr or result.stdout or "").strip()


def _assert_created_records(repo: Path, request: dict) -> None:
    """open_store reads the records canon create wrote."""
    project = open_store(repo)
    acceptance_id = request["acceptance_ids"][0]
    acceptance = project.get(acceptance_id, "score:acceptance")
    assert acceptance["id"] == acceptance_id
    assert acceptance["subject"] == CLAIM_ID
    assert acceptance["payload"]["method"] == "check"
    assert acceptance["payload"]["claim"] == CLAIM_ID
    check_run_id = request["criteria"][0]["check_run_id"]
    check_run = project.get(check_run_id, "tuner:check-run")
    assert check_run["id"] == check_run_id
    assert check_run["payload"]["criterion_id"] == acceptance_id
    assert check_run["payload"]["result"] == "pass"
    assert check_run["payload"]["runner"] == "orchestra"


def _close_in_process(repo: Path, request: dict, monkeypatch) -> int:
    """Python close on the fixture. A subprocess named aff or canon fails."""
    path = repo / "close-request.json"
    path.write_text(json.dumps(request), encoding="utf-8")
    out = repo / "close-python.ndjson"
    spawned: list[str] = []
    real_run = subprocess.run

    def spy(cmd, *args, **kwargs):
        argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
        parts = [str(part) for part in argv]
        name = Path(parts[0]).name if parts else ""
        if name in _CLOSE_MUST_NOT_START:
            spawned.append(name)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.chdir(repo)
    monkeypatch.setattr(subprocess, "run", spy)
    code = close_batch.main(
        ["--input", str(path), "--out", str(out), "--cwd", str(repo)]
    )
    assert spawned == [], f"in-process close started {spawned}"
    return code


def test_library_fixture_close(tmp_path, monkeypatch):
    """Created records are in the opened store, and command and Python close both accept the fixture."""
    repo, request = _repository(tmp_path)
    _assert_created_records(repo, request)
    code, detail = _close_command(repo, request)
    assert code == 0, detail or f"exit {code}"
    assert _close_in_process(repo, request, monkeypatch) == 0
