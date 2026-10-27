from __future__ import annotations

import contextlib
import copy
import importlib
import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

ALPHA: dict[str, Any] = {
    "namespace": "alpha",
    "version": "0.1.0",
    "types": {
        "config": {
            "purpose": "Settings for one component",
            "lifecycle": "current",
            "fields": {
                "title": {"type": "string"},
                "level": {"type": "integer"},
                "ratio": {"type": "number", "optional": True},
                "enabled": {"type": "boolean", "optional": True},
                "mode": {"enum": ["fast", "slow"], "optional": True},
                "tags": {"list": {"type": "string"}, "optional": True},
            },
        },
        "task": {
            "purpose": "A unit of work",
            "lifecycle": "staged",
            "fields": {
                "title": {"type": "string"},
                "owner": {"enum": ["ann", "bob"], "optional": True},
            },
        },
        "log": {
            "purpose": "What happened while working on a task",
            "lifecycle": "event",
            "fields": {
                "task": {"ref": "alpha:task"},
                "message": {"type": "string"},
            },
        },
        "issue": {
            "purpose": "An open question",
            "lifecycle": "question",
            "fields": {
                "summary": {"type": "string"},
                "task": {"ref": "alpha:task", "optional": True},
            },
        },
        "finding": {
            "purpose": "A claim with supporting records",
            "lifecycle": "claim",
            "fields": {
                "statement": {"type": "string"},
                "about": {"ref": ["alpha:task", "alpha:config"], "optional": True},
                "evidence": {
                    "list": {"ref": "alpha:log", "pin": True},
                    "optional": True,
                },
            },
        },
    },
    "migrations": [],
}

BETA: dict[str, Any] = {
    "namespace": "beta",
    "version": "0.1.0",
    "types": {
        "review": {
            "purpose": "A verdict on a task from another namespace",
            "lifecycle": "event",
            "fields": {
                "task": {"ref": "alpha:task"},
                "verdict": {"enum": ["pass", "fail"]},
                "logs": {
                    "list": {"ref": "alpha:log", "pin": True},
                    "optional": True,
                },
                "notes": {"type": "string", "optional": True},
            },
        },
        "plan": {
            "purpose": "The plan for the work",
            "lifecycle": "current",
            "fields": {"goal": {"type": "string"}},
            "sections": ["Orientation"],
        },
    },
}

PLAN_BODY = "## Orientation\n\nStart here.\n"


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@test")
    git(path, "config", "user.name", "test")
    git(path, "commit", "--allow-empty", "-qm", "init")
    return path


class Site:
    """Fake installed distributions that register modules in `canon.schemas`."""

    def __init__(self, root: Path):
        self.root = root
        self.packages: list[str] = []

    def publish(self, module: dict[str, Any], package: str | None = None) -> None:
        namespace = module["namespace"]
        package = package or f"canonfix_{namespace}"
        pkg_dir = self.root / package
        (pkg_dir / "schemas").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "schemas" / "__init__.py").write_text("")
        (pkg_dir / "schemas" / f"{namespace}.json").write_text(json.dumps(module, indent=2))
        dist = self.root / f"{package}-0.1.dist-info"
        dist.mkdir(exist_ok=True)
        (dist / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {package}\nVersion: 0.1\n")
        (dist / "entry_points.txt").write_text(
            f"[canon.schemas]\n{namespace} = {package}.schemas\n"
        )
        if package not in self.packages:
            self.packages.append(package)
        importlib.invalidate_caches()

    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join([str(SRC), str(self.root)])
        env.pop("CANON_READONLY", None)
        env.pop("ARTIFACTS_STORE", None)
        return env


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    home = tmp_path / "conftest-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    for name in (
        "ARTIFACTS_STORE",
        "CANON_READONLY",
        "CANON_SCHEMA_PATH",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def site(tmp_path, monkeypatch):
    root = tmp_path / "site-packages"
    root.mkdir()
    monkeypatch.syspath_prepend(str(root))
    fake = Site(root)
    fake.publish(copy.deepcopy(ALPHA))
    fake.publish(copy.deepcopy(BETA))
    yield fake
    for package in fake.packages:
        sys.modules.pop(package, None)
        sys.modules.pop(f"{package}.schemas", None)
    importlib.invalidate_caches()


@dataclass
class CliResult:
    code: int
    out: str
    err: str

    @property
    def json(self) -> Any:
        return json.loads(self.out)

    @property
    def lines(self) -> list[Any]:
        return [json.loads(line) for line in self.out.splitlines() if line.strip()]


class Cli:
    def __init__(self, root: Path, monkeypatch):
        self.root = root
        self.monkeypatch = monkeypatch

    def __call__(self, *args: str, stdin: str | None = None, root: Path | None = None) -> CliResult:
        from canon import cli

        out, err = io.StringIO(), io.StringIO()
        if stdin is not None:
            self.monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
        argv = ["--root", str(root or self.root), *args]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
        return CliResult(code, out.getvalue(), err.getvalue())

    def ok(self, *args: str, stdin: str | None = None) -> Any:
        result = self(*args, stdin=stdin)
        assert result.code == 0, result.out + result.err
        return result.json if result.out.strip() else None


@pytest.fixture
def repo(tmp_path):
    return make_git_repo(tmp_path / "repo")


@pytest.fixture
def cli(repo, site, monkeypatch):
    return Cli(repo, monkeypatch)


@pytest.fixture
def project(cli, repo):
    from canon.project import open_store

    cli.ok("init", "--schemas", "alpha,beta")
    return open_store(repo)


def payload_of(task: str = "do it") -> dict[str, Any]:
    return {"title": task}


def make_task(project, subject: str, **extra) -> dict[str, Any]:
    return project.create(record_type="alpha:task", subject=subject, payload={"title": subject, **extra})


def advance(project, record: dict[str, Any], *states: str) -> dict[str, Any]:
    for state in states:
        record = project.update(record["id"], transition=state)
    return record
