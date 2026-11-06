"""Canonical SSH-signed evidence produced by built-in verification plugins."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from orchestra.canon.extensions import (
    PluginCatalogError,
    compute_execution_identity,
    resolve_plugin,
    validate_plugin_config,
)
from orchestra.canon.project_config import (
    CONFIG_PATH,
    PluginName,
    ProjectConfigError,
    StageName,
    load_project_config_at_revision,
)
from orchestra.canon.types import JsonObject, JsonValue
from orchestra.tools.git import Git
from orchestra.tuner.manifest import ManifestError, load_allowlist, resolve_commit, runner_digest
from orchestra.tuner.plugins import PluginContext, PluginResult, dispatch_plugins
from orchestra.tuner.sign import sign
from orchestra.tuner.sign import verify as verify_signature
from orchestra.tuner.technique import (
    TechniqueResult,
    VerificationTechnique,
    validate_technique_result,
)

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
    output: JsonObject
    signature: str
    execution_identity: JsonObject


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
    identity, execution_digest, expected_runner = _execution_identity(
        root, commit, result.plugin_id
    )
    if result.execution_identity != identity or result.execution_digest != execution_digest:
        raise ValueError("plugin execution identity does not match the target config and provider")
    if result.runner_digest != expected_runner:
        raise ValueError("plugin result runner digest does not match the target config")
    output = _normalize_output(result.output)
    _validate_plugin_result(root, commit, result.plugin_id, result.result, output)
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
        execution_identity=identity,
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
        execution_identity=evidence.execution_identity,
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
        identity, _execution_digest, expected_runner = _execution_identity(
            root, commit, evidence.plugin_id
        )
        if evidence.execution_identity != identity:
            return False, "execution identity mismatch"
        if evidence.runner_digest != expected_runner:
            return False, "runner digest mismatch"
        output = _normalize_output(evidence.output)
        _validate_plugin_result(root, commit, evidence.plugin_id, evidence.result, output)
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
    return (
        b"orchestra-plugin-evidence "
        + b"v2"
        + b"\n"
        + _canonical_json(_unsigned_payload(evidence))
        + b"\n"
    )


def _unsigned_payload(evidence: PluginEvidence) -> JsonObject:
    payload: JsonObject = {
        "plugin_id": evidence.plugin_id,
        "stage": evidence.stage,
        "commit": evidence.commit,
        "config_digest": evidence.config_digest,
        "runner_digest": evidence.runner_digest,
        "result": evidence.result,
        "output_hash": evidence.output_hash,
        "output": _json_output(evidence.output),
    }
    payload["execution_identity"] = evidence.execution_identity
    return payload


def _execution_identity(
    root: Path | str, commit: str, plugin_id: str
) -> tuple[JsonObject, str, str | None]:
    config = load_project_config_at_revision(root, commit)
    try:
        registration = resolve_plugin("tuner.verify", plugin_id)
        factory = registration.load()
    except PluginCatalogError as exc:
        raise ValueError(str(exc)) from exc
    if not callable(factory):
        raise ValueError(f"verification plugin {plugin_id!r} is not constructible")
    plugin = factory()
    if not isinstance(plugin, VerificationTechnique):
        raise ValueError(f"verification plugin {plugin_id!r} has an invalid technique contract")
    validate_plugin_config(
        plugin_id,
        registration.descriptor.config_shape,
        config.verify_config.get(plugin_id, {}),
    )
    plugin.validate_config(config)
    definition = plugin.execution_definition(config)
    identity = compute_execution_identity(
        registration.descriptor,
        config.verify_config.get(plugin_id, {}),
        definition,
    )
    argv = definition.get("runner_argv")
    arguments = [item for item in argv if isinstance(item, str)] if isinstance(argv, list) else []
    expected_runner = (
        runner_digest(arguments) if isinstance(argv, list) and len(arguments) == len(argv) else None
    )
    return identity.payload, identity.digest, expected_runner


def _normalize_output(output: JsonObject) -> JsonObject:
    return {key: output[key] for key in sorted(output)}


def _validate_plugin_result(
    root: Path | str,
    commit: str,
    plugin_id: str,
    result: str,
    output: JsonObject,
) -> None:
    config = load_project_config_at_revision(root, commit)
    registration = resolve_plugin("tuner.verify", plugin_id)
    factory = registration.load()
    if not callable(factory):
        raise ValueError(f"verification plugin {plugin_id!r} is not constructible")
    plugin = factory()
    if not isinstance(plugin, VerificationTechnique):
        raise ValueError(f"verification plugin {plugin_id!r} has an invalid technique contract")
    validate_plugin_config(
        plugin_id,
        registration.descriptor.config_shape,
        config.verify_config.get(plugin_id, {}),
    )
    plugin.validate_config(config)
    if result not in ("pass", "fail", "error", "skip"):
        raise ValueError(f"verification plugin {plugin_id!r} returned an invalid verdict")
    validate_technique_result(plugin, TechniqueResult(result, output))


def _json_output(output: JsonObject) -> JsonValue:
    return output


def _canonical_json(value: JsonValue) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def _config_digest(root: Path | str, commit: str) -> str:
    blob = Git(Path(root)).show_bytes(commit, CONFIG_PATH)
    if blob is None:
        raise ProjectConfigError(f"cannot load {CONFIG_PATH} at commit {commit}")
    return _digest(blob)


def _digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()
