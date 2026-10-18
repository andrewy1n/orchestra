"""Selection, rendering, and execution for ``orchestra install``."""

from __future__ import annotations

import sys
from pathlib import Path

from installer.adapters import build_adapter
from installer.matrix import MatrixError, load_matrix
from installer.model import InstallReport, InstallRequest, Plan, Provider
from installer.paths import source_root as default_source_root


class InstallError(ValueError):
    """A request the installer refuses before touching the filesystem."""


def select_providers(
    providers: tuple[Provider, ...], request: InstallRequest
) -> tuple[Provider, ...]:
    """Resolve ``--only``/``--all`` to matrix rows, preserving request order."""
    if request.only and request.all_providers:
        raise InstallError("--only and --all are mutually exclusive")
    if not request.only:
        return providers
    by_id = {provider.id: provider for provider in providers}
    unknown = [name for name in request.only if name not in by_id]
    if unknown:
        raise InstallError(
            f"unknown provider(s): {', '.join(unknown)}; "
            f"choose from {', '.join(by_id)}"
        )
    selected: list[Provider] = []
    for name in request.only:
        provider = by_id[name]
        if provider not in selected:
            selected.append(provider)
    return tuple(selected)


def install_base(request: InstallRequest) -> Path:
    """Directory the provider roots hang off.

    ``--home`` wins over both scopes so tests can redirect the whole install.
    Without it, ``--global`` uses the user home and the default is the cwd.
    """
    if request.home is not None:
        return Path(request.home).expanduser()
    if request.global_scope:
        return Path.home()
    return Path(request.cwd or Path.cwd())


def render_plan(plan: Plan, *, dry_run: bool) -> None:
    verb = "uninstall" if plan.uninstall else "install"
    header = (
        f"{verb} {plan.provider.id} [{plan.mode}/{plan.scope}] -> {plan.root}"
    )
    if plan.note:
        header = f"{header} ({plan.note})"
    print(header)
    for action in plan.actions:
        print(f"  {action.render()}")
    if dry_run:
        print("  (dry run; nothing written)")


def _print_apply(result) -> None:
    print(f"installed {result.provider.id} -> {result.root}")
    if result.applied:
        print(f"  applied: {', '.join(result.applied)}")
    if result.unchanged:
        print(f"  unchanged: {', '.join(result.unchanged)}")
    if result.removed:
        print(f"  removed: {', '.join(result.removed)}")
    if result.note:
        print(f"  {result.note}")


def _print_remove(result) -> None:
    if result.skipped:
        print(f"not installed: {result.provider.id} -> {result.root}")
        return
    print(f"uninstalled {result.provider.id} -> {result.root}")
    if result.removed:
        print(f"  removed: {', '.join(result.removed)}")
    if result.note:
        print(f"  {result.note}")


def run(request: InstallRequest) -> int:
    """Execute one installer request; return a process exit code."""
    try:
        providers = load_matrix()
        selected = select_providers(providers, request)
    except (MatrixError, InstallError) as exc:
        print(f"orchestra install: {exc}", file=sys.stderr)
        return 2

    source = request.source_root or default_source_root()
    if not (source / "skills").is_dir():
        print(
            f"orchestra install: no skills/ under source root {source}",
            file=sys.stderr,
        )
        return 2

    base = install_base(request)
    scope = "global" if request.global_scope else "project"
    mode = "copy" if request.copy else "symlink"
    report = InstallReport()

    for provider in selected:
        adapter = build_adapter(
            provider,
            base=base,
            scope=scope,
            mode=mode,
            source_root=source,
        )
        plan = adapter.plan(uninstall=request.uninstall)
        report.plans.append(plan)
        if request.dry_run:
            render_plan(plan, dry_run=True)
            continue
        if request.uninstall:
            removed = adapter.remove()
            report.removed.append(removed)
            _print_remove(removed)
            continue
        applied = adapter.apply(plan)
        report.applied.append(applied)
        _print_apply(applied)
        verified = adapter.verify()
        report.verified.append(verified)
        if verified.ok:
            print("  verified: ok")
        else:
            print(f"  verified: FAILED ({'; '.join(verified.problems)})")

    if request.dry_run:
        print(f"planned {len(report.plans)} provider(s) at {base}")
    return 0 if report.ok else 1
