"""Real-entry-point check for the installer wizard.

The unit tests drive ``installer.wizard`` directly. This test pipes wizard
input through ``bin/orchestra install`` so the CLI parser, detection, prompts,
plan, confirmation, and apply path are exercised together.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKER = ".orchestra-install.json"

CANONICAL_AGENT = """---
name: reviewer
description: Fixture reviewer
---
Fixture reviewer body.
"""


def _make_source(root: Path) -> Path:
    source = root / "source"
    skill = source / "skills" / "init"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: init\ndescription: fixture\n---\n", encoding="utf-8"
    )
    agents = source / "agents"
    agents.mkdir()
    (agents / "reviewer.prompt.md").write_text(CANONICAL_AGENT, encoding="utf-8")
    return source


def test_interactive_end_to_end(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / ".claude").mkdir()
    home = tmp_path / "home"
    home.mkdir()
    source = _make_source(tmp_path)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT), env.get("PYTHONPATH", "")]).strip(
        os.pathsep
    )
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
    env["HOME"] = str(home)
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "orchestra"),
            "install",
            "--interactive",
            "--copy",
        ],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        input="1\n\n\n\n",
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Select hosts" in proc.stdout
    assert "Proceed? [Y/n]:" in proc.stdout
    assert "install claude [copy/project]" in proc.stdout
    assert (project / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert (project / ".claude" / MARKER).is_file()
    assert not (project / ".cursor").exists()
