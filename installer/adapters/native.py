"""Native adapters for Claude Code, Cursor, and OpenCode.

A native host gets the same portable skill payload as the
generic adapter, plus two host-shaped additions:

* files under ``hosts/<provider>/`` are merged at the install root instead of
  being copied as a nested ``hosts/<provider>`` directory. Claude gets its
  hooks merged into ``settings.json`` (plus a legacy ``hooks/hooks.json``
  copy), Cursor gets hook commands merged into ``hooks.json``, and OpenCode
  gets ``plugins/plugin.js`` and its ``opencode.json`` skills source.
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
                if is_allowed(f"hosts/{self.provider.id}/{relative}", self.provider.id):
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
                unchanged=self._settings_have_fragment(self._read_settings(), fragment),
                content=json.dumps(fragment),
            )
        )
        actions.append(register)
        return replace(plan, actions=tuple(actions))

    def apply(self, plan: Plan) -> ApplyResult:
        merges = [action for action in plan.actions if action.kind == "merge"]
        rest = replace(
            plan,
            actions=tuple(action for action in plan.actions if action.kind != "merge"),
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
        if fragment and not self._settings_have_fragment(self._read_settings(), fragment):
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
    """Cursor: ``.cursor/{skills,agents,hooks.json}`` project or user root.

    Cursor reads session hooks from ``hooks.json``. The source payload at
    ``hosts/cursor/hooks.json`` contributes ``{command}`` entries, merged by
    exact command string into the existing file. A symlinked ``hooks.json``
    is replaced by a regular file holding the merged hooks; the symlink
    target is not written. The registration records each ``(event, command)``
    pair this installer added under ``hooks``. Uninstall removes only those
    pairs.
    """

    def desired_entries(self) -> dict[str, Path]:
        entries = super().desired_entries()
        entries.pop("hooks.json", None)
        return entries

    def _source_path(self) -> Path:
        return self.source_root / "hosts" / "cursor" / "hooks.json"

    def _hooks_path(self) -> Path:
        return self.root / "hooks.json"

    def _fragment(self) -> dict[str, object]:
        """Payload document, or ``{}`` when this host ships no hooks file."""
        source = self._source_path()
        if not source.is_file():
            return {}
        payload = self._load_object(source)
        if not isinstance(payload.get("hooks"), dict):
            raise ValueError(f"{source} does not declare a hooks map")
        return payload

    def _load_object(self, path: Path) -> dict[str, object]:
        if path.is_symlink() and not path.exists():
            raise ValueError(f"{path} is a broken symlink")
        if not path.is_file():
            raise ValueError(f"{path} is not a regular hooks file")
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} is not valid JSON: {exc}") from exc
        return self._as_object(loaded, path)

    def _read_hooks(self) -> dict[str, object]:
        path = self._hooks_path()
        if path.is_symlink() and not path.exists():
            raise ValueError(f"{path} is a broken symlink")
        if not path.exists():
            return {}
        return self._load_object(path)

    def _write_hooks(self, payload: dict[str, object]) -> bool:
        path = self._hooks_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        replaced_symlink = self._unlink_if_symlink(path)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return replaced_symlink

    @staticmethod
    def _unlink_if_symlink(path: Path) -> bool:
        if not path.is_symlink():
            return False
        path.unlink()
        return True

    @staticmethod
    def _symlink_replacement_note(note: str) -> str:
        message = "hooks.json was a symlink and is now a regular file"
        if not note:
            return message
        return f"{note}; {message}"

    def _discard_hooks_file(self) -> None:
        path = self._hooks_path()
        if path.is_symlink() or path.is_file():
            path.unlink()

    @staticmethod
    def _as_object(loaded: object, label: Path | str) -> dict[str, object]:
        if not isinstance(loaded, dict):
            raise ValueError(f"{label} must contain a JSON object")
        document: dict[str, object] = {}
        for key, value in loaded.items():
            if not isinstance(key, str):
                raise ValueError(f"{label} must contain a JSON object")
            document[key] = value
        return document

    @staticmethod
    def _command_of(entry: object) -> str | None:
        if not isinstance(entry, dict):
            return None
        command = entry.get("command")
        if isinstance(command, str):
            return command
        return None

    def _payload_entries(
        self, payload: dict[str, object]
    ) -> list[tuple[str, list[dict[str, object]]]]:
        hooks = payload.get("hooks")
        if not isinstance(hooks, dict):
            return []
        grouped: list[tuple[str, list[dict[str, object]]]] = []
        for event, entries in hooks.items():
            if not isinstance(event, str):
                continue
            if not isinstance(entries, list):
                raise ValueError(f"{self._source_path()} hooks.{event} is not a list")
            commands: list[dict[str, object]] = []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                normalized: dict[str, object] = {}
                for key, value in entry.items():
                    if isinstance(key, str):
                        normalized[key] = value
                if isinstance(normalized.get("command"), str):
                    commands.append(normalized)
            if commands:
                grouped.append((event, commands))
        return grouped

    def _commands_in(self, entries: object) -> set[str]:
        if not isinstance(entries, list):
            return set()
        commands: set[str] = set()
        for entry in entries:
            command = self._command_of(entry)
            if command is not None:
                commands.add(command)
        return commands

    def _missing_pairs(
        self, document: dict[str, object], payload: dict[str, object]
    ) -> list[tuple[str, str]]:
        hooks = document.get("hooks")
        hooks_map = hooks if isinstance(hooks, dict) else {}
        missing: list[tuple[str, str]] = []
        for event, entries in self._payload_entries(payload):
            present = self._commands_in(hooks_map.get(event))
            for entry in entries:
                command = entry.get("command")
                if isinstance(command, str) and command not in present:
                    missing.append((event, command))
                    present.add(command)
        return missing

    def _previous_marker(self) -> dict[str, object] | None:
        marker = self._read_marker()
        if not isinstance(marker, dict):
            return None
        fields: dict[str, object] = {}
        for key, value in marker.items():
            if isinstance(key, str):
                fields[key] = value
        return fields

    def _pairs_in(self, marker: dict[str, object]) -> list[tuple[str, str]]:
        raw = marker.get("hooks")
        if not isinstance(raw, list):
            return []
        pairs: list[tuple[str, str]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            event = item.get("event")
            command = item.get("command")
            if isinstance(event, str) and isinstance(command, str):
                pairs.append((event, command))
        return pairs

    @staticmethod
    def _union_pairs(
        previous: list[tuple[str, str]], missing: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        combined = list(previous)
        seen = set(previous)
        for pair in missing:
            if pair not in seen:
                combined.append(pair)
                seen.add(pair)
        return combined

    def _pairs_to_record(self, payload: dict[str, object]) -> list[tuple[str, str]]:
        marker = self._previous_marker()
        previous = self._pairs_in(marker) if marker is not None else []
        return self._union_pairs(previous, self._missing_pairs(self._read_hooks(), payload))

    def _created_hooks_file(self) -> bool:
        marker = self._previous_marker()
        if marker is not None and marker.get("hooks_created") is True:
            return True
        path = self._hooks_path()
        return not path.exists() and not path.is_symlink()

    def _hooks_have_payload(self, document: dict[str, object], payload: dict[str, object]) -> bool:
        if "version" in payload and "version" not in document:
            return False
        hooks = document.get("hooks")
        if not isinstance(hooks, dict):
            return False
        return not self._missing_pairs(document, payload)

    def _merge_hooks(
        self, document: dict[str, object], payload: dict[str, object]
    ) -> dict[str, object]:
        merged: dict[str, object] = copy.deepcopy(document)
        if "version" not in merged and "version" in payload:
            merged = {"version": payload["version"], **merged}
        hooks_value = merged.get("hooks")
        if hooks_value is None:
            hooks: dict[str, object] = {}
            merged["hooks"] = hooks
        elif isinstance(hooks_value, dict):
            hooks = hooks_value
        else:
            raise ValueError("hooks.json has a non-object hooks value")
        for event, entries in self._payload_entries(payload):
            existing = hooks.get(event)
            if existing is None:
                bucket: list[object] = []
                hooks[event] = bucket
            elif isinstance(existing, list):
                bucket = existing
            else:
                raise ValueError(f"hooks.json hooks.{event} is not a list")
            present = self._commands_in(bucket)
            for entry in entries:
                command = entry.get("command")
                if not isinstance(command, str) or command in present:
                    continue
                bucket.append(copy.deepcopy(entry))
                present.add(command)
        return merged

    def _unmerge_hooks(
        self, document: dict[str, object], pairs: list[tuple[str, str]]
    ) -> dict[str, object]:
        merged: dict[str, object] = copy.deepcopy(document)
        if not pairs:
            return merged
        hooks_value = merged.get("hooks")
        if not isinstance(hooks_value, dict):
            return merged
        grouped: dict[str, set[str]] = {}
        for event, command in pairs:
            grouped.setdefault(event, set()).add(command)
        for event, commands in grouped.items():
            existing = hooks_value.get(event)
            if not isinstance(existing, list):
                continue
            kept: list[object] = []
            for entry in existing:
                command = self._command_of(entry)
                if command is not None and command in commands:
                    continue
                kept.append(entry)
            if kept:
                hooks_value[event] = kept
            else:
                hooks_value.pop(event, None)
        if not hooks_value:
            merged.pop("hooks", None)
        return merged

    def _hook_entries_remain(self, document: dict[str, object]) -> bool:
        hooks = document.get("hooks")
        if not isinstance(hooks, dict):
            return False
        return any(isinstance(entries, list) and len(entries) > 0 for entries in hooks.values())

    def _removable_shell(self, document: dict[str, object], payload: dict[str, object]) -> bool:
        if self._hook_entries_remain(document):
            return False
        for key in document:
            if key not in {"version", "hooks"}:
                return False
        if "version" in document and document.get("version") != payload.get("version"):
            return False
        hooks = document.get("hooks")
        return hooks is None or hooks == {}

    def _restore_hooks(self, marker: dict[str, object]) -> bool:
        path = self._hooks_path()
        if not path.exists() and not path.is_symlink():
            return False
        payload = self._fragment()
        document = self._read_hooks()
        remainder = self._unmerge_hooks(document, self._pairs_in(marker))
        created = marker.get("hooks_created") is True
        if created and self._removable_shell(remainder, payload):
            self._discard_hooks_file()
            return True
        if remainder == document:
            return False
        if remainder:
            self._write_hooks(remainder)
        else:
            self._discard_hooks_file()
        return True

    def plan(self, *, uninstall: bool = False) -> Plan:
        plan = super().plan(uninstall=uninstall)
        fragment = self._fragment()
        if uninstall or not fragment:
            return plan
        actions = list(plan.actions)
        register = actions.pop()
        actions.append(
            Action(
                kind="merge",
                destination=self._hooks_path(),
                unchanged=self._hooks_have_payload(self._read_hooks(), fragment),
                content=json.dumps(fragment),
            )
        )
        actions.append(register)
        return replace(plan, actions=tuple(actions))

    def apply(self, plan: Plan) -> ApplyResult:
        merges = [action for action in plan.actions if action.kind == "merge"]
        rest = replace(
            plan,
            actions=tuple(action for action in plan.actions if action.kind != "merge"),
        )
        result = super().apply(rest)
        applied = list(result.applied)
        unchanged = list(result.unchanged)
        note = result.note
        fragment = self._fragment()
        if merges and fragment:
            linked = self._hooks_path().is_symlink()
            document = self._read_hooks()
            if self._hooks_have_payload(document, fragment) and not linked:
                unchanged.append("hooks.json")
            else:
                replaced_symlink = self._write_hooks(self._merge_hooks(document, fragment))
                applied.append("hooks.json")
                if replaced_symlink:
                    note = self._symlink_replacement_note(note)
        return ApplyResult(
            provider=result.provider,
            root=result.root,
            applied=tuple(applied),
            unchanged=tuple(unchanged),
            removed=result.removed,
            note=note,
        )

    def verify(self) -> VerifyResult:
        result = super().verify()
        fragment = self._fragment()
        problems = list(result.problems)
        if fragment and not self._hooks_have_payload(self._read_hooks(), fragment):
            problems.append("hooks missing from hooks.json")
        return VerifyResult(
            provider=result.provider,
            root=result.root,
            ok=not problems,
            problems=tuple(problems),
        )

    def remove(self) -> RemoveResult:
        marker = self._previous_marker()
        touched = False
        if marker is not None:
            touched = self._restore_hooks(marker)
        result = super().remove()
        if not touched:
            return result
        return RemoveResult(
            provider=result.provider,
            root=result.root,
            removed=(*result.removed, "hooks.json"),
            skipped=result.skipped,
            note=result.note,
        )

    def registration_extra(self) -> dict[str, object]:
        fragment = self._fragment()
        if not fragment:
            return {}
        extra: dict[str, object] = {}
        pairs = self._pairs_to_record(fragment)
        if pairs:
            extra["hooks"] = [{"event": event, "command": command} for event, command in pairs]
        if self._created_hooks_file():
            extra["hooks_created"] = True
        return extra


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
