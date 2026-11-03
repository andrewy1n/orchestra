"""Read-only host footprint detection for the installer wizard."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from installer.adapters import build_adapter
from installer.model import Provider


@dataclass(frozen=True)
class HostStatus:
    """One provider's footprint at the project and global install bases."""

    provider: Provider
    project: bool
    global_: bool
    marker_project: bool
    marker_global: bool


def detect_hosts(
    providers: tuple[Provider, ...],
    project_base: Path,
    global_base: Path,
    source_root: Path,
) -> tuple[HostStatus, ...]:
    """Return one status per provider, in matrix order.

    Detection is read-only. A host is present at a scope when its registration
    marker exists or any matrix ``detect`` path exists under that base.
    """
    project_base = Path(project_base)
    global_base = Path(global_base)
    source_root = Path(source_root)
    statuses: list[HostStatus] = []
    for provider in providers:
        project_adapter = build_adapter(
            provider,
            base=project_base,
            scope="project",
            mode="symlink",
            source_root=source_root,
        )
        global_adapter = build_adapter(
            provider,
            base=global_base,
            scope="global",
            mode="symlink",
            source_root=source_root,
        )
        statuses.append(
            HostStatus(
                provider=provider,
                project=project_adapter.detect(),
                global_=global_adapter.detect(),
                marker_project=project_adapter.marker.is_file(),
                marker_global=global_adapter.marker.is_file(),
            )
        )
    return tuple(statuses)


def detected_ids(statuses: tuple[HostStatus, ...]) -> tuple[str, ...]:
    """Provider ids detected at either scope, in matrix order."""
    return tuple(status.provider.id for status in statuses if status.project or status.global_)


def installed_ids(statuses: tuple[HostStatus, ...]) -> tuple[str, ...]:
    """Provider ids with an orchestra registration at either scope."""
    return tuple(
        status.provider.id for status in statuses if status.marker_project or status.marker_global
    )
