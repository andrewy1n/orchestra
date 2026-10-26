"""Native adapters for Claude Code, Cursor, and OpenCode.

A native host gets the same portable skill payload as the
generic adapter, plus two host-shaped additions:

* files under ``hosts/<provider>/`` are merged at the install root instead of
  being copied as a nested ``hosts/<provider>`` directory. Claude gets its
  hooks merged into ``settings.json`` (plus a legacy ``hooks/hooks.json``
  copy), Cursor gets ``hooks.json``, and OpenCode gets ``plugins/plugin.js``
  and its ``opencode.json`` skills source.
* the reviewer agent is generated from ``agents/reviewer.prompt.md`` with
  frontmatter the host understands.

Hooks are optional by design: a host payload may omit them (or the entire
``hosts/<provider>/`` directory) and installation still succeeds. The skills
call ``orchestra hook-start`` themselves when no hook exists.
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

from installer.adapters import register_adapter
from installer.adapters.base import BaseAdapter
from installer.agents import generated_agent
from installer.allowlist import IGNORE_NAMES, IGNORE_SUFFIXES, is_allowed
from installer.model import Action, ApplyResult, Plan, RemoveResult, VerifyResult


class NativeAdapter(BaseAdapter):
    """Skills, host files merged at the root, generated agent."""

    def desired_entries(self) -> dict[str, Path]:
        entries = super().desired_entries()
        # Native hosts get one generated agent file, not the authored
        # ``agents/`` tree (which carries the Claude-shaped canonical copy).
        entries.pop("agents", None)
        entries.pop(f"hosts/{self.provider.id}", None)

        payload = self.source_root / "hosts" / self.provider.id
        if payload.is_dir():
            for child in sorted(payload.rglob("*")):
                if not child.is_file():
                    continue
                if child.name in IGNORE_NAMES or child.name.endswith(IGNORE_SUFFIXES):
                    continue
                relative = child.relative_to(payload).as_posix()
                if is_allowed(
                    f"hosts/{self.provider.id}/{relative}", self.provider.id
                ):
                    entries[relative] = child

        for entry in self.generated_entries():
            entries.pop(entry, None)
        return entries

    def generated_entries(self) -> dict[str, str]:
        generated = generated_agent(self.source_root, self.provider.id)
        if generated is None:
            return {}
        destination, text = generated
        return {destination: text}


@register_adapter("claude")
class ClaudeAdapter(NativeAdapter):
    """Claude Code: ``.claude/{skills,agents,hooks,settings.json}``.

    Claude reads session hooks from ``settings.json`` under its root, not from
    ``hooks/hooks.json``. The source payload at
    ``hosts/claude/hooks/hooks.json`` is shaped like a settings fragment, so
    the adapter merges its ``hooks`` map into an existing settings file instead
    of replacing user configuration. Uninstall removes only the groups this
    installer added. The legacy ``hooks/hooks.json`` copy stays in the payload
    for older installs; ``settings.json`` is the file Claude actually reads.
    """

    def _fragment(self) -> dict:
        """The hooks fragment the source payload declares, if any."""
        source = self.source_root / "hosts" / "claude" / "hooks" / "hooks.json"
        if not source.is_file():
            return {}
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload.get("hooks"), dict):
            raise ValueError(f"{source} does not declare a hooks map")
        return payload

    def _settings_path(self) -> Path:
        return self.root / "settings.json"

    def _read_settings(self) -> dict:
        path = self._settings_path()
        if path.is_symlink() and not path.exists():
            raise ValueError(f"{path} is a broken symlink")
        if not path.exists():
            return {}
        if not path.is_file():
            raise ValueError(f"{path} is not a regular settings file")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} is not valid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object")
        return payload

    def _write_settings(self, payload: dict) -> None:
        path = self._settings_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _groups(fragment: dict) -> list[tuple[str, list]]:
        return [
            (event, groups)
            for event, groups in fragment.get("hooks", {}).items()
            if isinstance(groups, list)
        ]

    def _settings_have_fragment(self, settings: dict, fragment: dict) -> bool:
        hooks = settings.get("hooks")
        if not isinstance(hooks, dict):
            return False
        for event, groups in self._groups(fragment):
            existing = hooks.get(event)
            if not isinstance(existing, list):
                return False
            if any(group not in existing for group in groups):
                return False
        return True

    def _merge_settings(self, settings: dict, fragment: dict) -> dict:
        merged = copy.deepcopy(settings)
        hooks = merged.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise ValueError("settings.json has a non-object hooks value")
        for event, groups in self._groups(fragment):
            existing = hooks.setdefault(event, [])
            if not isinstance(existing, list):
                raise ValueError(f"settings.json hooks.{event} is not a list")
            for group in groups:
                if group not in existing:
                    existing.append(copy.deepcopy(group))
        return merged

    def _unmerge_settings(self, settings: dict, fragment: dict) -> dict:
        merged = copy.deepcopy(settings)
        hooks = merged.get("hooks")
        if not isinstance(hooks, dict):
            return merged
        for event, groups in self._groups(fragment):
            existing = hooks.get(event)
            if not isinstance(existing, list):
                continue
            remainder = [group for group in existing if group not in groups]
            if remainder:
                hooks[event] = remainder
            else:
                hooks.pop(event, None)
        if not hooks:
            merged.pop("hooks", None)
        return merged

    def plan(self, *, uninstall: bool = False) -> Plan:
        plan = super().plan(uninstall=uninstall)
        fragment = self._fragment()
        if uninstall or not fragment:
            return plan
        actions = list(plan.actions)
        register = actions.pop()  # the register action is always last
        actions.append(
            Action(
                kind="merge",
                destination=self._settings_path(),
                unchanged=self._settings_have_fragment(
                    self._read_settings(), fragment
                ),
                content=json.dumps(fragment),
            )
        )
        actions.append(register)
        return replace(plan, actions=tuple(actions))

    def apply(self, plan: Plan) -> ApplyResult:
        merges = [action for action in plan.actions if action.kind == "merge"]
        rest = replace(
            plan,
            actions=tuple(
                action for action in plan.actions if action.kind != "merge"
            ),
        )
        result = super().apply(rest)
        applied = list(result.applied)
        unchanged = list(result.unchanged)
        fragment = self._fragment()
        if merges and fragment:
            settings = self._read_settings()
            if self._settings_have_fragment(settings, fragment):
                unchanged.append("settings.json")
            else:
                self._write_settings(self._merge_settings(settings, fragment))
                applied.append("settings.json")
        return ApplyResult(
            provider=result.provider,
            root=result.root,
            applied=tuple(applied),
            unchanged=tuple(unchanged),
            removed=result.removed,
            note=result.note,
        )

    def verify(self) -> VerifyResult:
        result = super().verify()
        fragment = self._fragment()
        problems = list(result.problems)
        if fragment and not self._settings_have_fragment(
            self._read_settings(), fragment
        ):
            problems.append("hooks missing from settings.json")
        return VerifyResult(
            provider=result.provider,
            root=result.root,
            ok=not problems,
            problems=tuple(problems),
        )

    def remove(self) -> RemoveResult:
        marker = self._read_marker()
        touched_settings = False
        if marker is not None:
            fragment = marker.get("settings_hooks") or {}
            if fragment and self._settings_path().exists():
                settings = self._read_settings()
                remainder = self._unmerge_settings(settings, fragment)
                if remainder:
                    self._write_settings(remainder)
                elif self._settings_path().is_symlink():
                    # The link is user-owned; keep it and clear the installed
                    # fragment through the link instead of deleting the link.
                    self._write_settings({})
                else:
                    self._settings_path().unlink()
                touched_settings = True
        result = super().remove()
        if not touched_settings:
            return result
        return RemoveResult(
            provider=result.provider,
            root=result.root,
            removed=(*result.removed, "settings.json"),
            skipped=result.skipped,
            note=result.note,
        )

    def registration_extra(self) -> dict:
        fragment = self._fragment()
        return {"settings_hooks": fragment} if fragment else {}


@register_adapter("cursor")
class CursorAdapter(NativeAdapter):
    """Cursor: ``.cursor/{skills,agents,hooks.json}`` project or user root."""


@register_adapter("opencode")
class OpenCodeAdapter(NativeAdapter):
    """OpenCode: ``skills`` source, ``agents/``, and ``plugins/`` hooks.

    OpenCode auto-loads plugins from ``plugins/<file>`` under its project or
    global config root; a root-level ``plugin.js`` is not discovered. The
    source payload keeps its flat shape and the adapter moves it into
    ``plugins/`` at the destination.
    """

    def desired_entries(self) -> dict[str, Path]:
        entries = super().desired_entries()
        plugin = entries.pop("plugin.js", None)
        if plugin is not None:
            entries["plugins/plugin.js"] = plugin
        return entries
