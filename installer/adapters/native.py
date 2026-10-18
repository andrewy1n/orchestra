"""Native adapters for Claude Code, Cursor, and OpenCode.

A native host gets the same portable skill and contract payload as the
generic adapter, plus two host-shaped additions:

* files under ``hosts/<provider>/`` are merged at the install root instead of
  being copied as a nested ``hosts/<provider>`` directory. Claude gets
  ``hooks/hooks.json``, Cursor ``hooks.json``, OpenCode ``plugin.js`` and its
  ``opencode.json`` skills source.
* the reviewer agent is generated from ``agents/reviewer.prompt.md`` with
  frontmatter the host understands.

Hooks are optional by design: a host payload may omit them (or the entire
``hosts/<provider>/`` directory) and installation still succeeds. The skills
call ``adaptive-artifacts hook-start`` themselves when no hook exists.
"""

from __future__ import annotations

from pathlib import Path

from installer.adapters import register_adapter
from installer.adapters.base import BaseAdapter
from installer.agents import generated_agent
from installer.allowlist import IGNORE_NAMES, IGNORE_SUFFIXES, is_allowed


class NativeAdapter(BaseAdapter):
    """Skills, contract, host files merged at the root, generated agent."""

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
    """Claude Code: ``.claude/{skills,agents,hooks}`` project or user root."""


@register_adapter("cursor")
class CursorAdapter(NativeAdapter):
    """Cursor: ``.cursor/{skills,agents,hooks.json}`` project or user root."""


@register_adapter("opencode")
class OpenCodeAdapter(NativeAdapter):
    """OpenCode: ``skills`` source, ``agents/``, and ``plugin.js`` hooks."""
