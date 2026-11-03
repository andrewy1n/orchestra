from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestra.tuner.technique import (
    ReplayRequest,
    TechniqueContractError,
    TechniqueResult,
    TestOutcome,
    replay_at_revision,
    run_claim_replay,
    validate_technique_result,
)


class ReplayTechnique:
    def validate_result(self, result: TechniqueResult) -> None:
        if not isinstance(result.output.get("count"), int):
            raise ValueError("expected integer count")

    def replay(self, request: ReplayRequest) -> Mapping[str, TestOutcome]:
        return {test_id: "passed" for test_id in request.test_ids}


class StageOnlyTechnique:
    def validate_result(self, result: TechniqueResult) -> None:
        del result


def _request() -> ReplayRequest:
    return ReplayRequest(Path("."), "revision", ("test_a",), ())


def test_result_uses_shared_verdict_and_structured_output() -> None:
    technique = ReplayTechnique()

    result = validate_technique_result(technique, TechniqueResult("pass", {"count": 2}))

    assert result.verdict == "pass"
    assert result.output == {"count": 2}


def test_technique_owns_output_validation() -> None:
    with pytest.raises(ValueError, match="integer count"):
        validate_technique_result(ReplayTechnique(), TechniqueResult("pass", {"count": "1"}))


def test_shared_contract_rejects_non_structured_output() -> None:
    with pytest.raises(TechniqueContractError, match="structured JSON"):
        validate_technique_result(ReplayTechnique(), TechniqueResult("pass", "text"))


def test_replay_requires_explicit_capability() -> None:
    with pytest.raises(TechniqueContractError, match="replay-capable"):
        run_claim_replay(StageOnlyTechnique(), _request())


def test_replay_returns_one_normalized_outcome_per_witness() -> None:
    assert run_claim_replay(ReplayTechnique(), _request()) == {"test_a": "passed"}


def test_replay_requires_complete_valid_outcomes() -> None:
    class MissingOutcome(ReplayTechnique):
        def replay(self, request: ReplayRequest) -> Mapping[str, TestOutcome]:
            del request
            return {}

    with pytest.raises(TechniqueContractError, match="cover each requested test"):
        run_claim_replay(MissingOutcome(), _request())


def test_selected_third_party_technique_uses_the_shared_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from orchestra.canon import extensions
    from orchestra.plugins import PluginContext, dispatch_plugins

    class ThirdPartyTechnique:
        def run(self, config: object, context: object) -> TechniqueResult:
            del config, context
            return TechniqueResult("pass", {"checks": {"ready": True}})

        def validate_result(self, result: TechniqueResult) -> None:
            if not isinstance(result.output.get("checks"), dict):
                raise ValueError("checks output is required")

    _init_repo(
        tmp_path, '[verify.stages]\nphase = ["external"]\n\n[verify.external]\nmode = "safe"\n'
    )
    entry = SimpleNamespace(
        name="external",
        value="external_plugin:Technique",
        dist=SimpleNamespace(metadata={"Name": "external-plugin"}, version="2.0"),
        load=lambda: ThirdPartyTechnique,
    )
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda *, group: (entry,))
    revision = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = dispatch_plugins(PluginContext(tmp_path, "phase", revision, reviewer_output="unused"))[
        0
    ]

    assert result.plugin_id == "external"
    assert result.result == "pass"
    assert result.output == {"checks": {"ready": True}}


def test_selected_stage_only_technique_cannot_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from orchestra.canon import extensions

    class StageOnlyFactory:
        def validate_result(self, result: TechniqueResult) -> None:
            del result

        def run(self, config: object, context: object) -> TechniqueResult:
            del config, context
            return TechniqueResult("pass", {})

    _init_repo(
        tmp_path,
        '[verify.stages]\nphase = ["stage-only"]\n[verify.replay]\ntechnique = "stage-only"\n',
    )
    entry = SimpleNamespace(
        name="stage-only",
        value="stage_only:Technique",
        dist=SimpleNamespace(metadata={"Name": "stage-only-plugin"}, version="1"),
        load=lambda: StageOnlyFactory,
    )
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda *, group: (entry,))
    revision = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with pytest.raises(TechniqueContractError, match="replay-capable"):
        replay_at_revision(tmp_path, revision, ("test_a",), ())


def _init_repo(root: Path, config: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "test"], check=True)
    (root / "orchestra.toml").write_text(config, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "orchestra.toml"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "config"], check=True)
