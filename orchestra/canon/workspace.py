from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from orchestra.canon.errors import StoreNotInitializedError
from orchestra.canon.project import Project, StoreBindingError, bound_store_path, open_store


class Access(Enum):
    READ = "read"
    WRITE = "write"


class StoreNotReady(Exception):
    def __init__(self, searched: tuple[Path, ...] = ()) -> None:
        listed = ", ".join(str(path) for path in searched)
        super().__init__(f"no store found; searched: {listed}")
        self.searched = searched


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
            except (StoreBindingError, StoreNotInitializedError):
                continue
            return cls(root=found.project_root, access=access)
        raise StoreNotReady(tuple(searched))

    @classmethod
    def _pinned(cls, root: Path, access: Access) -> Workspace:
        try:
            pinned = bound_store_path(root)
        except (StoreBindingError, StoreNotInitializedError):
            return cls(root=root, access=access)
        return cls(root=root, store=pinned, access=access)

    def open(self) -> Project:
        try:
            return open_store(self.root, store=self.store, read_only=self.access is Access.READ)
        except (StoreBindingError, StoreNotInitializedError) as exc:
            raise StoreNotReady((self.root,)) from exc
