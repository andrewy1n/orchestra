"""Provider-matrix installer: flags, plans, idempotency, and allowlist.

The tests drive ``orchestra install`` as a subprocess so the observable CLI is
the contract. A fixture source tree lets the allowlist test plant state that
must never be installed (``.artifacts/``, ``.worktrees/``, ``dashboard/``).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from installer.adapters import (
    Adapter,
    ClaudeAdapter,
    CursorAdapter,
    GenericSkillsAdapter,
    OpenCodeAdapter,
    SkillsCliAdapter,
    build_adapter,
    registered_adapters,
)
from installer.agents import load as load_agent
from installer.agents import render as render_agent
from installer.allowlist import COPY_ALLOWLIST, DENY_ROOTS, is_allowed
from installer.matrix import load_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = ".orchestra-install.json"

NPX_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$ORCHESTRA_NPX_LOG"
exit "${ORCHESTRA_NPX_EXIT:-0}"
"""

HOOKS_PAYLOAD = {
    "hooks": {
        "SessionStart": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "orchestra hook-start",
                        "timeout": 30,
                    }
                ]
            }
        ],
        "Stop": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "orchestra hook-stop",
                        "timeout": 30,
                    }
                ]
            }
        ],
    }
}

CANONICAL_AGENT = """---
name: se-reviewer
description: >-
  Fixture phase-end reviewer with one restriction set.
mode: subagent
tools: Read, Grep, Glob, Bash
deny: Write, Edit, NotebookEdit
store_writes: false
---

Fixture reviewer body. Read-only and no store writes.
"""


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    """A repository-shaped tree with allowlisted and forbidden payloads."""
    root = tmp_path / "source"
    for skill in ("init", "plan-phase"):
        skill_dir = root / "skills" / skill
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill}\ndescription: fixture\n---\n", encoding="utf-8"
        )
        reference = skill_dir / "references"
        reference.mkdir()
        (reference / "ensure-store.md").write_text("shared\n", encoding="utf-8")
    (root / "agents").mkdir()
    (root / "agents" / "se-reviewer.md").write_text("reviewer\n", encoding="utf-8")
    (root / "agents" / "reviewer.prompt.md").write_text(
        CANONICAL_AGENT, encoding="utf-8"
    )
    hooks = root / "hosts" / "claude" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "hooks.json").write_text(
        json.dumps(HOOKS_PAYLOAD) + "\n", encoding="utf-8"
    )
    cursor = root / "hosts" / "cursor"
    cursor.mkdir(parents=True)
    (cursor / "hooks.json").write_text(
        json.dumps({"version": 1, "hooks": {}}) + "\n", encoding="utf-8"
    )
    opencode = root / "hosts" / "opencode"
    opencode.mkdir(parents=True)
    (opencode / "plugin.js").write_text("export const Hooks = {}\n", encoding="utf-8")
    (opencode / "opencode.json").write_text(
        json.dumps({"skills": ["./skills"]}) + "\n", encoding="utf-8"
    )
    # Forbidden state: never copied, never linked.
    for name in (".artifacts", ".worktrees", "dashboard", "orchestra", "bin", "scripts"):
        forbidden = root / name
        forbidden.mkdir(parents=True)
        (forbidden / "secret.txt").write_text(f"do not install {name}\n", encoding="utf-8")
    return root


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    return path


@pytest.fixture()
def home(tmp_path: Path) -> Path:
    return tmp_path / "home"


def npx_paths(project: Path) -> tuple[Path, Path]:
    """A fake ``npx`` plus the log it appends each argument line to."""
    bin_dir = project.parent / "fake-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "npx"
    stub.write_text(NPX_STUB, encoding="utf-8")
    stub.chmod(0o755)
    return stub, project.parent / "npx.log"


def npx_calls(project: Path) -> list[str]:
    log = project.parent / "npx.log"
    if not log.is_file():
        return []
    return [line for line in log.read_text(encoding="utf-8").splitlines() if line]


def run_install(
    *args: str,
    project: Path,
    source: Path,
    home: Path | None = None,
    npx_exit: int = 0,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    stub, log = npx_paths(project)
    env["ORCHESTRA_NPX"] = str(stub)
    env["ORCHESTRA_NPX_LOG"] = str(log)
    env["ORCHESTRA_NPX_EXIT"] = str(npx_exit)
    # orchestra/__init__ resolves the sibling affidavit checkout through HOME.
    # Tests redirect HOME, so point it at the real checkout explicitly.
    affidavit_checkout = Path(os.environ.get("AFFIDAVIT_ROOT", Path.home() / "affidavit"))
    if (affidavit_checkout / "affidavit" / "__init__.py").is_file():
        env.setdefault("AFFIDAVIT_ROOT", str(affidavit_checkout))
    if home is not None:
        env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", *args],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
    )


def markers(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(MARKER))


def snapshot(root: Path) -> dict[str, str]:
    """Path -> bytes (copy) or link target (symlink), excluding the marker."""
    state: dict[str, str] = {}
    if not root.exists():
        return state
    for path in sorted(root.rglob("*")):
        if path.name == MARKER:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            state[relative] = "link:" + os.readlink(path)
        elif path.is_file():
            state[relative] = "file:" + path.read_text(encoding="utf-8")
    return state


# -- flags ---------------------------------------------------------------


def test_flags_only_installs_selected_provider(source, project, home):
    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "claude" in proc.stdout
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (home / ".cursor").exists()
    assert markers(home) == [home / ".claude" / MARKER]


def test_flags_only_repeats_in_request_order(source, project, home):
    proc = run_install(
        "--only", "cursor", "--only", "claude", "--home", str(home),
        project=project, source=source,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed_lines = [line for line in proc.stdout.splitlines() if line.startswith("installed ")]
    assert installed_lines[0].startswith("installed cursor")
    assert installed_lines[1].startswith("installed claude")
    assert len(markers(home)) == 2


def test_flags_all_installs_every_matrix_provider(source, project, home):
    expected = load_matrix()
    proc = run_install("--all", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert len(markers(home)) == len(expected)
    for provider in expected:
        assert (home / provider.project_root).is_dir(), provider.id
        payload = json.loads((home / provider.project_root / MARKER).read_text())
        assert payload["provider"] == provider.id


def test_flags_global_installs_under_home(source, project, home):
    proc = run_install("--only", "claude", "--global", "--copy",
                       project=project, source=source, home=home)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (project / ".claude").exists()


def test_flags_copy_switches_from_symlink_to_copy(source, project, home):
    linked = run_install("--only", "claude", "--home", str(home),
                         project=project, source=source)
    assert linked.returncode == 0, linked.stdout + linked.stderr
    linked_skill = home / ".claude" / "skills" / "init"
    assert linked_skill.is_symlink()
    assert linked_skill.resolve() == (source / "skills" / "init").resolve()

    copied = run_install("--only", "claude", "--home", str(home), "--copy",
                         project=project, source=source)
    assert copied.returncode == 0, copied.stdout + copied.stderr
    copied_skill = home / ".claude" / "skills" / "init" / "SKILL.md"
    assert copied_skill.is_file()
    assert not copied_skill.is_symlink()
    assert not copied_skill.parent.is_symlink()
    assert len(markers(home)) == 1


def test_flags_dry_run_writes_nothing(source, project, home):
    proc = run_install("--all", "--home", str(home), "--copy", "--dry-run",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "dry run" in proc.stdout
    assert "install claude" in proc.stdout
    assert "register" in proc.stdout
    assert not home.exists()


def test_flags_uninstall_removes_registration(source, project, home):
    installed = run_install("--only", "claude", "--home", str(home), "--copy",
                            project=project, source=source)
    assert installed.returncode == 0, installed.stdout + installed.stderr
    assert markers(home)

    removed = run_install("--only", "claude", "--home", str(home), "--uninstall",
                          project=project, source=source)
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert "uninstalled claude" in removed.stdout
    assert markers(home) == []
    assert not (home / ".claude").exists()


def test_flags_uninstall_is_safe_to_repeat(source, project, home):
    first = run_install("--only", "claude", "--home", str(home), "--uninstall",
                        project=project, source=source)
    second = run_install("--only", "claude", "--home", str(home), "--uninstall",
                         project=project, source=source)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr
    assert "not installed" in second.stdout
    assert markers(home) == []


def test_flags_reject_unknown_only_provider(source, project, home):
    proc = run_install("--only", "nope", "--home", str(home),
                       project=project, source=source)
    assert proc.returncode == 2
    assert "unknown provider" in proc.stderr
    assert not home.exists()


def test_flags_reject_only_with_all(source, project, home):
    proc = run_install("--only", "claude", "--all", "--home", str(home),
                       project=project, source=source)
    assert proc.returncode == 2
    assert "mutually exclusive" in proc.stderr
    assert not home.exists()


def test_flags_help_lists_documented_flags(source, project):
    proc = run_install("--help", project=project, source=source,
                       home=project.parent / "unused-home")
    assert proc.returncode == 0, proc.stderr
    for flag in ("--only", "--all", "--global", "--copy", "--dry-run", "--uninstall"):
        assert flag in proc.stdout


# -- allowlist -----------------------------------------------------------


def test_allowlist_declares_documented_roots():
    assert COPY_ALLOWLIST == ("skills", "agents")
    assert DENY_ROOTS == (".artifacts", ".worktrees", "dashboard")
    assert is_allowed("skills/init/SKILL.md", "claude")
    assert not is_allowed("contract", "claude")
    assert is_allowed("agents/se-reviewer.md", "claude")
    assert is_allowed("hosts/claude/plugin.json", "claude")


def test_allowlist_rejects_denied_and_foreign_paths():
    for relative in (".artifacts/records", ".worktrees/task", "dashboard/app.py"):
        assert not is_allowed(relative, "claude"), relative
    assert not is_allowed("hosts/cursor/plugin.json", "claude")
    assert not is_allowed("../outside", "claude")
    assert not is_allowed("/etc/passwd", "claude")


def test_allowlist_copy_excludes_artifacts_worktrees_and_dashboard(source, project, home):
    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = sorted(path.relative_to(home).as_posix() for path in home.rglob("*"))
    for relative in installed:
        parts = Path(relative).parts
        assert not any(part in DENY_ROOTS for part in parts), relative
        assert parts[0] == ".claude", relative

    assert not (home / ".claude" / "contract").exists()
    assert (home / ".claude" / "agents" / "se-reviewer.md").is_file()
    assert (home / ".claude" / "hooks" / "hooks.json").is_file()
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (home / ".claude" / "hosts").exists()
    assert not (home / ".claude" / "dashboard").exists()
    assert not (home / ".claude" / ".artifacts").exists()
    assert not (home / ".claude" / ".worktrees").exists()


def test_allowlist_symlink_targets_stay_in_source(source, project, home):
    proc = run_install("--only", "claude", "--home", str(home),
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    links = [path for path in home.rglob("*") if path.is_symlink()]
    assert links
    for link in links:
        target = link.resolve()
        assert source.resolve() in target.parents, link
        relative = target.relative_to(source.resolve()).as_posix()
        assert is_allowed(relative, "claude"), relative


# -- idempotency ---------------------------------------------------------


def test_idempotent_second_install_leaves_one_registration_per_host(source, project, home):
    args = ("--only", "claude", "--only", "cursor", "--home", str(home), "--copy")
    first = run_install(*args, project=project, source=source)
    assert first.returncode == 0, first.stdout + first.stderr
    before = snapshot(home)

    second = run_install(*args, project=project, source=source)
    assert second.returncode == 0, second.stdout + second.stderr
    assert snapshot(home) == before
    assert len(markers(home)) == 2
    for marker in markers(home):
        payload = json.loads(marker.read_text())
        assert len(payload["entries"]) == len(set(payload["entries"]))
    assert second.stdout.count("installed claude") == 1
    assert second.stdout.count("installed cursor") == 1


def test_idempotent_switch_mode_keeps_one_registration(source, project, home):
    assert run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source).returncode == 0
    assert run_install("--only", "claude", "--home", str(home),
                       project=project, source=source).returncode == 0
    assert len(markers(home)) == 1
    payload = json.loads(markers(home)[0].read_text())
    assert payload["mode"] == "symlink"
    assert (home / ".claude" / "skills" / "init").is_symlink()


def test_idempotent_prunes_entries_removed_from_source(source, project, home):
    assert run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source).returncode == 0
    assert (home / ".claude" / "skills" / "plan-phase").is_dir()

    shutil.rmtree(source / "skills" / "plan-phase")
    rerun = run_install("--only", "claude", "--home", str(home), "--copy",
                        project=project, source=source)
    assert rerun.returncode == 0, rerun.stdout + rerun.stderr
    assert not (home / ".claude" / "skills" / "plan-phase").exists()
    payload = json.loads((home / ".claude" / MARKER).read_text())
    assert "skills/plan-phase" not in payload["entries"]
    assert len(markers(home)) == 1


def test_idempotent_uninstall_leaves_nothing_behind(source, project, home):
    assert run_install("--only", "claude", "--only", "cursor", "--home", str(home),
                       "--copy", project=project, source=source).returncode == 0
    assert len(markers(home)) == 2
    for provider in ("claude", "cursor"):
        proc = run_install("--only", provider, "--home", str(home), "--uninstall",
                           project=project, source=source)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert not (home / f".{provider}").exists()
    assert markers(home) == []


# -- protocol and matrix -------------------------------------------------


def test_adapter_protocol_exposes_lifecycle_methods(source, project):
    for name in ("detect", "plan", "apply", "verify", "remove"):
        assert hasattr(GenericSkillsAdapter, name), name
    provider = load_matrix()[0]
    adapter = GenericSkillsAdapter(
        provider,
        base=project,
        scope="project",
        mode="copy",
        source_root=source,
    )
    assert isinstance(adapter, Adapter)
    assert adapter.detect() is False
    plan = adapter.plan()
    assert plan.provider.id == provider.id
    assert plan.entries


def test_matrix_has_native_three_and_a_generic_tail():
    providers = load_matrix()
    ids = {provider.id for provider in providers}
    assert {"claude", "cursor", "opencode"} <= ids
    native = [provider for provider in providers if provider.native]
    tail = [provider for provider in providers if provider.kind == "skills"]
    assert {provider.id for provider in native} >= {"claude", "cursor", "opencode"}
    assert tail and all(provider.profile for provider in tail)


# -- native adapters -----------------------------------------------------


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Top-level frontmatter keys plus the body, ignoring nested host maps."""
    text = path.read_text(encoding="utf-8")
    header, _, body = text.removeprefix("---\n").partition("\n---\n")
    meta: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip() or line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.lstrip("\n")


def test_native_adapters_registered_for_claude_cursor_and_opencode(project, source):
    assert {"claude", "cursor", "opencode"} <= set(registered_adapters())
    expected = {
        "claude": ClaudeAdapter,
        "cursor": CursorAdapter,
        "opencode": OpenCodeAdapter,
    }
    providers = {provider.id: provider for provider in load_matrix()}
    for provider_id, adapter_class in expected.items():
        adapter = build_adapter(
            providers[provider_id],
            base=project,
            scope="project",
            mode="copy",
            source_root=source,
        )
        assert isinstance(adapter, adapter_class), provider_id
        assert isinstance(adapter, Adapter), provider_id


def test_native_claude_installs_skills_agent_and_hooks(source, project, home):
    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    root = home / ".claude"
    assert (root / "skills" / "init" / "SKILL.md").is_file()
    assert not (root / "contract").exists()
    assert (root / "hooks" / "hooks.json").is_file()
    meta, body = frontmatter(root / "agents" / "se-reviewer.md")
    canonical = load_agent(source)
    assert meta["tools"].split(", ") == list(canonical.tools)
    assert body == canonical.body
    assert not (root / "hosts").exists()


def test_native_cursor_installs_read_only_agent_and_hooks(source, project, home):
    proc = run_install("--only", "cursor", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    root = home / ".cursor"
    assert (root / "skills" / "init" / "SKILL.md").is_file()
    assert (root / "hooks.json").is_file()
    meta, body = frontmatter(root / "agents" / "se-reviewer.md")
    assert meta["readonly"] == "true"
    assert body == load_agent(source).body
    assert "tools" not in meta
    assert not (root / "plugin.js").exists()


def test_native_opencode_installs_skills_source_plugin_and_subagent(
    source, project, home
):
    proc = run_install("--only", "opencode", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    root = home / ".opencode"
    assert (root / "skills" / "init" / "SKILL.md").is_file()
    config = json.loads((root / "opencode.json").read_text())
    assert config["skills"] == ["./skills"]
    assert (root / "plugins" / "plugin.js").is_file()
    assert not (root / "plugin.js").exists()
    meta, body = frontmatter(root / "agents" / "se-reviewer.md")
    text = (root / "agents" / "se-reviewer.md").read_text(encoding="utf-8")
    assert meta["mode"] == "subagent"
    assert "permissions:" in text
    assert "  edit: deny" in text
    assert "write:" not in text
    assert "apply_patch:" not in text
    assert body == load_agent(source).body


def test_opencode_plugin_uses_the_v2_default_definition():
    plugin = (
        Path(__file__).resolve().parents[1] / "hosts" / "opencode" / "plugin.js"
    ).read_text(encoding="utf-8")
    assert "export default Plugin.define" in plugin
    assert 'id: "orchestra-hooks"' in plugin
    assert "export const OrchestraHooks" not in plugin


def test_opencode_reinstall_moves_the_legacy_root_plugin(source, project, home):
    args = ("--only", "opencode", "--home", str(home), "--copy")
    assert run_install(*args, project=project, source=source).returncode == 0
    root = home / ".opencode"
    legacy = root / "plugin.js"
    (root / "plugins" / "plugin.js").rename(legacy)
    marker_path = root / MARKER
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["entries"] = [
        "plugin.js" if entry == "plugins/plugin.js" else entry
        for entry in marker["entries"]
    ]
    marker_path.write_text(json.dumps(marker) + "\n", encoding="utf-8")

    proc = run_install(*args, project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not legacy.exists()
    assert (root / "plugins" / "plugin.js").is_file()
    assert "verified: ok" in proc.stdout


def test_native_agent_matches_the_generated_rendering(source, project, home):
    for provider in ("claude", "cursor", "opencode"):
        proc = run_install("--only", provider, "--home", str(home), "--copy",
                           project=project, source=source)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        installed = home / f".{provider}" / "agents" / "se-reviewer.md"
        expected = render_agent(provider, load_agent(source))
        assert installed.read_text(encoding="utf-8") == expected, provider


# -- hooks are optional --------------------------------------------------


def hook_commands(settings: dict) -> list[str]:
    return [
        hook.get("command")
        for groups in settings.get("hooks", {}).values()
        for group in groups
        for hook in group.get("hooks", [])
    ]


def test_hooks_are_installed_for_every_supported_native_host(source, project, home):
    proc = run_install(
        "--only", "claude", "--only", "cursor", "--only", "opencode",
        "--home", str(home), "--copy", project=project, source=source,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    settings = json.loads((home / ".claude" / "settings.json").read_text())
    assert hook_commands(settings) == [
        "orchestra hook-start",
        "orchestra hook-stop",
    ]
    assert (home / ".cursor" / "hooks.json").is_file()
    assert (home / ".opencode" / "plugins" / "plugin.js").is_file()
    assert not (home / ".opencode" / "plugin.js").exists()


def test_claude_hooks_merge_into_the_settings_read_path(source, project, home):
    root = home / ".claude"
    root.mkdir(parents=True)
    preexisting = {
        "permissions": {"allow": ["Bash(git status)"]},
        "env": {"ORCHESTRA_TEST": "1"},
    }
    (root / "settings.json").write_text(
        json.dumps(preexisting) + "\n", encoding="utf-8"
    )

    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    settings = json.loads((root / "settings.json").read_text())
    assert set(settings) == {"permissions", "env", "hooks"}
    assert settings["permissions"] == preexisting["permissions"]
    assert settings["env"] == preexisting["env"]
    assert settings["hooks"] == HOOKS_PAYLOAD["hooks"]


def test_claude_hooks_merge_is_idempotent(source, project, home):
    args = ("--only", "claude", "--home", str(home), "--copy")
    assert run_install(*args, project=project, source=source).returncode == 0
    first = snapshot(home)

    assert run_install(*args, project=project, source=source).returncode == 0
    assert snapshot(home) == first

    settings = json.loads((home / ".claude" / "settings.json").read_text())
    for groups in settings["hooks"].values():
        assert len(groups) == 1


def test_claude_hooks_uninstall_restores_preexisting_settings(source, project, home):
    root = home / ".claude"
    root.mkdir(parents=True)
    preexisting = {"permissions": {"allow": ["Bash(git status)"]}}
    (root / "settings.json").write_text(
        json.dumps(preexisting) + "\n", encoding="utf-8"
    )

    assert run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source).returncode == 0
    removed = run_install("--only", "claude", "--home", str(home), "--uninstall",
                          project=project, source=source)
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert json.loads((root / "settings.json").read_text()) == preexisting
    assert markers(home) == []


def test_claude_hooks_merge_through_a_symlinked_settings_file(source, project, home):
    target = home / "dotfiles" / "claude" / "settings.json"
    target.parent.mkdir(parents=True)
    preexisting = {"permissions": {"allow": ["Bash(git status)"]}}
    target.write_text(json.dumps(preexisting) + "\n", encoding="utf-8")
    root = home / ".claude"
    root.mkdir(parents=True)
    link = root / "settings.json"
    link.symlink_to(target)

    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert link.is_symlink()
    settings = json.loads(link.read_text(encoding="utf-8"))
    assert settings["permissions"] == preexisting["permissions"]
    assert settings["hooks"] == HOOKS_PAYLOAD["hooks"]


def test_claude_uninstall_preserves_a_symlinked_settings_file(source, project, home):
    target = home / "dotfiles" / "claude" / "settings.json"
    target.parent.mkdir(parents=True)
    preexisting = {
        "permissions": {"allow": ["Bash(git status)"]},
        "env": {"ORCHESTRA_TEST": "1"},
    }
    target.write_text(json.dumps(preexisting) + "\n", encoding="utf-8")
    root = home / ".claude"
    root.mkdir(parents=True)
    link = root / "settings.json"
    link.symlink_to(target)

    assert run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source).returncode == 0
    removed = run_install("--only", "claude", "--home", str(home), "--uninstall",
                          project=project, source=source)
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert link.is_symlink()
    assert json.loads(target.read_text(encoding="utf-8")) == preexisting
    assert markers(home) == []


def test_claude_invalid_settings_fails_cleanly(source, project, home):
    root = home / ".claude"
    root.mkdir(parents=True)
    (root / "settings.json").write_text("{not json", encoding="utf-8")

    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 2
    assert "not valid JSON" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert not (root / "skills").exists()
    assert markers(home) == []


def test_claude_broken_settings_symlink_fails_cleanly(source, project, home):
    root = home / ".claude"
    root.mkdir(parents=True)
    link = root / "settings.json"
    link.symlink_to(home / "missing-settings.json")

    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 2
    assert "broken symlink" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert not (root / "skills").exists()
    assert markers(home) == []


def test_hooks_optional_when_a_host_payload_omits_them(source, project, home):
    shutil.rmtree(source / "hosts" / "claude")
    proc = run_install("--only", "claude", "--home", str(home), "--copy",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    root = home / ".claude"
    assert (root / "skills" / "init" / "SKILL.md").is_file()
    assert (root / "agents" / "se-reviewer.md").is_file()
    assert not (root / "hooks").exists()
    assert not (root / "settings.json").exists()
    assert "verified: ok" in proc.stdout


def test_hooks_absent_from_every_host_still_installs(source, project, home):
    shutil.rmtree(source / "hosts")
    proc = run_install(
        "--only", "claude", "--only", "cursor", "--only", "opencode",
        "--home", str(home), "--copy", project=project, source=source,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert len(markers(home)) == 3
    assert not (home / ".claude" / "hooks").exists()
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".cursor" / "hooks.json").exists()
    assert not (home / ".opencode" / "plugins" / "plugin.js").exists()
    assert not (home / ".opencode" / "plugin.js").exists()


# -- skills-CLI tail -----------------------------------------------------


def test_tail_delegates_to_npx_skills_add_and_reports_the_profile(
    source, project, home
):
    proc = run_install("--only", "codex", "--home", str(home),
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert npx_calls(project) == ["skills add -a codex"]
    assert "npx skills add -a codex" in proc.stdout
    assert "profile: codex" in proc.stdout
    payload = json.loads((home / ".codex" / MARKER).read_text())
    assert payload["profile"] == "codex"
    assert payload["entries"] == []
    assert "verified: ok" in proc.stdout


def test_tail_dry_run_reports_the_profile_without_delegating(
    source, project, home
):
    proc = run_install("--only", "gemini", "--home", str(home), "--dry-run",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "delegate npx skills add -a gemini-cli" in proc.stdout
    assert "profile: gemini-cli" in proc.stdout
    assert npx_calls(project) == []
    assert not home.exists()


def test_tail_falls_back_when_npx_fails(source, project, home):
    proc = run_install("--only", "codex", "--home", str(home),
                       project=project, source=source, npx_exit=1)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "fell back" in proc.stdout
    assert "profile: codex" in proc.stdout
    assert (home / ".codex" / "skills" / "init" / "SKILL.md").is_file()
    assert "verified: ok" in proc.stdout


def test_tail_uninstall_names_the_profile_it_leaves_behind(source, project, home):
    assert run_install("--only", "codex", "--home", str(home),
                       project=project, source=source).returncode == 0
    proc = run_install("--only", "codex", "--home", str(home), "--uninstall",
                       project=project, source=source)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "profile codex stays managed by npx skills" in proc.stdout
    assert markers(home) == []


def test_tail_adapter_is_selected_by_matrix_kind(source, project):
    providers = {provider.id: provider for provider in load_matrix()}
    adapter = build_adapter(
        providers["codex"],
        base=project,
        scope="project",
        mode="copy",
        source_root=source,
    )
    assert isinstance(adapter, SkillsCliAdapter)
    assert adapter.profile == "codex"
