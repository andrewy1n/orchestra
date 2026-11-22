from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from orchestra.canon.errors import StoreNotInitializedError
from orchestra.canon.project import (
    NoArtifactStoreError,
    Project,
    StoreBindingError,
    bound_store_path,
    open_store,
)
from orchestra.tools.command_kit import CommandError


class Access(Enum):
    READ = "read"
    WRITE = "write"


class StoreNotReady(Exception):
    def __init__(
        self, searched: tuple[Path, ...] = (), cause: StoreBindingError | None = None
    ) -> None:
        listed = ", ".join(str(path) for path in searched)
        detail = f"{cause}; " if cause is not None else ""
        super().__init__(f"no store found; {detail}searched: {listed}")
        self.searched = searched
        self.cause = cause


def not_ready_message(error: StoreNotReady, start: Path) -> str:
    searched = ", ".join(str(path) for path in error.searched)
    if error.cause is not None and not isinstance(error.cause, NoArtifactStoreError):
        return f"store_not_ready: {error.cause}; searched: {searched}"
    return f"store_not_ready: No artifact store for {start.resolve()}; searched: {searched}"


@dataclass(frozen=True)
class Workspace:
    root: Path
    store: Path | None = None
    access: Access = Access.WRITE

    @classmethod
    def resolve(
        cls, start: Path, store: Path | None = None, access: Access = Access.WRITE
    ) -> Workspace:
        if store is not None:
            return cls._pinned(Path(store).expanduser(), access)
        env = os.environ.get("ORCHESTRA_STORE")
        if env:
            return cls._pinned(Path(env).expanduser(), access)
        current = start.resolve()
        searched: list[Path] = []
        for candidate in [current, *current.parents]:
            searched.append(candidate)
            try:
                found = open_store(candidate, read_only=True)
            except (NoArtifactStoreError, StoreNotInitializedError):
                continue
            except StoreBindingError as exc:
                raise StoreNotReady(tuple(searched), exc) from exc
            return cls(root=found.project_root, access=access)
        raise StoreNotReady(tuple(searched))

    @classmethod
    def _pinned(cls, root: Path, access: Access) -> Workspace:
        try:
            pinned = bound_store_path(root)
        except (NoArtifactStoreError, StoreNotInitializedError):
            return cls(root=root, access=access)
        except StoreBindingError as exc:
            raise StoreNotReady((root,), exc) from exc
        return cls(root=root, store=pinned, access=access)

    def open(self) -> Project:
        try:
            return open_store(self.root, store=self.store, read_only=self.access is Access.READ)
        except StoreBindingError as exc:
            raise StoreNotReady((self.root,), exc) from exc
        except StoreNotInitializedError as exc:
            raise StoreNotReady((self.root,)) from exc


def open_for_command(
    start: Path, access: Access, *, store: Path | None = None, refused_exit: int = 2
) -> Project:
    try:
        return Workspace.resolve(start, store, access).open()
    except StoreNotReady as error:
        raise CommandError(not_ready_message(error, start), refused_exit) from error
