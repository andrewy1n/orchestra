from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest

from orchestra import plugin_verify_cli
from orchestra.canon.extensions import PluginDescriptor, compute_execution_identity
from orchestra.canon.project_config import DEFAULT_RUNNER
from orchestra.cli import main as orchestra_main
from orchestra.tuner import plugins
from orchestra.tuner.manifest import runner_digest
from orchestra.tuner.plugin_evidence import (
    NAMESPACE,
    _execution_identity,
    canonical_payload,
    sign_plugin_result,
    verify_plugin_evidence,
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _seed_repo(root: Path, plugin: str = "unit") -> tuple[str, Path, tuple[str, ...]]:
    root.mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "plugin-test@example.com")
    _git(root, "config", "user.name", "plugin test")
    key_path = root.parent / "plugin-evidence-key"
    subprocess.run(
        ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", str(key_path), "-q"],
        check=True,
        capture_output=True,
    )
    public_key = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(key_path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    signer = f'plugin-test namespaces="{NAMESPACE}" {" ".join(public_key.split()[:2])}\n'
    allowed_signers = root / ".tuner" / "allowed_signers"
    allowed_signers.parent.mkdir(parents=True)
    allowed_signers.write_text(signer, encoding="utf-8")
    runner = DEFAULT_RUNNER
    (root / "orchestra.toml").write_text(
        f'[verify.stages]\nphase = ["{plugin}"]\n\n[verify.unit]\nrunner = {list(runner)!r}\n',
        encoding="utf-8",
    )
    _git(root, "add", "orchestra.toml", ".tuner/allowed_signers")
    _git(root, "commit", "-qm", "base")
    return _git(root, "rev-parse", "HEAD"), key_path, runner


def _plugin_result(root: Path, revision: str, runner: tuple[str, ...]) -> plugins.PluginResult:
    identity, execution_digest, expected_runner = _execution_identity(root, revision, "unit")
    return plugins.PluginResult(
        plugin_id="unit",
        stage="phase",
        revision=revision,
        result="pass",
        runner_digest=expected_runner,
        output={"tests/test_widget.py::test_widget": "passed"},
        execution_identity=identity,
        execution_digest=execution_digest,
    )


def _review_result(root: Path, revision: str) -> plugins.PluginResult:
    output = (
        "verdict: PASS\nfindings: []\nintegration:\n"
        "  interfaces: stable\n  assumptions: reviewed\n"
        "  invariants: preserved\n  conflicts: none\n"
    )
    results = plugins.dispatch_plugins(
        plugins.PluginContext(root=root, stage="phase", revision=revision, reviewer_output=output)
    )
    return results[0]


def test_target_commit_is_loaded_for_unit_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "repo"
    revision, _key_path, runner = _seed_repo(root)
    changed_runner = ["python", "-c", "raise SystemExit(0)", "{tests}", "--junitxml={report}"]
    (root / "orchestra.toml").write_text(
        f'[verify.stages]\nphase = ["unit"]\n\n[verify.unit]\nrunner = {changed_runner!r}\n',
        encoding="utf-8",
    )
    calls: list[tuple[str, ...]] = []

    def run_tests(
        root_path: Path, test_ids: tuple[str, ...], argv: tuple[str, ...]
    ) -> dict[str, str]:
        del root_path, test_ids
        calls.append(argv)
        return {"tests/test_widget.py::test_widget": "passed"}

    monkeypatch.setattr(plugins, "run_tests", run_tests)
    context = plugins.PluginContext(
        root=root,
        stage="phase",
        revision=revision,
        tests=("tests/test_widget.py::test_widget",),
    )

    results = plugins.dispatch_plugins(context)

    assert results[0].revision == revision
    assert results[0].runner_digest == runner_digest(runner)
    assert calls == [runner]


def test_runner_digest_uses_canonical_argv(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)

    assert evidence.runner_digest == runner_digest(runner)
    assert evidence.execution_identity is not None
    assert evidence.execution_identity["scope"] == "tuner.verify"
    assert evidence.execution_identity["plugin_id"] == "unit"
    assert evidence.execution_identity["distribution_name"] == "orchestra"
    assert evidence.execution_identity["distribution_version"] == "0.1.0"
    assert evidence.execution_identity["execution_definition"] == {"runner_argv": list(runner)}


def test_execution_identity_canonical_hash_preserves_argv_boundaries() -> None:
    descriptor = PluginDescriptor(
        scope="tuner.verify",
        plugin_id="unit",
        target="orchestra.tuner.plugins:UnitPlugin",
        distribution="orchestra",
        version="1.0",
        api_version="1",
        config_shape={},
    )
    first = compute_execution_identity(
        descriptor, {"value": "same"}, {"runner_argv": ["--path", "a b"]}
    )
    repeat = compute_execution_identity(
        descriptor, {"value": "same"}, {"runner_argv": ["--path", "a b"]}
    )
    changed = compute_execution_identity(
        descriptor, {"value": "same"}, {"runner_argv": ["--path a", "b"]}
    )

    assert first.digest == repeat.digest
    assert first.digest != changed.digest


def test_execution_identity_mismatch_is_rejected_for_each_bound_field(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)
    assert evidence.execution_identity is not None
    mutations = {
        "scope": "composer.ideas",
        "plugin_id": "other",
        "entry_point_target": "other:Plugin",
        "distribution_name": "other",
        "distribution_version": "99",
        "api_version": "99",
        "parameters": {"changed": True},
        "execution_definition": {"runner_argv": ["changed"]},
    }

    for field, value in mutations.items():
        identity = {**evidence.execution_identity, field: value}
        forged = replace(evidence, execution_identity=identity)
        assert verify_plugin_evidence(root, forged, expected_revision=revision) == (
            False,
            "execution identity mismatch",
        )


def test_core_checks_identity_before_signing(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    result = _plugin_result(root, revision, runner)

    with pytest.raises(ValueError, match="execution identity"):
        sign_plugin_result(
            root,
            replace(result, execution_digest="sha256:" + "0" * 64),
            key_path=key_path,
        )


def test_plugin_payload_uses_v2_and_binds_execution_identity() -> None:
    from orchestra.tuner.plugin_evidence import PluginEvidence

    evidence = PluginEvidence(
        plugin_id="unit",
        stage="phase",
        commit="commit",
        config_digest="config",
        runner_digest="runner",
        result="pass",
        output_hash="output",
        output={"test": "passed"},
        signature="",
        execution_identity={"digest": "sha256:identity"},
    )

    assert canonical_payload(evidence) == (
        b'orchestra-plugin-evidence v2\n{"commit":"commit","config_digest":"config",'
        b'"execution_identity":{"digest":"sha256:identity"},'
        b'"output":{"test":"passed"},"output_hash":"output","plugin_id":"unit",'
        b'"result":"pass","runner_digest":"runner","stage":"phase"}\n'
    )


def test_allowlisted_signature_verifies(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)

    assert verify_plugin_evidence(root, evidence, expected_revision=revision) == (True, "")


def test_invalid_signature_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)
    forged = replace(evidence, signature="invalid signature")

    assert verify_plugin_evidence(root, forged, expected_revision=revision) == (
        False,
        "bad signature",
    )


def test_mismatched_commit_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)
    (root / "README.md").write_text("next commit\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-qm", "next")

    assert verify_plugin_evidence(root, evidence, expected_revision="HEAD") == (
        False,
        "commit mismatch",
    )


def test_mismatched_runner_digest_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    evidence = sign_plugin_result(root, _plugin_result(root, revision, runner), key_path=key_path)
    forged = replace(evidence, runner_digest="sha256:" + "0" * 64)

    assert verify_plugin_evidence(root, forged, expected_revision=revision) == (
        False,
        "runner digest mismatch",
    )


def test_actual_review_verdict_is_signed_and_verified(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, _runner = _seed_repo(root, plugin="review")
    result = _review_result(root, revision)

    evidence = sign_plugin_result(root, result, key_path=key_path)

    assert evidence.result == "pass"
    assert isinstance(evidence.output, dict)
    assert evidence.output["verdict"] == "PASS"
    assert verify_plugin_evidence(root, evidence, expected_revision=revision) == (True, "")


def test_review_evidence_cannot_sign_ready_or_mismatched_verdict(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    revision, key_path, _runner = _seed_repo(root, plugin="review")
    result = _review_result(root, revision)

    with pytest.raises(ValueError, match="invalid verdict"):
        sign_plugin_result(root, replace(result, result="ready"), key_path=key_path)


def test_verify_plugins_cli_signs_host_reviewer_stdin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "repo"
    _seed_repo(root, plugin="review")
    key_path = tmp_path / "plugin-evidence-key"
    monkeypatch.setattr(
        "sys.stdin",
        StringIO(
            "verdict: PASS\nfindings: []\nintegration:\n"
            "  interfaces: stable\n  assumptions: reviewed\n"
            "  invariants: preserved\n  conflicts: none\n"
        ),
    )

    result = orchestra_main(
        [
            "verify",
            "plugins",
            "--cwd",
            str(root),
            "--stage",
            "phase",
            "--review-output",
            "-",
            "--key",
            str(key_path),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output[0]["plugin_id"] == "review"
    assert output[0]["result"] == "pass"
    assert output[0]["output"]["verdict"] == "PASS"
    assert output[0]["signature"]


def test_signed_skip_does_not_pass_verification_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "repo"
    revision, key_path, runner = _seed_repo(root)
    skipped = sign_plugin_result(
        root,
        replace(_plugin_result(root, revision, runner), result="skip"),
        key_path=key_path,
    )
    monkeypatch.setattr(
        plugin_verify_cli,
        "dispatch_signed_plugins",
        lambda _context, key_path: (skipped,),
    )

    result = plugin_verify_cli.main(
        ["--cwd", str(root), "--stage", "phase", "--key", str(key_path)]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 1
    assert output[0]["result"] == "skip"
    assert output[0]["signature"]
