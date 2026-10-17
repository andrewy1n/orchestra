"""Find the adaptive-artifacts store and runtime binary for a directory."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DASHBOARD_VIEW = "project:dashboard"
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


def aa_command() -> list[str]:
    """Full argv for adaptive-artifacts (shared resolve order)."""
    from affidavit.aa_resolve import resolve_aa_command

    return resolve_aa_command()


def binary() -> str:
    """Legacy single-token form; prefer `aa_command()` for subprocesses."""
    try:
        argv = aa_command()
    except FileNotFoundError:
        return shutil.which("adaptive-artifacts") or "adaptive-artifacts"
    return argv[0] if len(argv) == 1 else argv[-1]
