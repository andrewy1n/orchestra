"""The installed console script runs ``orchestra check --help`` from PATH."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_cli_packaging import cli_env, install_cli


def test_check_help_through_installed_entry_point(tmp_path):
    prefix = tmp_path / "prefix"
    script = install_cli(prefix)
    env = cli_env(prefix)
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()

    proc = subprocess.run(
        ["orchestra", "check", "--help"],
        cwd=str(elsewhere),
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert script.is_file()
    assert "orchestra check" in proc.stdout
    assert "--acceptance" in proc.stdout
