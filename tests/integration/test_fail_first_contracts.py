from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_suite_opt_out(tmp_path: Path) -> None:
    (tmp_path / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["unit"]\n[verify.unit]\n'
        'runner = ["pytest", "{tests}", "--junitxml={report}"]\n'
        '[suite]\nmode = "external"\ngate = "required"\n'
    )
    args = ["--phase", "consumer", "--phase-head", "abc1234", "--cwd", str(tmp_path)]
    for action in ("start", "collect", "record"):
        command = [sys.executable, "-m", "orchestra.cli", "suite", action, *args]
        if action == "record":
            command.extend(["--effort", "consumer"])
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == 4, result.stderr
        if action == "record":
            assert "skipped" in result.stderr
        else:
            assert json.loads(result.stdout)["state"] == "skipped"
