"""Resolve the adaptive-artifacts CLI argv and a directory's store binding."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


def _as_argv(path: Path) -> list[str]:
    if path.name.endswith(".py"):
        return [sys.executable, str(path)]
    return [str(path)]


def _usable(path: Path) -> list[str] | None:
    if path.name.endswith(".py") and path.is_file():
        return _as_argv(path)
    if os.access(path, os.X_OK):
        return _as_argv(path)
    return None


def _plugin_roots() -> list[Path]:
    roots: list[Path] = []
    for key in ("CLAUDE_PLUGIN_ROOT", "CURSOR_PLUGIN_ROOT"):
        raw = os.environ.get(key)
        if not raw:
            continue
        path = Path(raw).expanduser()
        if path.is_dir():
            roots.append(path.resolve())
    return roots


def _search_roots(roots: list[Path]) -> list[str] | None:
    seen: set[Path] = set()
    candidates: list[Path] = []
    for root in roots:
        candidates.extend(
            [
                root / "bin" / "adaptive-artifacts",
                root / "tools" / "artifacts.py",
                root.parent / "adaptive-artifacts" / "bin" / "adaptive-artifacts",
                root.parent / "adaptive-artifacts" / "tools" / "artifacts.py",
            ]
        )
    for candidate in candidates:
        key = candidate.resolve() if candidate.exists() else candidate
        if key in seen:
            continue
        seen.add(key)
        found = _usable(candidate)
        if found is not None:
            return found
    return None


def resolve_aa_command() -> list[str]:
    """Return argv for adaptive-artifacts.

    Order: ADAPTIVE_ARTIFACTS_BIN, ADAPTIVE_ARTIFACTS_ROOT, plugin-root /
    sibling discovery, then PATH. Does not quietly prefer ~/adaptive-artifacts.
    """
    override = os.environ.get("ADAPTIVE_ARTIFACTS_BIN")
    if override:
        return _as_argv(Path(override).expanduser())

    root = os.environ.get("ADAPTIVE_ARTIFACTS_ROOT")
    if root:
        tools = Path(root).expanduser() / "tools" / "artifacts.py"
        if tools.is_file():
            return _as_argv(tools)

    from_plugins = _search_roots(_plugin_roots())
    if from_plugins is not None:
        return from_plugins

    which = shutil.which("adaptive-artifacts")
    if which:
        return [which]

    raise FileNotFoundError(
        "adaptive-artifacts not found. Install it on PATH, set "
        "ADAPTIVE_ARTIFACTS_BIN or ADAPTIVE_ARTIFACTS_ROOT, or run under a "
        "host that sets CLAUDE_PLUGIN_ROOT / CURSOR_PLUGIN_ROOT with a "
        "co-installed adaptive-artifacts plugin."
    )


BINDING_VALUES = frozenset({"local", "global"})
ENV_STORE = "SE_WORKFLOW_STORE"
COMMITTED_BINDING = "store-binding.json"
LOCAL_BINDING = "store-binding.local.json"

StoreKind = Literal["local", "global"]


class StoreBindingError(Exception):
    """Invalid binding or a bound store path that has no meta.json."""


@dataclass(frozen=True)
class Binding:
    store: StoreKind
    source: str


@dataclass(frozen=True)
class Target:
    root: Path
    store: Path | None
    contract: Path | None
    binding: Binding | None = None

    def home_store(self) -> Path:
        return Path.home() / ".artifacts" / self.root.name

    def repo_store(self) -> Path:
        return self.root / ".artifacts"

    def has_view(self, view_id: str) -> bool:
        if self.contract is None:
            return False
        try:
            views = json.loads(self.contract.read_text()).get("views") or []
        except (OSError, ValueError, AttributeError):
            return False
        return any(isinstance(view, dict) and view.get("id") == view_id for view in views)

    def cli_args(self) -> list[str]:
        if self.store is None or self.contract is None:
            raise StoreBindingError(
                f"No usable artifact store for {self.root}"
                + (f" (binding {self.binding.store} from {self.binding.source})" if self.binding else "")
            )
        return ["--root", str(self.root), "--store", str(self.store), "--contract", str(self.contract)]


def project_root(directory: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return directory.resolve()


def _contract_path(store: Path) -> Path | None:
    try:
        ref = json.loads((store / "meta.json").read_text()).get("contract")
    except (OSError, ValueError, AttributeError):
        return None
    if not isinstance(ref, str) or not ref:
        return None
    path = Path(ref)
    if path.is_absolute():
        return path if path.is_file() else None
    # The runtime resolves a relative ref against the store's parent; flat stores keep it inside the store.
    for candidate in (store.parent / path, store / path):
        if candidate.is_file():
            return candidate.resolve()
    return None


def _parse_store_value(raw: object, source: str) -> StoreKind:
    if not isinstance(raw, str) or raw not in BINDING_VALUES:
        raise StoreBindingError(
            f"Invalid store binding from {source}: expected \"local\" or \"global\", got {raw!r}"
        )
    return raw  # type: ignore[return-value]


def _parse_binding_file(path: Path) -> StoreKind:
    source = str(path)
    try:
        data = json.loads(path.read_text())
    except OSError as exc:
        raise StoreBindingError(f"Cannot read store binding {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StoreBindingError(f"Invalid store binding JSON in {source}: {exc}") from exc
    if not isinstance(data, dict) or "store" not in data:
        raise StoreBindingError(
            f"Invalid store binding in {source}: expected object with \"store\" key"
        )
    return _parse_store_value(data.get("store"), source)


def binding_for(root: Path, env: dict[str, str] | None = None) -> Binding | None:
    """Return the explicit binding for root, or None to use default discovery."""
    environ = os.environ if env is None else env
    if ENV_STORE in environ:
        return Binding(_parse_store_value(environ[ENV_STORE], f"env:{ENV_STORE}"), f"env:{ENV_STORE}")
    local_path = root / ".artifacts" / LOCAL_BINDING
    if local_path.is_file():
        return Binding(_parse_binding_file(local_path), str(local_path))
    committed_path = root / ".artifacts" / COMMITTED_BINDING
    if committed_path.is_file():
        return Binding(_parse_binding_file(committed_path), str(committed_path))
    return None


def store_path_for(root: Path, kind: StoreKind) -> Path:
    if kind == "local":
        return root / ".artifacts"
    return Path.home() / ".artifacts" / root.name


def resolve(directory: Path, env: dict[str, str] | None = None) -> Target:
    root = project_root(directory)
    binding = binding_for(root, env=env)
    if binding is not None:
        store = store_path_for(root, binding.store)
        if not (store / "meta.json").is_file():
            raise StoreBindingError(
                f"Store binding {binding.store!r} from {binding.source} points at {store}, "
                f"which has no meta.json"
            )
        return Target(root, store, _contract_path(store), binding)

    repo = root / ".artifacts"
    if (repo / "meta.json").is_file():
        return Target(root, repo, _contract_path(repo), Binding("local", "default"))
    home = Path.home() / ".artifacts" / root.name
    if (home / "meta.json").is_file():
        return Target(root, home, _contract_path(home), Binding("global", "default"))
    return Target(root, None, None, None)
