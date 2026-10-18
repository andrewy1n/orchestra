"""Install the package into a temporary prefix and drive the console script.

The CLI must work from a directory that is not the checkout, with only the
installed prefix (scripts + site-packages) on ``PATH``/``PYTHONPATH``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _source_tree(prefix: Path) -> Path:
    """Copy the build inputs out of the checkout so pip leaves no artifacts."""
    source = prefix.parent / "source"
    source.mkdir()
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(REPO_ROOT / name, source / name)
    for name in ("orchestra", "scripts", "contract"):
        shutil.copytree(
            REPO_ROOT / name,
            source / name,
            symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    return source


def install_cli(prefix: Path) -> Path:
    """Install this checkout into ``prefix`` and return the console script."""
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--prefix",
            str(prefix),
            "--no-deps",
            "--no-build-isolation",
            "--no-warn-script-location",
            str(_source_tree(prefix)),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    for candidate in (
        prefix / "bin" / "orchestra",
        prefix / "local" / "bin" / "orchestra",
        prefix / "Scripts" / "orchestra.exe",
    ):
        if candidate.is_file():
            return candidate
    raise AssertionError(f"console script not installed under {prefix}")


def _site_dirs(prefix: Path) -> list[Path]:
    dirs = [
        Path(sysconfig.get_path("purelib", vars={"base": str(prefix), "platbase": str(prefix)})),
        Path(sysconfig.get_path("platlib", vars={"base": str(prefix), "platbase": str(prefix)})),
    ]
    dirs.extend(prefix.glob("**/site-packages"))
    dirs.extend(prefix.glob("**/dist-packages"))
    return sorted({d for d in dirs if d.is_dir()})


def cli_env(prefix: Path) -> dict[str, str]:
    """Environment that resolves ``orchestra`` to the installed prefix only."""
    env = dict(os.environ)
    scripts = [str(prefix / "bin"), str(prefix / "local" / "bin"), str(prefix / "Scripts")]
    env["PATH"] = os.pathsep.join([*scripts, env.get("PATH", "")])
    env["PYTHONPATH"] = os.pathsep.join(
        [*(str(d) for d in _site_dirs(prefix)), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    for name in ("ORCHESTRA_CONTRACT", "ORCHESTRA_SCRIPTS"):
        env.pop(name, None)
    env["PYTHONNOUSERSITE"] = "1"
    return env


@pytest.fixture(scope="session")
def installed(tmp_path_factory) -> tuple[Path, dict[str, str]]:
    prefix = tmp_path_factory.mktemp("orchestra-prefix")
    script = install_cli(prefix)
    return script, cli_env(prefix)


def run_cli(env: dict[str, str], cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["orchestra", *args], cwd=str(cwd), env=env, capture_output=True, text=True
    )


def test_console_script_resolves_on_path_from_unrelated_cwd(installed, tmp_path):
    script, env = installed
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()

    resolved = shutil.which("orchestra", path=env["PATH"])
    assert resolved is not None
    assert Path(resolved).resolve() == script.resolve()

    proc = run_cli(env, elsewhere, "--help")
    assert proc.returncode == 0, proc.stderr
    assert "check" in proc.stdout
    assert "contract" in proc.stdout
    assert "project-field" in proc.stdout
    assert "sessions" in proc.stdout


def test_contract_subcommand_reports_packaged_path(installed, tmp_path):
    _, env = installed
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()

    proc = run_cli(env, elsewhere, "contract", "--path")
    assert proc.returncode == 0, proc.stderr
    path = Path(proc.stdout.strip())
    assert path.is_file()
    assert "orchestra" in path.parts
    assert json.loads(path.read_text())["project"] == "orchestra"
    # The packaged copy matches the checkout's source of truth.
    assert path.read_text() == (REPO_ROOT / "contract" / "project-design.json").read_text()

    body = run_cli(env, elsewhere, "contract")
    assert body.returncode == 0, body.stderr
    assert json.loads(body.stdout)["project"] == "orchestra"

    written = elsewhere / "nested" / "project-design.json"
    write = run_cli(env, elsewhere, "contract", "--write", str(written))
    assert write.returncode == 0, write.stderr
    assert Path(write.stdout.strip()) == written
    assert written.read_text() == (REPO_ROOT / "contract" / "project-design.json").read_text()


def _write_session(root: Path, project: str, name: str, session_id: str) -> None:
    path = root / project / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {
            "type": "user",
            "sessionId": session_id,
            "timestamp": "2026-01-01T00:00:00Z",
            "message": {"role": "user", "content": "prompt text"},
        },
        {
            "type": "assistant",
            "timestamp": "2026-01-01T00:01:00Z",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "1", "name": "Bash", "input": {"cmd": "ls"}}
                ]
            },
        },
    ]
    path.write_text("".join(json.dumps(event) + "\n" for event in events))


def test_installed_subcommands_run_from_unrelated_cwd(installed, tmp_path):
    _, env = installed
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()

    contract = run_cli(env, elsewhere, "contract", "--path")
    assert contract.returncode == 0, contract.stderr
    assert Path(contract.stdout.strip()).is_file()

    design = elsewhere / "project-design.json"
    design.write_text(json.dumps({"project": "affidavit"}))
    rewritten = run_cli(env, elsewhere, "project-field", "rewrite", str(design))
    assert rewritten.returncode == 0, rewritten.stderr
    assert rewritten.stdout.strip() == "rewritten"
    assert json.loads(design.read_text())["project"] == "orchestra"
    current = run_cli(env, elsewhere, "project-field", "rewrite", str(design))
    assert current.stdout.strip() == "current"

    design.write_text(json.dumps({"project": "someone-else"}))
    stopped = run_cli(env, elsewhere, "project-field", "rewrite", str(design))
    assert stopped.returncode == 1
    assert stopped.stdout.strip() == "stopped"
    assert json.loads(design.read_text())["project"] == "someone-else"

    transcripts = elsewhere / "transcripts"
    _write_session(transcripts, "projA", "s1", "s1")
    _write_session(transcripts, "projB", "s2", "s2")

    rows = run_cli(env, elsewhere, "sessions", "report", "--records", str(transcripts))
    assert rows.returncode == 0, rows.stderr
    summaries = [json.loads(line) for line in rows.stdout.splitlines() if line.strip()]
    assert len(summaries) == 2
    assert {row["session_id"] for row in summaries} == {"s1", "s2"}
    assert all(row["records"]["total"] == 0 for row in summaries)

    report_path = elsewhere / "report.jsonl"
    report_path.write_text(rows.stdout)
    aggregate = run_cli(env, elsewhere, "sessions", "aggregate", str(report_path))
    assert aggregate.returncode == 0, aggregate.stderr
    document = json.loads(aggregate.stdout)
    assert document["sessions"] == 2
    assert document["tools"][0]["name"] == "Bash"
