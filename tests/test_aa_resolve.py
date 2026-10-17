"""Shared adaptive-artifacts binary resolution order."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from affidavit.aa_resolve import resolve_aa_command
from affidavit import aa
from dashboard import artifact_store


def test_bin_env_wins(tmp_path, monkeypatch):
    bin_path = tmp_path / "aa"
    bin_path.write_text("#!/bin/sh\n")
    bin_path.chmod(0o755)
    monkeypatch.setenv("ADAPTIVE_ARTIFACTS_BIN", str(bin_path))
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_ROOT", raising=False)
    assert resolve_aa_command() == [str(bin_path)]
    assert aa.resolve_aa_command() == [str(bin_path)]


def test_root_env_uses_tools_py(tmp_path, monkeypatch):
    root = tmp_path / "aa-root"
    tools = root / "tools" / "artifacts.py"
    tools.parent.mkdir(parents=True)
    tools.write_text("# aa\n")
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_BIN", raising=False)
    monkeypatch.setenv("ADAPTIVE_ARTIFACTS_ROOT", str(root))
    assert resolve_aa_command() == [sys.executable, str(tools)]


def test_plugin_root_sibling_before_path(tmp_path, monkeypatch):
    plugins = tmp_path / "plugins"
    se = plugins / "affidavit"
    aa_plugin = plugins / "adaptive-artifacts"
    se.mkdir(parents=True)
    bin_path = aa_plugin / "bin" / "adaptive-artifacts"
    bin_path.parent.mkdir(parents=True)
    bin_path.write_text("#!/bin/sh\n")
    bin_path.chmod(0o755)

    path_bin = tmp_path / "path-bin"
    path_bin.mkdir()
    path_aa = path_bin / "adaptive-artifacts"
    path_aa.write_text("#!/bin/sh\n")
    path_aa.chmod(0o755)

    home_aa = tmp_path / "home" / "adaptive-artifacts" / "bin" / "adaptive-artifacts"
    home_aa.parent.mkdir(parents=True)
    home_aa.write_text("#!/bin/sh\n")
    home_aa.chmod(0o755)

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("CLAUDE_PLUGIN_ROOT", str(se))
    monkeypatch.delenv("CURSOR_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_BIN", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_ROOT", raising=False)
    monkeypatch.setenv("PATH", str(path_bin))

    assert resolve_aa_command() == [str(bin_path)]


def test_path_used_when_no_plugin_root(tmp_path, monkeypatch):
    path_bin = tmp_path / "path-bin"
    path_bin.mkdir()
    path_aa = path_bin / "adaptive-artifacts"
    path_aa.write_text("#!/bin/sh\n")
    path_aa.chmod(0o755)

    home_aa = tmp_path / "home" / "adaptive-artifacts" / "bin" / "adaptive-artifacts"
    home_aa.parent.mkdir(parents=True)
    home_aa.write_text("#!/bin/sh\n")
    home_aa.chmod(0o755)

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("CURSOR_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_BIN", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_ROOT", raising=False)
    monkeypatch.setenv("PATH", str(path_bin))

    assert resolve_aa_command() == [str(path_aa)]
    # Home checkout must not win over PATH
    assert "home" not in resolve_aa_command()[0]


def test_home_checkout_not_quiet_fallback(tmp_path, monkeypatch):
    home_aa = tmp_path / "home" / "adaptive-artifacts" / "bin" / "adaptive-artifacts"
    home_aa.parent.mkdir(parents=True)
    home_aa.write_text("#!/bin/sh\n")
    home_aa.chmod(0o755)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("CURSOR_PLUGIN_ROOT", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_BIN", raising=False)
    monkeypatch.delenv("ADAPTIVE_ARTIFACTS_ROOT", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "empty-path"))
    (tmp_path / "empty-path").mkdir()

    with pytest.raises(FileNotFoundError):
        resolve_aa_command()


def test_dashboard_binary_uses_shared_resolver(tmp_path, monkeypatch):
    bin_path = tmp_path / "aa"
    bin_path.write_text("#!/bin/sh\n")
    bin_path.chmod(0o755)
    monkeypatch.setenv("ADAPTIVE_ARTIFACTS_BIN", str(bin_path))
    assert artifact_store.binary() == str(bin_path)
