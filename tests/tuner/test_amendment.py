"""Amendment signature chain (R3)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from affidavit.amendment import authorize, canonical_payload


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
    blob = " ".join(public.split()[:2])
    return key_path, blob


def _allowlist(principal: str, blob: str) -> bytes:
    return f'{principal} namespaces="affidavit-amendment" {blob}\n'.encode()


def _claim(claim_id: str, tests: list[str], hashes: dict[str, str]) -> dict:
    return {
        "id": claim_id,
        "text": "observable",
        "tests": list(tests),
        "oracle_hashes": dict(hashes),
    }


def _amendment(
    claim_id: str,
    old_tests: list[str],
    new_tests: list[str],
    old_hashes: dict[str, str],
    new_hashes: dict[str, str],
) -> dict:
    return {
        "claim": claim_id,
        "old_tests": list(old_tests),
        "new_tests": list(new_tests),
        "old_hashes": dict(old_hashes),
        "new_hashes": dict(new_hashes),
    }


def _sign(key_path: Path, amendment: dict) -> dict:
    payload = canonical_payload(amendment)
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
        input=payload,
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


def test_canonical_payload_orders_hashes_and_omits_signature():
    amendment = _amendment(
        "R1",
        ["tests/test_mod.py::test_a", "tests/test_mod.py::test_b"],
        ["tests/test_mod.py::test_b"],
        {"b.py": "sha256:bb", "a.py": "sha256:aa"},
        {"a.py": "sha256:cc"},
    )
    amendment["signature"] = "not-part-of-the-payload"
    assert canonical_payload(amendment) == (
        "affidavit-amendment v1\n"
        "claim: R1\n"
        "old_tests: tests/test_mod.py::test_a,tests/test_mod.py::test_b\n"
        "new_tests: tests/test_mod.py::test_b\n"
        "old_hashes:\n"
        "a.py sha256:aa\n"
        "b.py sha256:bb\n"
        "new_hashes:\n"
        "a.py sha256:cc\n"
    ).encode()


def test_one_step_chain(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    old_hashes = {"tests/test_mod.py": "sha256:11"}
    new_hashes = {"tests/test_mod.py": "sha256:22"}
    tests = ["tests/test_mod.py::test_name"]
    base = _claim("R1", tests, old_hashes)
    head = _claim("R1", tests, new_hashes)
    step = _sign(key, _amendment("R1", tests, tests, old_hashes, new_hashes))
    assert authorize(base, head, [step], allow, allow) == (True, "")


def test_two_step_chain(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests_a = ["tests/test_mod.py::test_name"]
    tests_b = ["tests/test_mod.py::test_name", "tests/test_mod.py::test_extra"]
    tests_c = ["tests/test_mod.py::test_extra"]
    hashes_a = {"tests/test_mod.py": "sha256:01"}
    hashes_b = {"tests/test_mod.py": "sha256:02"}
    hashes_c = {
        "tests/test_mod.py": "sha256:03",
        "tests/test_extra.py": "sha256:04",
    }
    base = _claim("R1", tests_a, hashes_a)
    head = _claim("R1", tests_c, hashes_c)
    first = _sign(key, _amendment("R1", tests_a, tests_b, hashes_a, hashes_b))
    second = _sign(key, _amendment("R1", tests_b, tests_c, hashes_b, hashes_c))
    other = _amendment("R2", tests_a, tests_c, hashes_a, hashes_c)
    other["signature"] = "not-a-signature"
    assert authorize(base, head, [first, other, second], allow, allow) == (True, "")


def test_broken_middle(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes_a = {"tests/test_mod.py": "sha256:01"}
    hashes_b = {"tests/test_mod.py": "sha256:02"}
    hashes_c = {"tests/test_mod.py": "sha256:03"}
    base = _claim("R1", tests, hashes_a)
    head = _claim("R1", tests, hashes_c)
    first = _sign(key, _amendment("R1", tests, tests, hashes_a, hashes_b))
    skipped = _sign(key, _amendment("R1", tests, tests, hashes_a, hashes_c))
    assert authorize(base, head, [first, skipped], allow, allow) == (False, "missing step")


def test_bad_signature(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    old_hashes = {"tests/test_mod.py": "sha256:11"}
    new_hashes = {"tests/test_mod.py": "sha256:22"}
    base = _claim("R1", tests, old_hashes)
    head = _claim("R1", tests, new_hashes)
    step = _sign(key, _amendment("R1", tests, tests, old_hashes, new_hashes))
    step["signature"] = _corrupt(step["signature"])
    assert authorize(base, head, [step], allow, allow) == (False, "bad signature")


def test_key_not_on_allowlist(tmp_path):
    signer, _signer_blob = _generate_key(tmp_path, "signer")
    _other, other_blob = _generate_key(tmp_path, "other")
    allow = _allowlist("owner", other_blob)
    tests = ["tests/test_mod.py::test_name"]
    old_hashes = {"tests/test_mod.py": "sha256:11"}
    new_hashes = {"tests/test_mod.py": "sha256:22"}
    base = _claim("R1", tests, old_hashes)
    head = _claim("R1", tests, new_hashes)
    step = _sign(signer, _amendment("R1", tests, tests, old_hashes, new_hashes))
    assert authorize(base, head, [step], allow, allow) == (False, "bad signature")


def test_differing_allowlist_bytes(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    old_hashes = {"tests/test_mod.py": "sha256:11"}
    new_hashes = {"tests/test_mod.py": "sha256:22"}
    base = _claim("R1", tests, old_hashes)
    head = _claim("R1", tests, new_hashes)
    step = _sign(key, _amendment("R1", tests, tests, old_hashes, new_hashes))
    changed = allow + b"# changed\n"
    assert authorize(base, head, [step], allow, changed) == (False, "allowlist changed")


def test_unchanged_claim_without_amendment(tmp_path):
    _key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes = {"tests/test_mod.py": "sha256:11"}
    base = _claim("R1", tests, hashes)
    head = _claim("R1", tests, hashes)
    assert authorize(base, head, [], allow, allow) == (True, "")


def test_support_hash_drift_without_amendment_is_missing_step(tmp_path):
    _key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes = {"tests/test_mod.py": "sha256:11"}
    base = _claim("R1", tests, hashes)
    head = _claim("R1", tests, hashes)
    base["support_hashes"] = {"tests/conftest.py": "sha256:aa"}
    head["support_hashes"] = {"tests/conftest.py": "sha256:bb"}
    assert authorize(base, head, [], allow, allow) == (False, "missing step")


def test_runner_digest_drift_without_amendment_is_missing_step(tmp_path):
    _key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes = {"tests/test_mod.py": "sha256:11"}
    base = _claim("R1", tests, hashes)
    head = _claim("R1", tests, hashes)
    base["runner_digest"] = "sha256:oldrunner"
    head["runner_digest"] = "sha256:newrunner"
    assert authorize(base, head, [], allow, allow) == (False, "missing step")


def test_signed_support_hash_amendment_authorizes(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes = {"tests/test_mod.py": "sha256:11"}
    old_support = {"tests/conftest.py": "sha256:aa"}
    new_support = {"tests/conftest.py": "sha256:bb"}
    base = _claim("R1", tests, hashes)
    head = _claim("R1", tests, hashes)
    base["support_hashes"] = dict(old_support)
    head["support_hashes"] = dict(new_support)
    step = _amendment("R1", tests, tests, hashes, hashes)
    step["old_support_hashes"] = dict(old_support)
    step["new_support_hashes"] = dict(new_support)
    step = _sign(key, step)
    assert authorize(base, head, [step], allow, allow) == (True, "")


def test_signed_runner_digest_amendment_authorizes(tmp_path):
    key, blob = _generate_key(tmp_path, "id_ed25519")
    allow = _allowlist("owner", blob)
    tests = ["tests/test_mod.py::test_name"]
    hashes = {"tests/test_mod.py": "sha256:11"}
    base = _claim("R1", tests, hashes)
    head = _claim("R1", tests, hashes)
    base["runner_digest"] = "sha256:oldrunner"
    head["runner_digest"] = "sha256:newrunner"
    step = _amendment("R1", tests, tests, hashes, hashes)
    step["old_runner_digest"] = "sha256:oldrunner"
    step["new_runner_digest"] = "sha256:newrunner"
    step = _sign(key, step)
    assert authorize(base, head, [step], allow, allow) == (True, "")


def test_canonical_payload_includes_support_and_runner_when_present():
    amendment = _amendment(
        "R1",
        ["tests/test_mod.py::test_a"],
        ["tests/test_mod.py::test_a"],
        {"a.py": "sha256:aa"},
        {"a.py": "sha256:aa"},
    )
    amendment["old_support_hashes"] = {"b.py": "sha256:11", "a.py": "sha256:00"}
    amendment["new_support_hashes"] = {"a.py": "sha256:22"}
    amendment["old_runner_digest"] = "sha256:old"
    amendment["new_runner_digest"] = "sha256:new"
    amendment["signature"] = "not-part-of-the-payload"
    assert canonical_payload(amendment) == (
        "affidavit-amendment v1\n"
        "claim: R1\n"
        "old_tests: tests/test_mod.py::test_a\n"
        "new_tests: tests/test_mod.py::test_a\n"
        "old_hashes:\n"
        "a.py sha256:aa\n"
        "new_hashes:\n"
        "a.py sha256:aa\n"
        "old_support_hashes:\n"
        "a.py sha256:00\n"
        "b.py sha256:11\n"
        "new_support_hashes:\n"
        "a.py sha256:22\n"
        "old_runner_digest: sha256:old\n"
        "new_runner_digest: sha256:new\n"
    ).encode()
