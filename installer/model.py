"""Data types shared by the installer, its adapters, and the CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Provider:
    """One row of the provider matrix (``installer/providers.json``)."""

    id: str
    name: str
    kind: str
    project_root: str
    global_root: str
    skills_subdir: str = "skills"
    profile: str | None = None
    detect: tuple[str, ...] = ()

    @property
    def native(self) -> bool:
        return self.kind == "native"


@dataclass(frozen=True)
class Action:
    """One filesystem step in a plan."""

    kind: str  # link | copy | write | remove | register | delegate
    destination: Path
    source: Path | None = None
    unchanged: bool = False
    content: str | None = None

    def render(self) -> str:
        prefix = {
            "link": "link",
            "copy": "copy",
            "write": "write",
            "remove": "remove",
            "register": "register",
            "delegate": "delegate",
        }.get(self.kind, self.kind)
        if self.unchanged:
            prefix = f"{prefix} (unchanged)"
        if self.source is not None:
            return f"{prefix} {self.source} -> {self.destination}"
        return f"{prefix} {self.destination}"


@dataclass(frozen=True)
class Plan:
    """What an adapter would do for one provider at one scope."""

    provider: Provider
    scope: str
    mode: str
    root: Path
    actions: tuple[Action, ...] = ()
    entries: tuple[str, ...] = ()
    uninstall: bool = False
    note: str = ""

    @property
    def has_changes(self) -> bool:
        return any(not action.unchanged for action in self.actions)


@dataclass(frozen=True)
class ApplyResult:
    provider: Provider
    root: Path
    applied: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class VerifyResult:
    provider: Provider
    root: Path
    ok: bool
    problems: tuple[str, ...] = ()


@dataclass(frozen=True)
class RemoveResult:
    provider: Provider
    root: Path
    removed: tuple[str, ...] = ()
    skipped: bool = False
    note: str = ""


@dataclass(frozen=True)
class InstallRequest:
    only: tuple[str, ...] = ()
    all_providers: bool = False
    global_scope: bool = False
    copy: bool = False
    dry_run: bool = False
    uninstall: bool = False
    home: Path | None = None
    source_root: Path | None = None
    cwd: Path | None = None


@dataclass
class InstallReport:
    """Aggregate outcome for ``orchestra install``."""

    plans: list[Plan] = field(default_factory=list)
    applied: list[ApplyResult] = field(default_factory=list)
    verified: list[VerifyResult] = field(default_factory=list)
    removed: list[RemoveResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and all(result.ok for result in self.verified)
