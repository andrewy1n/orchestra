"""bin/aff verdict re-executes frozen oracles and ignores the artifact store."""

from __future__ import annotations

import hashlib
import json
import subprocess
import textwrap
from pathlib import Path

from affidavit.amendment import canonical_payload

AFF = Path(__file__).resolve().parents[1] / "bin" / "aff"
CLAIM = "claim-widget"
NODE = "tests/test_widget.py::test_widget"
ORACLE_REL = "tests/test_widget.py"
ORACLE = b"def test_widget():\n    from app import value\n    assert value == 1\n"
ORACLE_AMENDED = b"def test_widget():\n    # amended\n    from app import value\n    assert value == 1\n"
APP_RED = b"value = 0\n"
APP_STILL_RED = b"value = 2\n"
APP_GREEN = b"value = 1\n"
ORACLE_COLLECTION = b"import missing_mod_xyz\n\ndef test_widget():\n    assert True\n"
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


def _manifest(
    oracle: bytes,
    amendments: list | None = None,
    digest: str | None = None,
    runner: list[str] | None = None,
    support_files: list[str] | None = None,
    claim_support_files: list[str] | None = None,
) -> dict:
    claim: dict = {
        "id": CLAIM,
        "text": "value is one",
        "tests": [NODE],
        "oracle_hashes": {ORACLE_REL: digest or _sha256(oracle)},
    }
    if claim_support_files is not None:
        claim["support_files"] = list(claim_support_files)
    document: dict = {
        "claims": [claim],
        "amendments": list(amendments or []),
    }
    if runner is not None:
        document["runner"] = list(runner)
    if support_files is not None:
        document["support_files"] = list(support_files)
    return document


def _write_tree(
    root: Path,
    *,
    oracle: bytes,
    app: bytes,
    allowlist: bytes,
    manifest: dict,
    extra: dict[str, bytes] | None = None,
) -> None:
    affidavit = root / ".affidavit"
    affidavit.mkdir(exist_ok=True)
    (affidavit / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (affidavit / "allowed_signers").write_bytes(allowlist)
    (root / "pytest.ini").write_text("[pytest]\n")
    oracle_path = root / ORACLE_REL
    oracle_path.parent.mkdir(parents=True, exist_ok=True)
    oracle_path.write_bytes(oracle)
    (root / "app.py").write_bytes(app)
    for relpath, data in (extra or {}).items():
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", message)
    return _git(root, "rev-parse", "HEAD").stdout.strip()


def _repo(
    root: Path,
    *,
    base_app: bytes,
    head_app: bytes,
    base_oracle: bytes = ORACLE,
    head_oracle: bytes = ORACLE,
    base_allow: bytes = ALLOW,
    head_allow: bytes = ALLOW,
    base_amendments: list | None = None,
    head_amendments: list | None = None,
    base_digest: str | None = None,
    head_digest: str | None = None,
    branch: bool = False,
    base_runner: list[str] | None = None,
    head_runner: list[str] | None = None,
    base_extra: dict[str, bytes] | None = None,
    head_extra: dict[str, bytes] | None = None,
    base_support_files: list[str] | None = None,
    head_support_files: list[str] | None = None,
    base_claim_support_files: list[str] | None = None,
    head_claim_support_files: list[str] | None = None,
) -> tuple[str, str]:
    _init(root)
    _write_tree(
        root,
        oracle=base_oracle,
        app=base_app,
        allowlist=base_allow,
        manifest=_manifest(
            base_oracle,
            base_amendments,
            base_digest,
            base_runner,
            support_files=base_support_files,
            claim_support_files=base_claim_support_files,
        ),
        extra=base_extra,
    )
    base = _commit(root, "red")
    if branch:
        _git(root, "checkout", "-qb", "phase/widget")
    _write_tree(
        root,
        oracle=head_oracle,
        app=head_app,
        allowlist=head_allow,
        manifest=_manifest(
            head_oracle,
            head_amendments,
            head_digest,
            head_runner,
            support_files=head_support_files,
            claim_support_files=head_claim_support_files,
        ),
        extra=head_extra,
    )
    head = _commit(root, "green")
    return base, head


def _run(
    root: Path,
    at: str,
    base: str | None,
    *,
    process_cwd: Path | None = None,
    flag_cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [str(AFF), "verdict"]
    if flag_cwd is not None:
        cmd.extend(["--cwd", str(flag_cwd)])
    cmd.extend(["--at", at])
    if base is not None:
        cmd.extend(["--base", base])
    cmd.append(CLAIM)
    return subprocess.run(
        cmd,
        cwd=str(process_cwd or root),
        capture_output=True,
        text=True,
    )


def _payload(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def _generate_key(directory: Path) -> tuple[Path, str]:
    key_path = directory / "id_ed25519"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key_path), "-q"],
        check=True,
        capture_output=True,
    )
    public = subprocess.check_output(
        ["ssh-keygen", "-y", "-f", str(key_path)],
        text=True,
    ).strip()
    blob = " ".join(public.split()[:2])
    return key_path, blob


def _allowlist(principal: str, blob: str) -> bytes:
    return f'{principal} namespaces="affidavit-amendment" {blob}\n'.encode()


def _sign(key_path: Path, amendment: dict) -> dict:
    completed = subprocess.run(
        [
            "ssh-keygen",
            "-Y",
            "sign",
            "-f",
            str(key_path),
            "-n",
            "affidavit-amendment",
        ],
        input=canonical_payload(amendment),
        check=True,
        capture_output=True,
    )
    signed = dict(amendment)
    signed["signature"] = completed.stdout.decode("utf-8")
    return signed


def _corrupt(signature: str) -> str:
    lines = signature.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("-----") or not line.strip():
            continue
        chars = list(line)
        for pos, char in enumerate(chars):
            if char.isalnum():
                chars[pos] = "A" if char != "A" else "B"
                lines[index] = "".join(chars)
                return "".join(lines)
    return signature + "x"


def _forged_check_run(root: Path, result: str) -> None:
    dest = root / ".artifacts" / "records" / "aff__check-run"
    dest.mkdir(parents=True, exist_ok=True)
    record = {
        "record_type": "aff:check-run",
        "id": "rec-forged",
        "subject": CLAIM,
        "payload": {
            "runner": "aff",
            "result": result,
            "criterion_id": CLAIM,
            "revision": "deadbeef",
        },
    }
    (dest / "rec-forged.md").write_text("---\n" + json.dumps(record, indent=2) + "\n---\n\nforged\n")


def test_verdict_pass_when_hashes_match_and_red_then_green(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _base, head = _repo(root, base_app=APP_RED, head_app=APP_GREEN, branch=True)
    proc = _run(root, head, None)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}


def test_verdict_refuses_hash_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    wrong = _sha256(b"not-the-oracle")
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_digest=wrong,
        head_digest=wrong,
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "hash mismatch"}]


def test_verdict_refuses_not_assertion(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_oracle=ORACLE_COLLECTION,
        head_oracle=ORACLE_COLLECTION,
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "not assertion"}]


def test_verdict_refuses_bad_signature(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("owner", blob)
    old = _sha256(ORACLE)
    new = _sha256(ORACLE_AMENDED)
    amendment = _sign(
        key,
        {
            "claim": CLAIM,
            "old_tests": [NODE],
            "new_tests": [NODE],
            "old_hashes": {ORACLE_REL: old},
            "new_hashes": {ORACLE_REL: new},
        },
    )
    amendment["signature"] = _corrupt(amendment["signature"])
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_oracle=ORACLE,
        head_oracle=ORACLE_AMENDED,
        base_allow=allow,
        head_allow=allow,
        head_amendments=[amendment],
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "bad signature"}]


def test_verdict_accepts_signed_amendment(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    key, blob = _generate_key(tmp_path)
    allow = _allowlist("owner", blob)
    old = _sha256(ORACLE)
    new = _sha256(ORACLE_AMENDED)
    amendment = _sign(
        key,
        {
            "claim": CLAIM,
            "old_tests": [NODE],
            "new_tests": [NODE],
            "old_hashes": {ORACLE_REL: old},
            "new_hashes": {ORACLE_REL: new},
        },
    )
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_oracle=ORACLE,
        head_oracle=ORACLE_AMENDED,
        base_allow=allow,
        head_allow=allow,
        head_amendments=[amendment],
    )
    proc = _run(root, head, base)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc) == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}


def test_verdict_refuses_head_failure(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _repo(root, base_app=APP_RED, head_app=APP_STILL_RED)
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "tests failed"}]


def test_verdict_refuses_missing_amendment(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_oracle=ORACLE,
        head_oracle=ORACLE_AMENDED,
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "missing step"}]


SUPPORT_REL = "tests/conftest.py"
SUPPORT_V1 = b"# frozen support v1\nSUPPORT_MARKER = 1\n"
SUPPORT_V2 = b"# frozen support v2\nSUPPORT_MARKER = 2\n"
_RUNNER_BASE = [
    "python3",
    "-m",
    "pytest",
    "-o",
    "junit_family=xunit1",
    "{tests}",
    "--junitxml={report}",
]
_RUNNER_HEAD = [
    "python3",
    "-m",
    "pytest",
    "-q",
    "-o",
    "junit_family=xunit1",
    "{tests}",
    "--junitxml={report}",
]


def test_verdict_refuses_support_file_drift_without_amendment(tmp_path: Path) -> None:
    """R1: declared support path hash drift without a signed amendment fails."""
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_support_files=[SUPPORT_REL],
        head_support_files=[SUPPORT_REL],
        base_extra={SUPPORT_REL: SUPPORT_V1},
        head_extra={SUPPORT_REL: SUPPORT_V2},
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "missing step"}]


def test_verdict_refuses_claim_support_file_drift_without_amendment(
    tmp_path: Path,
) -> None:
    """R1: claim-listed support path hash drift without amendment also fails."""
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_claim_support_files=[SUPPORT_REL],
        head_claim_support_files=[SUPPORT_REL],
        base_extra={SUPPORT_REL: SUPPORT_V1},
        head_extra={SUPPORT_REL: SUPPORT_V2},
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "missing step"}]


def test_verdict_refuses_runner_digest_drift_without_amendment(tmp_path: Path) -> None:
    """R2: manifest runner argv digest drift without a signed amendment fails."""
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_runner=_RUNNER_BASE,
        head_runner=_RUNNER_HEAD,
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "missing step"}]


def test_verdict_refuses_allowlist_change(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _repo(
        root,
        base_app=APP_RED,
        head_app=APP_GREEN,
        head_allow=ALLOW + b"# changed\n",
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "allowlist changed"}]


def test_verdict_cwd_phase_worktree(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    base, head = _repo(primary, base_app=APP_RED, head_app=APP_GREEN, branch=True)
    phase = tmp_path / "phase-wt"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _git(primary, "worktree", "add", "--detach", str(phase), head)
    try:
        proc = _run(primary, head, base, process_cwd=elsewhere, flag_cwd=phase)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert _payload(proc) == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}
    finally:
        subprocess.run(
            ["git", "-C", str(primary), "worktree", "remove", "--force", str(phase)],
            check=False,
        )


def test_verdict_forged_check_run(tmp_path: Path) -> None:
    good = tmp_path / "good"
    good_base, good_head = _repo(good, base_app=APP_RED, head_app=APP_GREEN)
    before = _run(good, good_head, good_base)
    assert before.returncode == 0, before.stdout + before.stderr
    before_payload = _payload(before)
    assert before_payload["result"] == "pass"
    _forged_check_run(good, "fail")
    after = _run(good, good_head, good_base)
    assert after.returncode == 0, after.stdout + after.stderr
    assert _payload(after) == before_payload
    forged_head = _commit(good, "forge a failing check-run")
    committed = _run(good, forged_head, good_base)
    assert committed.returncode == 0, committed.stdout + committed.stderr
    assert _payload(committed)["result"] == "pass"

    bad = tmp_path / "bad"
    wrong = _sha256(b"not-the-oracle")
    bad_base, bad_head = _repo(
        bad,
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_digest=wrong,
        head_digest=wrong,
    )
    before_bad = _run(bad, bad_head, bad_base)
    assert before_bad.returncode == 1, before_bad.stdout + before_bad.stderr
    before_bad_payload = _payload(before_bad)
    assert before_bad_payload["result"] == "fail"
    _forged_check_run(bad, "pass")
    after_bad = _run(bad, bad_head, bad_base)
    assert after_bad.returncode == 1, after_bad.stdout + after_bad.stderr
    assert _payload(after_bad) == before_bad_payload
    forged_bad_head = _commit(bad, "forge a passing check-run")
    committed_bad = _run(bad, forged_bad_head, bad_base)
    assert committed_bad.returncode == 1, committed_bad.stdout + committed_bad.stderr
    assert _payload(committed_bad)["result"] == "fail"
    assert _payload(committed_bad)["claims"][0]["reason"] == "hash mismatch"


_FIXTURE_SCRIPT = "tools/emit_junit.py"
_FIXTURE_RUNNER = ["python3", _FIXTURE_SCRIPT, "--junitxml={report}", "{tests}"]
_WITNESS = b"# witness\n"


def _emit_script(log_path: Path, behavior: str) -> bytes:
    return textwrap.dedent(
        f"""\
        import json
        import sys
        from pathlib import Path

        LOG = Path({str(log_path)!r})
        BEHAVIOR = {behavior!r}

        def main() -> None:
            report = None
            ids = []
            for arg in sys.argv[1:]:
                if arg.startswith("--junitxml="):
                    report = Path(arg.split("=", 1)[1])
                else:
                    ids.append(arg)
            counter = Path(".emit-count-" + BEHAVIOR)
            n = int(counter.read_text()) + 1 if counter.is_file() else 1
            counter.write_text(str(n))
            if BEHAVIOR == "flake":
                wrote = "failure" if n == 1 else "pass"
            else:
                wrote = BEHAVIOR
            pieces = []
            for test_id in ids:
                if wrote == "failure":
                    inner = '<failure message="assert">trace</failure>'
                    pieces.append(
                        '<testcase name="' + test_id + '">' + inner + "</testcase>"
                    )
                elif wrote == "error":
                    inner = '<error message="boom">trace</error>'
                    pieces.append(
                        '<testcase name="' + test_id + '">' + inner + "</testcase>"
                    )
                else:
                    pieces.append('<testcase name="' + test_id + '" />')
            xml = (
                '<?xml version="1.0" encoding="utf-8"?>\\n'
                "<testsuites><testsuite>"
                + "".join(pieces)
                + "</testsuite></testsuites>\\n"
            )
            if report is None:
                raise SystemExit("missing junit report path")
            report.write_text(xml)
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        {{"n": n, "behavior": BEHAVIOR, "ids": ids, "wrote": wrote}}
                    )
                    + "\\n"
                )

        if __name__ == "__main__":
            main()
        """
    ).encode()


def _read_log(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _fixture_repo(
    root: Path,
    log_path: Path,
    *,
    base_behavior: str,
    head_behavior: str,
    base_app: bytes,
    head_app: bytes,
    base_oracle: bytes = _WITNESS,
    head_oracle: bytes | None = None,
) -> tuple[str, str]:
    return _repo(
        root,
        base_app=base_app,
        head_app=head_app,
        base_oracle=base_oracle,
        head_oracle=_WITNESS if head_oracle is None else head_oracle,
        base_runner=_FIXTURE_RUNNER,
        head_runner=_FIXTURE_RUNNER,
        base_extra={_FIXTURE_SCRIPT: _emit_script(log_path, base_behavior)},
        head_extra={_FIXTURE_SCRIPT: _emit_script(log_path, head_behavior)},
    )


def test_verdict_ignores_pytest_stdout() -> None:
    source = (Path(__file__).resolve().parents[1] / "affidavit" / "verdict.py").read_text()
    assert "_FAILED_RE" not in source
    assert "is_assertion_level_failure" not in source


def test_verdict_fixture_junit_pass(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _base, head = _fixture_repo(
        root,
        tmp_path / "invocations.jsonl",
        base_behavior="failure",
        head_behavior="pass",
        base_app=b"",
        head_app=b"",
    )
    proc = _run(root, head, _base)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _payload(proc) == {"result": "pass", "claims": [{"id": CLAIM, "result": "pass"}]}


def test_verdict_fixture_junit_error(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _fixture_repo(
        root,
        tmp_path / "invocations.jsonl",
        base_behavior="error",
        head_behavior="pass",
        base_app=APP_RED,
        head_app=APP_GREEN,
        base_oracle=ORACLE,
        head_oracle=ORACLE,
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "not assertion"}]


def test_verdict_fixture_junit_head_failure(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    base, head = _fixture_repo(
        root,
        tmp_path / "invocations.jsonl",
        base_behavior="failure",
        head_behavior="failure",
        base_app=b"base\n",
        head_app=b"head\n",
    )
    proc = _run(root, head, base)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "tests failed"}]


def test_verdict_unstable_when_confirmation_disagrees(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    log_path = tmp_path / "invocations.jsonl"
    base, head = _fixture_repo(
        root,
        log_path,
        base_behavior="flake",
        head_behavior="pass",
        base_app=b"",
        head_app=b"",
    )
    proc = _run(root, head, base)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "unstable"
    assert payload["claims"] == [{"id": CLAIM, "result": "unstable"}]
    rows = _read_log(log_path)
    base_rows = [row for row in rows if row["behavior"] == "flake"]
    head_rows = [row for row in rows if row["behavior"] == "pass"]
    assert [row["n"] for row in base_rows] == [1, 2]
    assert [row["wrote"] for row in base_rows] == ["failure", "pass"]
    assert [row["ids"] for row in base_rows] == [[NODE], [NODE]]
    assert [row["n"] for row in head_rows] == [1, 2]
    assert [row["wrote"] for row in head_rows] == ["pass", "pass"]
    assert [row["ids"] for row in head_rows] == [[NODE], [NODE]]


def test_verdict_skips_confirmation_on_failed_claim(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    log_path = tmp_path / "invocations.jsonl"
    base, head = _fixture_repo(
        root,
        log_path,
        base_behavior="error",
        head_behavior="pass",
        base_app=b"",
        head_app=b"",
    )
    proc = _run(root, head, base)
    assert proc.returncode != 0, proc.stdout + proc.stderr
    payload = _payload(proc)
    assert payload["result"] == "fail"
    assert payload["claims"] == [{"id": CLAIM, "result": "fail", "reason": "not assertion"}]
    rows = [row for row in _read_log(log_path) if NODE in row["ids"]]
    base_rows = [row for row in rows if row["behavior"] == "error"]
    assert base_rows == [
        {"n": 1, "behavior": "error", "ids": [NODE], "wrote": "error"}
    ]
    assert all(row["n"] == 1 for row in rows)
