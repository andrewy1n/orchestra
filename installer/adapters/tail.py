"""Install a provider through its configured skills CLI profile."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from installer.adapters.base import BaseAdapter
from installer.model import (
    Action,
    ApplyResult,
    Plan,
    Provider,
    RemoveResult,
    VerifyResult,
)

NPX_ENV = "ORCHESTRA_NPX"


class SkillsCliAdapter(BaseAdapter):
    """Delegate one host to ``npx skills add -a <profile>``."""

    def __init__(
        self,
        provider: Provider,
        *,
        base: Path,
        scope: str,
        mode: str,
        source_root: Path,
    ) -> None:
        super().__init__(provider, base=base, scope=scope, mode=mode, source_root=source_root)
        if not provider.profile:
            raise ValueError(f"provider {provider.id!r} needs a skills profile to delegate")
        self.profile = provider.profile

    # -- delegation -----------------------------------------------------

    def command(self) -> tuple[str, ...]:
        executable = os.environ.get(NPX_ENV, "npx")
        return (executable, "skills", "add", "-a", self.profile)

    def delegate_label(self) -> str:
        return f"npx skills add -a {self.profile} (profile: {self.profile})"

    def registration_extra(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "delegate": f"npx skills add -a {self.profile}",
        }

    def plan(self, *, uninstall: bool = False) -> Plan:
        if uninstall:
            return super().plan(uninstall=uninstall)
        return Plan(
            provider=self.provider,
            scope=self.scope,
            mode=self.mode,
            root=self.root,
            actions=(
                Action(kind="delegate", destination=self.root),
                Action(kind="register", destination=self.marker),
            ),
            entries=(),
            note=f"delegate {self.delegate_label()}",
        )

    def apply(self, plan: Plan) -> ApplyResult:
        self.base.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            self.command(), cwd=self.base, capture_output=True, text=True, check=False
        )
        if completed.returncode != 0:
            raise ValueError(
                f"{self.delegate_label()} exited {completed.returncode}: {completed.stderr.strip()}"
            )
        self.root.mkdir(parents=True, exist_ok=True)
        self._write_marker(())
        return ApplyResult(
            provider=self.provider,
            root=self.root,
            note=f"delegated to {self.delegate_label()}",
        )

    def verify(self) -> VerifyResult:
        marker = self.read_marker()
        if marker is None:
            return VerifyResult(
                provider=self.provider,
                root=self.root,
                ok=False,
                problems=("registration missing",),
            )
        problems: list[str] = []
        if marker["provider"] != self.provider.id:
            problems.append(
                f"registration names {marker['provider']!r}, expected {self.provider.id!r}"
            )
        if marker["scope"] != self.scope:
            problems.append(f"registration scope is {marker['scope']!r}, expected {self.scope!r}")
        if marker["mode"] != self.mode:
            problems.append(f"registration mode is {marker['mode']!r}, expected {self.mode!r}")
        if marker.get("profile") != self.profile:
            problems.append(
                f"registration profile is {marker.get('profile')!r}, expected {self.profile!r}"
            )
        for entry in self._marker_entries(marker):
            destination = self.root / entry
            if not (destination.exists() or destination.is_symlink()):
                problems.append(f"missing {entry}")
        return VerifyResult(
            provider=self.provider,
            root=self.root,
            ok=not problems,
            problems=tuple(problems),
        )

    def remove(self) -> RemoveResult:
        marker = self.read_marker()
        result = super().remove()
        if result.skipped or marker is None:
            return result
        return RemoveResult(
            provider=result.provider,
            root=result.root,
            removed=result.removed,
            skipped=result.skipped,
            note=f"profile {self.profile} stays managed by npx skills",
        )
