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

from installer.adapters import Adapter, GenericSkillsAdapter
from installer.allowlist import COPY_ALLOWLIST, DENY_ROOTS, is_allowed
from installer.matrix import load_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
MARKER = ".orchestra-install.json"


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
    (root / "contract").mkdir()
    (root / "contract" / "project-design.json").write_text("{}\n", encoding="utf-8")
    (root / "agents").mkdir()
    (root / "agents" / "se-reviewer.md").write_text("reviewer\n", encoding="utf-8")
    for host in ("claude", "cursor"):
        host_dir = root / "hosts" / host
        host_dir.mkdir(parents=True)
        (host_dir / "plugin.json").write_text(
            json.dumps({"name": host}) + "\n", encoding="utf-8"
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


def run_install(
    *args: str,
    project: Path,
    source: Path,
    home: Path | None = None,
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    env["ORCHESTRA_INSTALL_SOURCE"] = str(source)
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
    assert COPY_ALLOWLIST == ("skills", "contract", "agents")
    assert DENY_ROOTS == (".artifacts", ".worktrees", "dashboard")
    assert is_allowed("skills/init/SKILL.md", "claude")
    assert is_allowed("contract", "claude")
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

    assert (home / ".claude" / "contract" / "project-design.json").is_file()
    assert (home / ".claude" / "agents" / "se-reviewer.md").is_file()
    assert (home / ".claude" / "hosts" / "claude" / "plugin.json").is_file()
    assert (home / ".claude" / "skills" / "init" / "SKILL.md").is_file()
    assert not (home / ".claude" / "hosts" / "cursor").exists()
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
