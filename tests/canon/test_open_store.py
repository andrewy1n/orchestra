"""Store selection for canon.project.open_store."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

_PATH_ATTRS = ("store_path", "store", "store_root", "path", "root")


def load_open_store():
    try:
        from orchestra.canon.project import open_store
    except (ImportError, AttributeError) as exc:
        raise AssertionError("orchestra.canon.project.open_store is not available") from exc
    if not callable(open_store):
        raise AssertionError("orchestra.canon.project.open_store is not available")
    return open_store


def isolate(monkeypatch, home: Path) -> None:
    monkeypatch.setenv("HOME", str(home))
    for name in (
        "CANON_STORE",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "CANON_READONLY",
        "SE_WORKFLOW_STORE",
    ):
        monkeypatch.delenv(name, raising=False)


def git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return path


def git_toplevel(directory: Path) -> Path | None:
    proc = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    return Path(proc.stdout.strip()).resolve()


def write_config(store: Path) -> None:
    store.mkdir(parents=True, exist_ok=True)
    (store / "config.json").write_text('{"format": "canon/1", "schemas": {}}\n', encoding="utf-8")


def write_binding(root: Path, filename: str, value: str) -> None:
    path = root / ".canon" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"store": value}) + "\n", encoding="utf-8")


def local_store(root: Path) -> Path:
    return root / ".canon"


def global_store(home: Path, root: Path) -> Path:
    return home / ".canon" / root.name


def file_set(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _as_path(value):
    if callable(value):
        try:
            value = value()
        except TypeError:
            return None
    if isinstance(value, (str, Path)):
        return Path(value)
    if value is None:
        return None
    for attr in ("store_path", "root", "path"):
        inner = getattr(value, attr, None)
        if inner is None:
            continue
        if callable(inner):
            try:
                inner = inner()
            except TypeError:
                continue
        if isinstance(inner, (str, Path)):
            return Path(inner)
    return None


def store_path_of(opened) -> Path:
    for name in _PATH_ATTRS:
        try:
            value = getattr(opened, name)
        except Exception:
            continue
        path = _as_path(value)
        if path is not None:
            return path
    raise AssertionError(f"{type(opened).__name__} does not expose a store path")


def assert_store(opened, expected: Path) -> None:
    got = store_path_of(opened).resolve()
    assert got == expected.resolve(), f"store path {got} != {expected.resolve()}"


def prepared_home(tmp_path, monkeypatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    isolate(monkeypatch, home)
    return home


def test_r1_git_toplevel(tmp_path, monkeypatch):
    open_store = load_open_store()
    prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    subprocess.run(
        ["git", "commit", "--allow-empty", "-qm", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    nested = repo / "sub" / "dir"
    nested.mkdir(parents=True)
    toplevel = git_toplevel(nested)
    assert toplevel == repo.resolve()
    assert toplevel != nested.resolve()
    write_config(local_store(repo))
    write_config(nested / ".canon")
    assert_store(open_store(nested), local_store(repo))

    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree)],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    inner = worktree / "inside"
    inner.mkdir()
    assert git_toplevel(inner) == worktree.resolve()
    write_config(local_store(worktree))
    assert_store(open_store(inner), local_store(worktree))


def test_r2_outside_git(tmp_path, monkeypatch):
    open_store = load_open_store()
    prepared_home(tmp_path, monkeypatch)
    directory = tmp_path / "outside"
    directory.mkdir()
    assert git_toplevel(directory) is None
    write_config(directory / ".canon")
    assert_store(open_store(directory), directory / ".canon")


def test_r3_store_argument(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    explicit = tmp_path / "explicit"
    write_config(explicit)
    write_config(local_store(repo))
    write_config(global_store(home, repo))
    write_binding(repo, "store-binding.local.json", "global")
    write_binding(repo, "store-binding.json", "local")
    assert_store(open_store(repo, store=explicit), explicit)


def test_r4_artifacts_store_env(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    chosen = tmp_path / "chosen"
    write_config(chosen)
    write_config(local_store(repo))
    write_config(global_store(home, repo))
    write_binding(repo, "store-binding.local.json", "local")
    write_binding(repo, "store-binding.json", "global")
    monkeypatch.setenv("CANON_STORE", str(chosen))
    assert_store(open_store(repo), chosen)


def test_r5_local_binding_file(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)

    local_repo = git_repo(tmp_path / "local-repo")
    write_config(local_store(local_repo))
    write_config(global_store(home, local_repo))
    write_binding(local_repo, "store-binding.json", "global")
    write_binding(local_repo, "store-binding.local.json", "local")
    assert_store(open_store(local_repo), local_store(local_repo))

    global_repo = git_repo(tmp_path / "global-repo")
    write_config(local_store(global_repo))
    write_config(global_store(home, global_repo))
    write_binding(global_repo, "store-binding.json", "local")
    write_binding(global_repo, "store-binding.local.json", "global")
    assert_store(open_store(global_repo), global_store(home, global_repo))


def test_r6_committed_binding_file(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)

    local_repo = git_repo(tmp_path / "local-repo")
    write_config(local_store(local_repo))
    write_config(global_store(home, local_repo))
    write_binding(local_repo, "store-binding.json", "local")
    assert_store(open_store(local_repo), local_store(local_repo))

    global_repo = git_repo(tmp_path / "global-repo")
    write_config(local_store(global_repo))
    write_config(global_store(home, global_repo))
    write_binding(global_repo, "store-binding.json", "global")
    assert_store(open_store(global_repo), global_store(home, global_repo))


def test_r7_repo_config(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    write_config(local_store(repo))
    write_config(global_store(home, repo))
    assert_store(open_store(repo), local_store(repo))


def test_r8_home_config(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    local_store(repo).mkdir(parents=True)
    assert not (local_store(repo) / "config.json").is_file()
    write_config(global_store(home, repo))
    assert_store(open_store(repo), global_store(home, repo))


def test_r9_store_argument_missing_config(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    explicit = tmp_path / "explicit"
    explicit.mkdir()
    write_config(local_store(repo))
    write_config(global_store(home, repo))
    write_binding(repo, "store-binding.json", "global")
    before_home = file_set(home)
    before_local = file_set(local_store(repo))
    with pytest.raises(Exception):
        open_store(repo, store=explicit)
    assert file_set(home) == before_home
    assert file_set(local_store(repo)) == before_local


def test_r10_env_missing_config(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    chosen = tmp_path / "chosen"
    chosen.mkdir()
    write_config(local_store(repo))
    write_config(global_store(home, repo))
    write_binding(repo, "store-binding.local.json", "local")
    write_binding(repo, "store-binding.json", "global")
    before_local = file_set(local_store(repo))
    before_global = file_set(global_store(home, repo))
    monkeypatch.setenv("CANON_STORE", str(chosen))
    with pytest.raises(Exception):
        open_store(repo)
    assert file_set(local_store(repo)) == before_local
    assert file_set(global_store(home, repo)) == before_global


def test_r11_binding_missing_config(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)

    global_repo = git_repo(tmp_path / "global-repo")
    write_config(local_store(global_repo))
    global_store(home, global_repo).mkdir(parents=True)
    write_binding(global_repo, "store-binding.local.json", "global")
    before_local = file_set(local_store(global_repo))
    with pytest.raises(Exception):
        open_store(global_repo)
    assert file_set(local_store(global_repo)) == before_local

    local_repo = git_repo(tmp_path / "local-repo")
    local_store(local_repo).mkdir(parents=True)
    write_config(global_store(home, local_repo))
    write_binding(local_repo, "store-binding.json", "local")
    before_global = file_set(global_store(home, local_repo))
    with pytest.raises(Exception):
        open_store(local_repo)
    assert file_set(global_store(home, local_repo)) == before_global


def test_r12_binding_value(tmp_path, monkeypatch):
    open_store = load_open_store()
    home = prepared_home(tmp_path, monkeypatch)

    local_repo = git_repo(tmp_path / "local-repo")
    write_config(local_store(local_repo))
    write_config(global_store(home, local_repo))
    write_binding(local_repo, "store-binding.local.json", "both")
    with pytest.raises(Exception):
        open_store(local_repo)

    committed_repo = git_repo(tmp_path / "committed-repo")
    write_config(local_store(committed_repo))
    write_config(global_store(home, committed_repo))
    write_binding(committed_repo, "store-binding.json", "sideways")
    with pytest.raises(Exception):
        open_store(committed_repo)


def test_r13_no_store(tmp_path, monkeypatch):
    open_store = load_open_store()
    prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    with pytest.raises(Exception):
        open_store(repo)


def test_legacy_meta_json_is_not_a_store(tmp_path, monkeypatch):
    open_store = load_open_store()
    prepared_home(tmp_path, monkeypatch)
    repo = git_repo(tmp_path / "repo")
    (local_store(repo)).mkdir()
    (local_store(repo) / "meta.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(Exception, match="config.json"):
        open_store(repo)
