"""Adapter protocol plus the generic skills-directory implementation.

Native adapters for Claude Code, Cursor, and OpenCode live in
:mod:`installer.adapters.native` and register themselves with
:func:`installer.adapters.register_adapter`. Non-native matrix rows delegate to
:class:`installer.adapters.tail.SkillsCliAdapter`; anything else keeps the
generic behaviour here.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Protocol, runtime_checkable

from installer.allowlist import IGNORE_NAMES, IGNORE_SUFFIXES, is_allowed
from installer.model import (
    Action,
    ApplyResult,
    Plan,
    Provider,
    RemoveResult,
    VerifyResult,
)

REGISTRATION = ".orchestra-install.json"
SCHEMA_VERSION = 1


@runtime_checkable
class Adapter(Protocol):
    """The five lifecycle methods every host adapter exposes."""

    provider: Provider

    def detect(self) -> bool: ...

    def plan(self, *, uninstall: bool = False) -> Plan: ...

    def apply(self, plan: Plan) -> ApplyResult: ...

    def verify(self) -> VerifyResult: ...

    def remove(self) -> RemoveResult: ...


def _ignore(directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES or name.endswith(IGNORE_SUFFIXES)}


def _same_tree(left: Path, right: Path) -> bool:
    """Byte-identical trees, ignoring interpreter and editor housekeeping."""
    if left.is_symlink() or right.is_symlink():
        return False
    if left.is_file() and right.is_file():
        try:
            return left.read_bytes() == right.read_bytes()
        except OSError:
            return False
    if not (left.is_dir() and right.is_dir()):
        return False
    left_names = {
        n for n in os.listdir(left) if n not in IGNORE_NAMES and not n.endswith(IGNORE_SUFFIXES)
    }
    right_names = {
        n for n in os.listdir(right) if n not in IGNORE_NAMES and not n.endswith(IGNORE_SUFFIXES)
    }
    if left_names != right_names:
        return False
    return all(_same_tree(left / name, right / name) for name in left_names)


class BaseAdapter:
    """Allowlist-only install into a provider's root directory."""

    def __init__(
        self,
        provider: Provider,
        *,
        base: Path,
        scope: str,
        mode: str,
        source_root: Path,
    ) -> None:
        if scope not in ("project", "global"):
            raise ValueError(f"unknown install scope {scope!r}")
        if mode not in ("symlink", "copy"):
            raise ValueError(f"unknown install mode {mode!r}")
        self.provider = provider
        self.base = Path(base)
        self.scope = scope
        self.mode = mode
        self.source_root = Path(source_root)
        relative_root = provider.global_root if scope == "global" else provider.project_root
        self.root = (self.base / relative_root).expanduser()
        self.marker = self.root / REGISTRATION

    # -- protocol -------------------------------------------------------

    def detect(self) -> bool:
        """Whether this host already has a footprint at the install base."""
        if self.marker.is_file():
            return True
        if not self.provider.detect:
            return self.root.parent.is_dir()
        return any((self.base / item).exists() for item in self.provider.detect)

    def plan(self, *, uninstall: bool = False) -> Plan:
        if uninstall:
            previous = self._read_marker()
            if previous is None:
                return Plan(
                    provider=self.provider,
                    scope=self.scope,
                    mode=self.mode,
                    root=self.root,
                    uninstall=True,
                    note="not installed",
                )
            actions = tuple(
                Action(kind="remove", destination=self.root / entry)
                for entry in previous["entries"]
            )
            actions += (Action(kind="remove", destination=self.marker),)
            return Plan(
                provider=self.provider,
                scope=self.scope,
                mode=self.mode,
                root=self.root,
                actions=actions,
                entries=tuple(previous["entries"]),
                uninstall=True,
            )

        desired = self.desired_entries()
        generated = self.generated_entries()
        overlap = set(desired) & set(generated)
        if overlap:
            raise ValueError(
                "generated entries collide with source entries: " + ", ".join(sorted(overlap))
            )
        actions: list[Action] = []
        for entry, source in desired.items():
            destination = self.root / entry
            unchanged = self._matches(destination, source)
            actions.append(
                Action(
                    kind="link" if self.mode == "symlink" else "copy",
                    destination=destination,
                    source=source,
                    unchanged=unchanged,
                )
            )
        for entry, text in generated.items():
            destination = self.root / entry
            actions.append(
                Action(
                    kind="write",
                    destination=destination,
                    unchanged=self._text_matches(destination, text),
                    content=text,
                )
            )
        actions.append(Action(kind="register", destination=self.marker))
        return Plan(
            provider=self.provider,
            scope=self.scope,
            mode=self.mode,
            root=self.root,
            actions=tuple(actions),
            entries=tuple((*desired, *generated)),
        )

    def apply(self, plan: Plan) -> ApplyResult:
        self.root.mkdir(parents=True, exist_ok=True)
        previous = self._read_marker()
        previous_entries = tuple(previous["entries"]) if previous else ()

        applied: list[str] = []
        unchanged: list[str] = []
        removed: list[str] = []
        desired = set(plan.entries)

        for entry in sorted(set(previous_entries) - desired, reverse=True):
            destination = self.root / entry
            if destination.exists() or destination.is_symlink():
                self._remove_entry(destination)
                removed.append(entry)

        for action in plan.actions:
            if action.kind == "register":
                continue
            entry = action.destination.relative_to(self.root).as_posix()
            if action.kind == "write":
                text = action.content or ""
                if action.unchanged and self._text_matches(action.destination, text):
                    unchanged.append(entry)
                    continue
                self._remove_entry(action.destination)
                self._write_text(action.destination, text)
                applied.append(entry)
                continue
            if (
                action.unchanged
                and action.source is not None
                and self._matches(action.destination, action.source)
            ):
                unchanged.append(entry)
                continue
            self._remove_entry(action.destination)
            if action.source is None:
                continue
            self._install_entry(action.destination, action.source)
            applied.append(entry)

        self._write_marker(plan.entries)
        return ApplyResult(
            provider=self.provider,
            root=self.root,
            applied=tuple(applied),
            unchanged=tuple(unchanged),
            removed=tuple(removed),
        )

    def verify(self) -> VerifyResult:
        problems: list[str] = []
        marker = self._read_marker()
        if marker is None:
            return VerifyResult(
                provider=self.provider,
                root=self.root,
                ok=False,
                problems=("registration missing",),
            )
        if marker["provider"] != self.provider.id:
            problems.append(
                f"registration names {marker['provider']!r}, expected {self.provider.id!r}"
            )
        if marker["scope"] != self.scope:
            problems.append(f"registration scope is {marker['scope']!r}, expected {self.scope!r}")
        if marker["mode"] != self.mode:
            problems.append(f"registration mode is {marker['mode']!r}, expected {self.mode!r}")

        desired = self.desired_entries()
        generated = self.generated_entries()
        wanted = set(desired) | set(generated)
        recorded = marker["entries"]
        missing = [entry for entry in wanted if entry not in recorded]
        stale = [entry for entry in recorded if entry not in wanted]
        if missing:
            problems.append(f"unregistered payload: {', '.join(sorted(missing))}")
        if stale:
            problems.append(f"stale registration: {', '.join(sorted(stale))}")
        for entry, source in desired.items():
            destination = self.root / entry
            if not (destination.exists() or destination.is_symlink()):
                problems.append(f"missing {entry}")
            elif not self._matches(destination, source):
                problems.append(f"modified {entry}")
        for entry, text in generated.items():
            destination = self.root / entry
            if not (destination.exists() or destination.is_symlink()):
                problems.append(f"missing {entry}")
            elif not self._text_matches(destination, text):
                problems.append(f"modified {entry}")
        return VerifyResult(
            provider=self.provider,
            root=self.root,
            ok=not problems,
            problems=tuple(problems),
        )

    def remove(self) -> RemoveResult:
        marker = self._read_marker()
        if marker is None:
            return RemoveResult(provider=self.provider, root=self.root, skipped=True)
        removed: list[str] = []
        parents = {
            (self.root / entry).parent
            for entry in marker["entries"]
            if (self.root / entry).parent != self.root
        }
        for entry in sorted(marker["entries"], reverse=True):
            destination = self.root / entry
            if destination.exists() or destination.is_symlink():
                self._remove_entry(destination)
                removed.append(entry)
        if self.marker.exists() or self.marker.is_symlink():
            self.marker.unlink()
        for parent in sorted(parents, key=lambda path: len(path.parts), reverse=True):
            self._prune_empty(parent)
        self._prune_empty(self.root)
        return RemoveResult(
            provider=self.provider,
            root=self.root,
            removed=tuple(removed),
        )

    # -- generic helpers ------------------------------------------------

    def desired_entries(self) -> dict[str, Path]:
        """Allowlisted source paths keyed by destination-relative path."""
        entries: dict[str, Path] = {}
        source = self.source_root
        skills = source / "skills"
        if skills.is_dir():
            for child in sorted(skills.iterdir()):
                if child.name in IGNORE_NAMES or child.name.startswith("."):
                    continue
                relative = f"skills/{child.name}"
                if is_allowed(relative, self.provider.id):
                    entries[relative] = child
        candidate = source / "agents"
        if candidate.exists() and is_allowed("agents", self.provider.id):
            entries["agents"] = candidate
        host = source / "hosts" / self.provider.id
        relative_host = f"hosts/{self.provider.id}"
        if host.exists() and is_allowed(relative_host, self.provider.id):
            entries[relative_host] = host
        return entries

    def generated_entries(self) -> dict[str, str]:
        """Destination-relative path -> text the adapter renders itself.

        Native adapters use this for host-shaped files (the reviewer agent)
        that cannot be a plain copy of one source file.
        """
        return {}

    def registration_extra(self) -> dict:
        """Extra marker fields an adapter needs for verify/remove."""
        return {}

    def _matches(self, destination: Path, source: Path) -> bool:
        if self.mode == "symlink":
            if not destination.is_symlink():
                return False
            try:
                return destination.resolve() == source.resolve()
            except OSError:
                return False
        return _same_tree(destination, source)

    def _install_entry(self, destination: Path, source: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if self.mode == "symlink":
            os.symlink(source, destination, target_is_directory=source.is_dir())
            return
        if source.is_dir():
            shutil.copytree(source, destination, ignore=_ignore, symlinks=False)
        else:
            shutil.copy2(source, destination)

    def _write_text(self, destination: Path, text: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")

    def _text_matches(self, destination: Path, text: str) -> bool:
        if destination.is_symlink() or not destination.is_file():
            return False
        try:
            return destination.read_text(encoding="utf-8") == text
        except OSError:
            return False

    def _remove_entry(self, destination: Path) -> None:
        relative = destination.relative_to(self.root)
        if not relative.parts:
            raise ValueError("refusing to remove the install root")
        if destination.is_symlink() or destination.is_file():
            destination.unlink()
        elif destination.is_dir():
            shutil.rmtree(destination)

    def _read_marker(self) -> dict | None:
        if not self.marker.is_file() or self.marker.is_symlink():
            return None
        try:
            marker = json.loads(self.marker.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if marker.get("schema") != SCHEMA_VERSION:
            return None
        entries = marker.get("entries")
        if not isinstance(entries, list) or not all(isinstance(entry, str) for entry in entries):
            return None
        marker["entries"] = sorted(set(entries))
        return marker

    def _write_marker(self, entries: tuple[str, ...]) -> None:
        payload = {
            "schema": SCHEMA_VERSION,
            "provider": self.provider.id,
            "scope": self.scope,
            "mode": self.mode,
            "source": str(self.source_root),
            "entries": sorted(set(entries)),
            **self.registration_extra(),
        }
        temporary = self.marker.with_name(self.marker.name + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.marker)

    def _prune_empty(self, directory: Path) -> None:
        current = directory
        while True:
            if current == self.root.parent:
                return
            try:
                current.rmdir()
            except OSError:
                return
            if current == self.root:
                return
            current = current.parent
