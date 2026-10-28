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
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _source_tree(prefix: Path) -> Path:
    """Copy the build inputs out of the checkout so pip leaves no artifacts."""
    source = Path(tempfile.mkdtemp(dir=prefix.parent, prefix="source-"))
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(REPO_ROOT / name, source / name)
    for name in ("orchestra", "scripts"):
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


def run_canon(env: dict[str, str], cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["canon", *args], cwd=str(cwd), env=env, capture_output=True, text=True
    )


def _git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "store-repo"
    root.mkdir()
    for args in (
        ["init", "-q"],
        ["config", "user.email", "test@example.com"],
        ["config", "user.name", "test"],
        ["commit", "--allow-empty", "-qm", "init"],
    ):
        proc = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
    return root


def _scrub_checkout(env: dict[str, str]) -> dict[str, str]:
    scrubbed = dict(env)
    scrubbed.pop("CANON_SCHEMA_PATH", None)
    checkout = str(REPO_ROOT)
    for key in ("PATH", "PYTHONPATH"):
        parts = [
            part
            for part in scrubbed.get(key, "").split(os.pathsep)
            if part and not part.startswith(checkout)
        ]
        if parts:
            scrubbed[key] = os.pathsep.join(parts)
    return scrubbed


def _roadmap_section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    start = text.find(marker)
    assert start != -1, f"missing section {heading!r} in:\n{text}"
    rest = text[start + len(marker) :]
    next_heading = rest.find("\n## ")
    if next_heading == -1:
        return rest
    return rest[:next_heading]


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
    assert "sessions" in proc.stdout


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


def test_installed_idea_and_roadmap_from_unrelated_cwd(installed, tmp_path):
    _, base_env = installed
    env = _scrub_checkout(base_env)
    repo = _git_repo(tmp_path)
    init = run_canon(env, repo, "init", "--schemas", "score,conductor,tuner,composer")
    assert init.returncode == 0, init.stdout + init.stderr

    captured = run_cli(env, repo, "idea", "Try roadmap")
    assert captured.returncode == 0, captured.stdout + captured.stderr

    roadmap = run_cli(env, repo, "view", "roadmap")
    assert roadmap.returncode == 0, roadmap.stdout + roadmap.stderr
    untriaged = _roadmap_section(roadmap.stdout, "untriaged")
    assert "**try-roadmap**" in untriaged


def test_installed_subcommands_run_from_unrelated_cwd(installed, tmp_path):
    _, env = installed
    elsewhere = tmp_path / "unrelated"
    elsewhere.mkdir()

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


def _installed_prefix(script: Path) -> Path:
    return script.parent.parent if script.parent.name == "bin" else script.parent


def _standalone_env(env: dict[str, str], prefix: Path, home: Path) -> dict[str, str]:
    """Strip the checkout from the CLI environment."""
    scrubbed = dict(env)
    scrubbed["HOME"] = str(home)
    for name in (
        "CLAUDE_PLUGIN_ROOT",
        "CURSOR_PLUGIN_ROOT",
        "SE_WORKFLOW_STORE",
    ):
        scrubbed.pop(name, None)

    checkout = str(REPO_ROOT)

    def keep(entry: str) -> bool:
        if not entry:
            return False
        return not entry.startswith(checkout)

    site_dirs = [str(d) for d in _site_dirs(prefix)]
    for key in ("PATH", "PYTHONPATH"):
        parts = [p for p in scrubbed.get(key, "").split(os.pathsep) if keep(p)]
        if parts:
            scrubbed[key] = os.pathsep.join(parts)
        else:
            scrubbed.pop(key, None)
    # Ensure the installed prefix supplies the package and the script.
    script_dirs = [str(prefix / "bin"), str(prefix / "local" / "bin"), str(prefix / "Scripts")]
    scrubbed["PATH"] = os.pathsep.join([*script_dirs, scrubbed.get("PATH", "")]).strip(
        os.pathsep
    )
    scrubbed["PYTHONPATH"] = os.pathsep.join(
        [*site_dirs, scrubbed.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    return scrubbed


def test_cli_standalone_without_checkout(installed, tmp_path):
    """The installed CLI answers from the installed prefix with an empty HOME."""
    script, base_env = installed
    prefix = _installed_prefix(script)
    home = tmp_path / "empty-home"
    home.mkdir()
    env = _standalone_env(base_env, prefix, home)
    elsewhere = tmp_path / "unrelated-standalone"
    elsewhere.mkdir()

    helped = run_cli(env, elsewhere, "--help")
    assert helped.returncode == 0, helped.stderr
    for command in ("check", "install", "sessions"):
        assert command in helped.stdout

    for command in ("check", "install", "sessions"):
        proc = run_cli(env, elsewhere, command, "--help")
        assert proc.returncode == 0, (command, proc.stdout + proc.stderr)

    transcripts = elsewhere / "transcripts"
    _write_session(transcripts, "projA", "s1", "s1")
    rows = run_cli(env, elsewhere, "sessions", "report", str(transcripts))
    assert rows.returncode == 0, rows.stderr
    assert len([line for line in rows.stdout.splitlines() if line.strip()]) == 1

    # install is checkout-side; standalone it must explain, not traceback.
    install = run_cli(env, elsewhere, "install", "--dry-run")
    assert install.returncode == 2
    assert "installer" in install.stderr
    assert "Traceback" not in install.stderr

    module = subprocess.run(
        [sys.executable, "-c", "import orchestra.cli, orchestra.conductor.close_batch"],
        cwd=str(elsewhere),
        env=env,
        capture_output=True,
        text=True,
    )
    assert module.returncode == 0, module.stderr

    helper = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import orchestra.conductor.close_batch as cb\n"
                "print(cb._assertion_level_red({}))\n"
            ),
        ],
        cwd=str(elsewhere),
        env=env,
        capture_output=True,
        text=True,
    )
    assert helper.returncode == 0, helper.stdout + helper.stderr
    assert helper.stdout.strip() == "False"
