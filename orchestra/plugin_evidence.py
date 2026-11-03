"""Canonical SSH-signed evidence produced by built-in verification plugins."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.types import JsonObject, JsonValue
from orchestra.plugins import PluginContext, PluginResult, dispatch_plugins
from orchestra.project_config import (
    CONFIG_PATH,
    PluginName,
    ProjectConfigError,
    StageName,
    load_project_config_at_revision,
)
from orchestra.tuner.manifest import (
    ManifestError,
    load_allowlist,
    resolve_commit,
    runner_digest,
)
from orchestra.tuner.sign import sign
from orchestra.tuner.sign import verify as verify_signature

NAMESPACE = "orchestra-plugin-evidence"


@dataclass(frozen=True)
class PluginEvidence:
    plugin_id: PluginName
    stage: StageName
    commit: str
    config_digest: str
    runner_digest: str | None
    result: str
    output_hash: str
    output: Mapping[str, str] | str
    signature: str


def dispatch_signed_plugins(
    context: PluginContext,
    *,
    key_path: Path | str,
) -> tuple[PluginEvidence, ...]:
    """Run configured plugins at the target commit and sign each result."""
    return tuple(
        sign_plugin_result(context.root, result, key_path=key_path)
        for result in dispatch_plugins(context)
    )


def sign_plugin_result(
    root: Path | str,
    result: PluginResult,
    *,
    key_path: Path | str,
) -> PluginEvidence:
    """Bind one built-in result to its committed config and sign it."""
    commit = resolve_commit(root, result.revision)
    config = load_project_config_at_revision(root, commit)
    if result.plugin_id not in config.stages.get(result.stage, ()):
        raise ValueError("plugin is not configured for the target stage")
    expected_runner = runner_digest(config.runner) if result.plugin_id == "unit" else None
    if result.runner_digest != expected_runner:
        raise ValueError("plugin result runner digest does not match the target config")
    output = _normalize_output(result.output)
    evidence = PluginEvidence(
        plugin_id=result.plugin_id,
        stage=result.stage,
        commit=commit,
        config_digest=_config_digest(root, commit),
        runner_digest=expected_runner,
        result=result.result,
        output_hash=_digest(_canonical_json(_json_output(output))),
        output=output,
        signature="",
    )
    signature = sign(NAMESPACE, canonical_payload(evidence), key_path)
    return PluginEvidence(
        plugin_id=evidence.plugin_id,
        stage=evidence.stage,
        commit=evidence.commit,
        config_digest=evidence.config_digest,
        runner_digest=evidence.runner_digest,
        result=evidence.result,
        output_hash=evidence.output_hash,
        output=evidence.output,
        signature=signature,
    )


def verify_plugin_evidence(
    root: Path | str,
    evidence: PluginEvidence,
    *,
    expected_revision: str,
) -> tuple[bool, str]:
    """Verify evidence signature and every target-commit binding."""
    try:
        commit = resolve_commit(root, expected_revision)
        if evidence.commit != commit:
            return False, "commit mismatch"
        config = load_project_config_at_revision(root, commit)
        if evidence.plugin_id not in config.stages.get(evidence.stage, ()):
            return False, "plugin is not configured for the target stage"
        if evidence.config_digest != _config_digest(root, commit):
            return False, "config digest mismatch"
        expected_runner = runner_digest(config.runner) if evidence.plugin_id == "unit" else None
        if evidence.runner_digest != expected_runner:
            return False, "runner digest mismatch"
        output = _normalize_output(evidence.output)
        if evidence.output_hash != _digest(_canonical_json(_json_output(output))):
            return False, "output hash mismatch"
        allowlist = load_allowlist(root, commit)
    except (ManifestError, ProjectConfigError, OSError, ValueError) as exc:
        return False, str(exc)
    if not evidence.signature or not verify_signature(
        NAMESPACE,
        canonical_payload(evidence),
        evidence.signature,
        allowlist,
    ):
        return False, "bad signature"
    return True, ""


def canonical_payload(evidence: PluginEvidence) -> bytes:
    """Return canonical bytes signed for a plugin evidence envelope."""
    return b"orchestra-plugin-evidence v1\n" + _canonical_json(_unsigned_payload(evidence)) + b"\n"


def _unsigned_payload(evidence: PluginEvidence) -> JsonObject:
    return {
        "plugin_id": evidence.plugin_id,
        "stage": evidence.stage,
        "commit": evidence.commit,
        "config_digest": evidence.config_digest,
        "runner_digest": evidence.runner_digest,
        "result": evidence.result,
        "output_hash": evidence.output_hash,
        "output": _json_output(evidence.output),
    }


def _normalize_output(output: Mapping[str, str] | str) -> dict[str, str] | str:
    if isinstance(output, str):
        return output
    return {key: output[key] for key in sorted(output)}


def _json_output(output: Mapping[str, str] | str) -> JsonValue:
    if isinstance(output, str):
        return output
    result: dict[str, JsonValue] = {}
    for key in sorted(output):
        result[key] = output[key]
    return result


def _canonical_json(value: JsonValue) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def _config_digest(root: Path | str, commit: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{CONFIG_PATH}"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise ProjectConfigError(f"cannot load {CONFIG_PATH} at commit {commit}")
    return _digest(completed.stdout)


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()
