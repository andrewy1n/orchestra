from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import orchestra.canon.extensions as extensions
from orchestra.cli import main


def test_plugins_list_reports_scopes_without_loading_plugins(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loaded: list[str] = []

    def entry(name: str, target: str, distribution: str) -> SimpleNamespace:
        return SimpleNamespace(
            name=name,
            value=target,
            dist=SimpleNamespace(
                metadata={"Name": distribution, "Orchestra-Plugin-API": "1"},
                version="1.0",
            ),
            load=lambda: loaded.append(name),
        )

    entries = {
        "orchestra.composer.ideas": (entry("acme-ideas", "ideas:Source", "acme"),),
        "orchestra.tuner.verify": (entry("acme-checks", "checks:Technique", "checks"),),
        "orchestra.conductor.land": (entry("acme-land", "land:Adapter", "land"),),
    }
    monkeypatch.setattr(
        extensions.metadata,
        "entry_points",
        lambda *, group: entries.get(group, ()),
    )

    result = main(["plugins", "list", "--format", "json"])
    output = capsys.readouterr().out

    assert result == 0
    assert [plugin["scope"] for plugin in json.loads(output)] == [
        "composer.ideas",
        "conductor.land",
        "tuner.verify",
    ]
    assert loaded == []
