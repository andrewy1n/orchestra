"""A temporary-HOME install loads native payloads for Claude and OpenCode.

This drives the real checkout as the install source: every advertised skill
directory, the generated reviewer agent, and the optional hook payload must
land under the host roots, survive a re-run unchanged, and uninstall cleanly.
The skills-CLI tail is exercised through a fake ``npx`` so no network or npm
access is needed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKER = ".orchestra-install.json"

NPX_STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$ORCHESTRA_NPX_LOG"
exit 0
"""


def install(source: Path, home: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["HOME"] = str(home)
    env["ORCHESTRA_NPX"] = str(home.parent / "fake-bin" / "npx")
    env["ORCHESTRA_NPX_LOG"] = str(home.parent / "npx.log")
    stub = Path(env["ORCHESTRA_NPX"])
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_text(NPX_STUB, encoding="utf-8")
    stub.chmod(0o755)
    return subprocess.run(
        [sys.executable, "-m", "orchestra.cli", "install", *args],
        cwd=str(home.parent),
        env=env,
        capture_output=True,
        text=True,
    )


def skill_directories(root: Path) -> list[Path]:
    return sorted(path.parent for path in root.glob("*/SKILL.md"))


def assert_skills_load(root: Path) -> None:
    skills = skill_directories(root)
    assert skills, f"no skills installed under {root}"
    for skill in skills:
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---\n"), skill
        assert f"name: {skill.name}\n" in text, skill
        for reference in (skill / "references").glob("*"):
            if reference.is_file():
                assert reference.resolve().is_relative_to(skill.resolve()), reference


def snapshot(root: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.name == MARKER or not path.is_file():
            continue
        state[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8")
    return state


def test_temp_home_install_claude_and_opencode(tmp_path):
    home = tmp_path / "home"

    proc = install(
        REPO_ROOT, home, "--only", "claude", "--only", "opencode",
        "--global", "--copy",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "verified: ok" in proc.stdout

    claude = home / ".claude"
    opencode = home / ".config" / "opencode"

    assert_skills_load(claude / "skills")
    assert_skills_load(opencode / "skills")

    assert not (claude / "contract").exists()
    assert (claude / "agents" / "reviewer.md").is_file()
    assert (claude / "hooks" / "hooks.json").is_file()

    assert not (opencode / "contract").exists()
    assert (opencode / "agents" / "reviewer.md").is_file()
    assert (opencode / "plugins" / "plugin.js").is_file()
    assert not (opencode / "plugin.js").exists()
    config = json.loads((opencode / "opencode.json").read_text(encoding="utf-8"))
    assert config["skills"] == ["./skills"]

    reviewer = (claude / "agents" / "reviewer.md").read_text(encoding="utf-8")
    assert "tools: Read, Grep, Glob, Bash" in reviewer
    opencode_reviewer = (opencode / "agents" / "reviewer.md").read_text(
        encoding="utf-8"
    )
    assert "mode: subagent" in opencode_reviewer
    assert "  edit: deny" in opencode_reviewer
    assert "write:" not in opencode_reviewer

    before = {path: snapshot(path) for path in (claude, opencode)}
    again = install(
        REPO_ROOT, home, "--only", "claude", "--only", "opencode",
        "--global", "--copy",
    )
    assert again.returncode == 0, again.stdout + again.stderr
    assert {path: snapshot(path) for path in (claude, opencode)} == before
    assert (claude / MARKER).is_file()
    assert (opencode / MARKER).is_file()

    removed = install(
        REPO_ROOT, home, "--only", "claude", "--only", "opencode",
        "--global", "--uninstall",
    )
    assert removed.returncode == 0, removed.stdout + removed.stderr
    assert not claude.exists()
    assert not opencode.exists()


def test_temp_home_install_uses_skills_cli_for_a_generic_host(tmp_path):
    home = tmp_path / "home"
    proc = install(REPO_ROOT, home, "--only", "codex", "--global")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "profile: codex" in proc.stdout
    log = (home.parent / "npx.log").read_text(encoding="utf-8")
    assert "skills add -a codex" in log
    payload = json.loads(
        (home / ".codex" / MARKER).read_text(encoding="utf-8")
    )
    assert payload["profile"] == "codex"
