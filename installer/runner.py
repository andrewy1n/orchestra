"""Selection, rendering, and execution for ``orchestra install``."""

from __future__ import annotations

import sys
from pathlib import Path

from installer.adapters import build_adapter
from installer.detect import HostStatus, detect_hosts, detected_ids
from installer.matrix import MatrixError, load_matrix
from installer.model import InstallReport, InstallRequest, Plan, Provider
from installer.paths import source_root as default_source_root
from installer.wizard import (
    WizardCancelled,
    WizardSelectionError,
    confirm,
    prompt_hosts,
    prompt_mode,
    prompt_scope,
    wants_wizard,
)


class InstallError(ValueError):
    """A request the installer refuses before touching the filesystem."""


def select_providers(
    providers: tuple[Provider, ...], request: InstallRequest
) -> tuple[Provider, ...]:
    """Resolve explicit ``--only``/``--all`` to matrix rows.

    ``--only`` preserves request order. With neither flag, the caller decides
    from detection or the wizard, so this returns an empty tuple.
    """
    if request.only and request.all_providers:
        raise InstallError("--only and --all are mutually exclusive")
    if request.all_providers:
        return providers
    if not request.only:
        return ()
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


def install_bases(request: InstallRequest) -> tuple[Path, Path]:
    """Project and global bases before scope selection.

    ``--home`` replaces both bases so tests and throwaway homes never read the
    real HOME. Without it, the project base is the requested cwd and the global
    base is the user home.
    """
    if request.home is not None:
        redirect = Path(request.home).expanduser()
        return redirect, redirect
    return Path(request.cwd or Path.cwd()), Path.home()


def install_base(request: InstallRequest, scope: str = "project") -> Path:
    """Directory the provider roots hang off for one scope."""
    project_base, global_base = install_bases(request)
    return global_base if scope == "global" else project_base


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


def render_host_list(statuses: tuple[HostStatus, ...]) -> None:
    """Print the provider matrix with project and global detection."""
    print(
        f"{'ID':<10} {'HOST':<18} {'KIND':<8} {'PROJECT':<8} "
        f"{'GLOBAL':<7} {'PROJECT ROOT':<18} GLOBAL ROOT"
    )
    for status in statuses:
        project = "yes" if status.project else "no"
        global_ = "yes" if status.global_ else "no"
        print(
            f"{status.provider.id:<10} {status.provider.name:<18} "
            f"{status.provider.kind:<8} {project:<8} {global_:<7} "
            f"{status.provider.project_root:<18} {status.provider.global_root}"
        )


def _providers_for_ids(
    providers: tuple[Provider, ...], ids: tuple[str, ...]
) -> tuple[Provider, ...]:
    by_id = {provider.id: provider for provider in providers}
    return tuple(by_id[provider_id] for provider_id in ids)


def _no_detection_guidance(project_base: Path, global_base: Path) -> None:
    print(
        "orchestra install: no host footprints detected in "
        f"{project_base} or {global_base}; use --all, --only HOST, "
        "or --interactive",
        file=sys.stderr,
    )


def _cancelled() -> int:
    print("orchestra install: cancelled; nothing written", file=sys.stderr)
    return 0


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
    except MatrixError as exc:
        print(f"orchestra install: {exc}", file=sys.stderr)
        return 2

    source = request.source_root or default_source_root()
    project_base, global_base = install_bases(request)

    if request.list_only:
        statuses = detect_hosts(providers, project_base, global_base, source)
        render_host_list(statuses)
        return 0

    try:
        explicit = select_providers(providers, request)
    except InstallError as exc:
        print(f"orchestra install: {exc}", file=sys.stderr)
        return 2

    if not (source / "skills").is_dir():
        print(
            f"orchestra install: no skills/ under source root {source}",
            file=sys.stderr,
        )
        return 2

    wizard = wants_wizard(request)
    needs_detection = not request.uninstall and (
        wizard or not (request.only or request.all_providers)
    )
    statuses = (
        detect_hosts(providers, project_base, global_base, source)
        if needs_detection
        else ()
    )

    if request.only or request.all_providers:
        selected = explicit
    elif request.uninstall:
        selected = providers
    elif wizard:
        try:
            selected_ids = prompt_hosts(statuses, detected_ids(statuses))
        except WizardCancelled:
            return _cancelled()
        except WizardSelectionError as exc:
            print(f"orchestra install: {exc}", file=sys.stderr)
            return 2
        selected = _providers_for_ids(providers, selected_ids)
    else:
        selected_ids = detected_ids(statuses)
        if not selected_ids:
            _no_detection_guidance(project_base, global_base)
            return 2
        selected = _providers_for_ids(providers, selected_ids)

    if request.scope is not None:
        scope = request.scope
    elif wizard:
        try:
            scope = prompt_scope(
                default="project",
                project_base=project_base,
                global_base=global_base,
            )
        except WizardCancelled:
            return _cancelled()
    else:
        scope = "project"

    if request.copy:
        mode = "copy"
    elif wizard:
        try:
            mode = prompt_mode(default="symlink")
        except WizardCancelled:
            return _cancelled()
    else:
        mode = "symlink"

    base = global_base if scope == "global" else project_base
    report = InstallReport()
    pairs = []
    for provider in selected:
        adapter = build_adapter(
            provider,
            base=base,
            scope=scope,
            mode=mode,
            source_root=source,
        )
        plan = adapter.plan(uninstall=request.uninstall)
        pairs.append((adapter, plan))
        report.plans.append(plan)

    if request.dry_run or wizard:
        for plan in report.plans:
            render_plan(plan, dry_run=request.dry_run)

    if wizard and not request.dry_run:
        try:
            proceed = confirm("Proceed?", default=True)
        except WizardCancelled:
            return _cancelled()
        if not proceed:
            return _cancelled()

    for adapter, plan in pairs:
        if request.dry_run:
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
