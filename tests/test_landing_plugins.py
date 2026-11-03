from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestra.canon import extensions
from orchestra.conductor.land import LandingResult, LandRequest, dispatch_land


def test_selected_third_party_landing_adapter_runs_without_core_allowlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[LandRequest] = []

    class ExternalAdapter:
        def run(self, request: LandRequest) -> LandingResult:
            seen.append(request)
            return LandingResult("success", 7, "https://example.test/pr/7", "abc123", (), ())

    _repo(tmp_path)
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n'
        '[land]\nadapter = "external-land"\nmerge = "human"\n'
        '[land.config]\nregion = "west"\n',
        encoding="utf-8",
    )
    entry = SimpleNamespace(
        name="external-land",
        value="external_land:Adapter",
        dist=SimpleNamespace(metadata={"Name": "external-land"}, version="1.0"),
        load=lambda: ExternalAdapter,
    )
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda *, group: (entry,))

    result = dispatch_land(tmp_path, "proof packet", base="stable")

    assert result.number == 7
    assert [(request.base, request.proof_packet, request.config) for request in seen] == [
        ("stable", "proof packet", {"region": "west"})
    ]


def test_landing_entry_points_include_builtin_adapters() -> None:
    descriptors = extensions.list_plugins("conductor.land")

    assert {descriptor.plugin_id for descriptor in descriptors} == {"none", "github-pr"}


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
