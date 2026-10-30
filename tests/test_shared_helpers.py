"""Requirements for shared helpers. Already-true requirements pass; the rest fail by assertion."""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GIT_BACKEND = "orchestra/canon/git_backend.py"
SAMPLE_OUTPUT = "FAILED tests/test_mod.py::test_name\n"


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _defines_function(path: Path, name: str) -> bool:
    return any(
        isinstance(node, ast.FunctionDef) and node.name == name for node in ast.walk(_parse(path))
    )


def _mentions_sha256(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute) and child.attr == "sha256":
            return True
        if isinstance(child, ast.Name) and child.id == "sha256":
            return True
    return False


def _looks_like_output_hasher(node: ast.FunctionDef) -> bool:
    if _runs_process(node):
        return False
    if _mentions_sha256(node):
        return True
    lowered = node.name.lower()
    return any(token in lowered for token in ("hash", "sha", "digest"))


def _runs_process(node: ast.AST) -> bool:
    blocked = {"_git", "subprocess", "Popen", "run_git", "open_store"}
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id in blocked:
            return True
        if isinstance(child, ast.Attribute) and child.attr in {"run", "Popen", "check_output"}:
            return True
    return False


def _defined_output_hashers(path: Path) -> list[str]:
    tree = _parse(path)
    module = importlib.import_module(_module_name(path))
    expected = hashlib.sha256(SAMPLE_OUTPUT.encode("utf-8")).hexdigest()
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not _looks_like_output_hasher(node):
            continue
        fn = getattr(module, node.name, None)
        if not callable(fn) or getattr(fn, "__module__", None) != module.__name__:
            continue
        try:
            digest = fn(SAMPLE_OUTPUT)
        except Exception:
            continue
        if digest == expected or digest == f"sha256:{expected}":
            found.append(node.name)
    return found


def _starts_git(path: Path) -> bool:
    for node in ast.walk(_parse(path)):
        if not isinstance(node, (ast.List, ast.Tuple)) or not node.elts:
            continue
        first = node.elts[0]
        if isinstance(first, ast.Constant) and first.value == "git":
            return True
    return False


def _python_files(*roots: Path) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        files.extend(path for path in root.rglob("*.py") if path.is_file())
    return files


def _git_starter_paths() -> list[str]:
    return sorted(
        path.relative_to(ROOT).as_posix()
        for path in _python_files(ROOT / "orchestra", ROOT / "dashboard")
        if _starts_git(path)
    )


def _ssh_keygen_modules() -> list[str]:
    root = ROOT / "orchestra" / "tuner"
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if "ssh-keygen" in path.read_text(encoding="utf-8")
    )


def _generate_key(directory: Path, name: str = "id_ed25519") -> tuple[Path, str]:
    key_path = directory / name
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key_path), "-q"],
        check=True,
        capture_output=True,
    )
    public = subprocess.check_output(["ssh-keygen", "-y", "-f", str(key_path)], text=True).strip()
    return key_path, " ".join(public.split()[:2])


def _allowlist(principal: str, namespace: str, blob: str) -> bytes:
    return f'{principal} namespaces="{namespace}" {blob}\n'.encode()


def _sign(key_path: Path, payload: bytes, namespace: str) -> str:
    completed = subprocess.run(
        ["ssh-keygen", "-Y", "sign", "-f", str(key_path), "-n", namespace],
        input=payload,
        check=True,
        capture_output=True,
    )
    return completed.stdout.decode("utf-8")


def _reads_payload_field(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "get"
            and child.args
            and isinstance(child.args[0], ast.Constant)
            and child.args[0].value == "payload"
        ):
            return True
        slice_node = child.slice if isinstance(child, ast.Subscript) else None
        if isinstance(slice_node, ast.Constant) and slice_node.value == "payload":
            return True
    return False


def _record_payload_getters(path: Path) -> list[str]:
    return sorted(
        {
            node.name
            for node in ast.walk(_parse(path))
            if isinstance(node, ast.FunctionDef)
            and (node.name in {"_payload", "record_payload"} or _reads_payload_field(node))
        }
    )


def _callable_with_record(fn: object) -> bool:
    if not callable(fn):
        return False
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        return False
    positional = [
        param
        for param in signature.parameters.values()
        if param.kind in {param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD}
    ]
    required = [param for param in positional if param.default is inspect.Parameter.empty]
    keyword_required = [
        param
        for param in signature.parameters.values()
        if param.kind is param.KEYWORD_ONLY and param.default is inspect.Parameter.empty
    ]
    return len(required) == 1 and not keyword_required


def _returns_record_payload(fn: object) -> bool:
    if not _callable_with_record(fn):
        return False
    samples = (
        {"id": "rec", "payload": {"a": 1}},
        {"id": "rec", "payload": {}},
        {"id": "rec"},
        {"id": "rec", "payload": None},
        {"id": "rec", "payload": "x"},
        {"id": "rec", "payload": ["a"]},
    )
    try:
        results = [fn(sample) for sample in samples]
    except (Exception, SystemExit):
        return False
    return results == [{"a": 1}, {}, {}, {}, {}, {}]


def _canon_record_payload_getters() -> list[object]:
    found: list[object] = []
    for path in _python_files(ROOT / "orchestra" / "canon"):
        if path.name == "__main__.py":
            continue
        tree = _parse(path)
        candidates = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and _reads_payload_field(node)
        ]
        if not candidates:
            continue
        try:
            module = importlib.import_module(_module_name(path))
        except SystemExit:
            continue
        for name in candidates:
            fn = getattr(module, name, None)
            if getattr(fn, "__module__", None) != module.__name__:
                continue
            if _returns_record_payload(fn):
                found.append(fn)
    return found


def _calls_named(path: Path, name: str) -> bool:
    for node in ast.walk(_parse(path)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == name:
            return True
        if isinstance(func, ast.Attribute) and func.attr == name:
            return True
    return False


def _fails_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "missing-git-dir"))
    return tmp_path


def test_r1_check_defines_parser() -> None:
    """R1: orchestra.conductor.check defines parse_failing_node_ids."""
    assert _defines_function(ROOT / "orchestra" / "conductor" / "check.py", "parse_failing_node_ids")


def test_r2_suite_omits_parser() -> None:
    """R2: orchestra.conductor.suite does not define parse_failing_node_ids."""
    assert not _defines_function(
        ROOT / "orchestra" / "conductor" / "suite.py", "parse_failing_node_ids"
    )


def test_r3_check_defines_hash() -> None:
    """R3: orchestra.conductor.check defines the helper that hashes command output."""
    assert _defined_output_hashers(ROOT / "orchestra" / "conductor" / "check.py")


def test_r4_suite_omits_hash() -> None:
    """R4: orchestra.conductor.suite does not define a helper that hashes command output."""
    assert _defined_output_hashers(ROOT / "orchestra" / "conductor" / "suite.py") == []


def test_r5_git_only_in_backend() -> None:
    """R5: Python files under orchestra/ and dashboard/ start the git executable only in orchestra/canon/git_backend.py."""
    assert _git_starter_paths() == [GIT_BACKEND]


def test_r6_landing_none_on_git_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R6: dashboard.landing.rev_parse_token returns None when the git command fails."""
    from dashboard.backend.landing import rev_parse_token

    root = _fails_git(monkeypatch, tmp_path)
    assert rev_parse_token(root, "HEAD") is None


def test_r7_git_head_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """R7: orchestra.conductor.check.git_head raises when git rev-parse HEAD fails."""
    from orchestra.conductor.check import git_head

    root = _fails_git(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError):
        git_head(root)


def test_r8_ssh_keygen_one_module() -> None:
    """R8: The text ssh-keygen appears under orchestra/tuner/ in only one Python module."""
    modules = _ssh_keygen_modules()
    assert len(modules) == 1


def test_r9_claim_signature(tmp_path: Path) -> None:
    """R9: orchestra.tuner.human_claim.verify_claim_signature returns true for a valid signature."""
    from orchestra.tuner.human_claim import canonical_payload, verify_claim_signature

    key, blob = _generate_key(tmp_path)
    claim_id = "claim-widget"
    text = "the widget is blue"
    signature = _sign(key, canonical_payload(claim_id, text), "tuner-claim")
    assert verify_claim_signature(
        claim_id, text, signature, _allowlist("reviewer", "tuner-claim", blob)
    ) is True


def test_r10_amendment_signature(tmp_path: Path) -> None:
    """R10: Amendment signature verification returns true for a valid signature."""
    from orchestra.tuner.amendment import canonical_payload, verify_signature

    key, blob = _generate_key(tmp_path)
    amendment = {
        "claim": "R1",
        "old_tests": ["tests/test_mod.py::test_name"],
        "new_tests": ["tests/test_mod.py::test_name"],
        "old_hashes": {"tests/test_mod.py": "sha256:11"},
        "new_hashes": {"tests/test_mod.py": "sha256:22"},
    }
    signature = _sign(key, canonical_payload(amendment), "tuner-amendment")
    assert verify_signature(
        canonical_payload(amendment),
        signature,
        _allowlist("owner", "tuner-amendment", blob),
    ) is True


def test_r11_attestation_signature(tmp_path: Path) -> None:
    """R11: Attestation verification returns true for a valid signature."""
    from orchestra.tuner import attestation

    key, blob = _generate_key(tmp_path)
    body = {
        "commit": "a" * 40,
        "manifest_hash": "sha256:" + ("11" * 32),
        "runner_digest": "sha256:" + ("33" * 32),
        "claims": [{"id": "claim-widget", "result": "pass"}],
    }
    signed = attestation.emit(body, key_path=key)
    result = attestation.verify(
        signed,
        _allowlist("ci", "tuner-verdict", blob),
        expected_commit=body["commit"],
        expected_manifest_hash=body["manifest_hash"],
    )
    ok = result[0] if isinstance(result, tuple) else result
    assert ok is True





def test_r15_views_omits_getter() -> None:
    """R15: orchestra.views does not define a record-payload getter."""
    assert _record_payload_getters(ROOT / "orchestra" / "views.py") == []


def test_r16_close_batch_omits_getter() -> None:
    """R16: orchestra.conductor.close_batch does not define a record-payload getter."""
    assert _record_payload_getters(ROOT / "orchestra" / "conductor" / "close_batch.py") == []


def test_r17_model_omits_getter() -> None:
    """R17: dashboard.model does not define a record-payload getter."""
    assert _record_payload_getters(ROOT / "dashboard" / "backend" / "records.py") == []


def test_r18_approval_omits_getter() -> None:
    """R18: dashboard.approval does not define a record-payload getter."""
    assert _record_payload_getters(ROOT / "dashboard" / "backend" / "approval.py") == []


def test_r19_canon_record_payload() -> None:
    """R19: orchestra.canon defines one function that returns a record's payload as a dict."""
    getters = _canon_record_payload_getters()
    assert len(getters) == 1


def test_r20_views_calls_payload() -> None:
    """R20: orchestra.views calls that function."""
    getters = _canon_record_payload_getters()
    assert len(getters) == 1
    assert _calls_named(ROOT / "orchestra" / "views.py", getters[0].__name__)


def test_r21_close_batch_calls_payload() -> None:
    """R21: orchestra.conductor.close_batch calls that function."""
    getters = _canon_record_payload_getters()
    assert len(getters) == 1
    assert _calls_named(ROOT / "orchestra" / "conductor" / "close_batch.py", getters[0].__name__)


def test_r22_model_calls_payload() -> None:
    """R22: dashboard.model calls that function."""
    getters = _canon_record_payload_getters()
    assert len(getters) == 1
    assert _calls_named(ROOT / "dashboard" / "backend" / "records.py", getters[0].__name__)


def test_r23_approval_calls_payload() -> None:
    """R23: dashboard.approval calls that function."""
    getters = _canon_record_payload_getters()
    assert len(getters) == 1
    assert _calls_named(ROOT / "dashboard" / "backend" / "approval.py", getters[0].__name__)
