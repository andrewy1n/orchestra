from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "examples" / "third-party-plugins"


def _run(
    args: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, check=False)


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _json_output(result: subprocess.CompletedProcess[str]) -> object:
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_installed_example_plugins_run_through_public_interfaces(tmp_path: Path) -> None:
    target = tmp_path / "site"
    source = tmp_path / "plugin-source"
    shutil.copytree(PLUGIN_ROOT, source)
    installed = _run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--no-build-isolation",
            "--target",
            str(target),
            str(source),
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert installed.returncode == 0, installed.stderr or installed.stdout
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(target), str(REPO_ROOT)))}

    listing = _json_output(
        _run(
            [
                sys.executable,
                "-c",
                "from orchestra.cli import main; raise SystemExit(main(['plugins', 'list', '--format', 'json']))",
            ],
            cwd=tmp_path,
            env=env,
        )
    )
    assert isinstance(listing, list)
    assert {item["plugin_id"] for item in listing if isinstance(item, dict)} >= {
        "example-ideas",
        "example-checks",
        "example-land",
    }

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "plugin-test@example.com")
    _git(repo, "config", "user.name", "plugin test")
    key = tmp_path / "plugin-key"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
        capture_output=True,
        text=True,
        check=True,
    )
    public_key = subprocess.run(
        ["ssh-keygen", "-y", "-f", str(key)], capture_output=True, text=True, check=True
    ).stdout.strip()
    signer = f'orchestra-test namespaces="orchestra-plugin-evidence" {" ".join(public_key.split()[:2])}\n'
    (repo / ".tuner").mkdir()
    (repo / ".tuner" / "allowed_signers").write_text(signer, encoding="utf-8")
    (repo / "orchestra.toml").write_text(
        '[verify.stages]\nphase = ["example-checks"]\n'
        '[verify.unit]\nrunner = ["python3", "-m", "pytest", "{tests}", "--junitxml={report}"]\n'
        "[verify.example-checks]\nenabled = true\n"
        '[land]\nadapter = "example-land"\nmerge = "human"\n',
        encoding="utf-8",
    )
    _git(repo, "add", "orchestra.toml", ".tuner/allowed_signers")
    _git(repo, "commit", "-qm", "plugin test project")
    revision = _git(repo, "rev-parse", "HEAD")

    verification = _run(
        [
            sys.executable,
            "-c",
            "from orchestra.cli import main; raise SystemExit(main(['verify', 'plugins', '--cwd', "
            f"{str(repo)!r}, '--stage', 'phase', '--key', {str(key)!r}]))",
        ],
        cwd=repo,
        env=env,
    )
    evidence = _json_output(verification)
    assert isinstance(evidence, list)
    assert evidence[0]["plugin_id"] == "example-checks"
    assert evidence[0]["result"] == "pass"

    subprocess.run(
        [sys.executable, "-m", "orchestra.canon.cli", "init", "--schemas", "score,conductor"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    for record_type, subject, payload in (
        (
            "score:effort",
            "plugin-test",
            {"goal": "Test installed plugin commands", "kind": "deliver"},
        ),
        (
            "score:phase",
            "plugin-test",
            {"title": "Plugin test", "effort": "plugin-test", "ordinal": 1},
        ),
        (
            "conductor:proof-packet",
            "plugin-test",
            {
                "phase": "plugin-test",
                "effort": "plugin-test",
                "revision": revision,
                "base": "main",
                "kind": "commands",
            },
        ),
    ):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "orchestra.canon.cli",
                "create",
                "--type",
                record_type,
                "--subject",
                subject,
                "--payload",
                json.dumps(payload),
                "--body",
                (
                    "## Problem\n\nTest installed plugin commands.\n\n"
                    "## Approach\n\nRun installed plugins.\n\n"
                    "## Exit criteria\n\nThe public commands run.\n\n"
                    "## Look\n\nTemporary integration test proof.\n\n"
                    "## Machine\n\nSee the integration test output.\n\n"
                    "## Attention\n\nNone.\n\n## Diff\n\nNo product diff."
                ),
            ],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
    landing = _run(
        [
            sys.executable,
            "-c",
            "from orchestra import cli; cli.gate.gate_terms = lambda *args, **kwargs: []; "
            "raise SystemExit(cli.main(['land', '--phase', 'plugin-test', '--cwd', "
            f"{str(repo)!r}, '--timeout', '1']))",
        ],
        cwd=repo,
        env=env,
    )
    result = json.loads(landing.stdout)
    assert landing.returncode == 1
    assert result["result"] == "skipped"

    ideas = _run(
        [
            sys.executable,
            "-c",
            "from orchestra.composer.idea_source import fetch_plugin_ideas; "
            "item = fetch_plugin_ideas('example-ideas', {'project': 'sample'})[0]; "
            "print(item.external_id)",
        ],
        cwd=tmp_path,
        env=env,
    )
    assert ideas.returncode == 0, ideas.stderr or ideas.stdout
    assert ideas.stdout.strip() == "example-1"
