"""Generate the reviewer agent for one host from one canonical prompt.

``agents/reviewer.prompt.md`` is the only place the reviewer's prompt and
restriction set are authored. A host adapter renders that document into the
frontmatter its harness understands:

===========  ==========================================================
host         rendering
===========  ==========================================================
Claude Code  ``tools:`` allowlist
OpenCode     ``mode: subagent`` plus a ``permissions:`` map
Cursor       ``readonly: true`` (the closest read-only agent switch)
===========  ==========================================================

The body is copied byte-for-byte into every host file, so a prompt change
reaches all hosts at once and never drifts per host.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CANONICAL_PATH = Path("agents") / "reviewer.prompt.md"
AGENT_FILENAME = "se-reviewer.md"

#: Where each native host discovers a project/global subagent file.
HOST_DESTINATIONS = {
    "claude": f"agents/{AGENT_FILENAME}",
    "cursor": f"agents/{AGENT_FILENAME}",
    "opencode": f"agents/{AGENT_FILENAME}",
}

#: Tools the canonical prompt may allow. Anything write-shaped is denied.
DEFAULT_TOOLS = ("Read", "Grep", "Glob", "Bash")
DEFAULT_DENY = ("Write", "Edit", "NotebookEdit")


@dataclass(frozen=True)
class CanonicalAgent:
    """The parsed canonical prompt plus its restriction set."""

    name: str
    description: str
    mode: str
    tools: tuple[str, ...]
    deny: tuple[str, ...]
    store_writes: bool
    body: str

    @property
    def allows_read_only_tools(self) -> bool:
        return bool(self.tools) and not set(self.tools) & set(self.deny)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the small YAML subset this repository authors.

    Supports ``key: value`` and folded (``>-``) or literal (``|``) blocks.
    Nested maps are host renderings, not canonical input; a canonical prompt
    with an indented line under an unknown key is rejected.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("agent prompt has no frontmatter")
    end = next(
        (index for index in range(1, len(lines)) if lines[index].strip() == "---"),
        None,
    )
    if end is None:
        raise ValueError("agent prompt frontmatter is not closed")

    meta: dict[str, str] = {}
    index = 1
    while index < end:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith((" ", "\t")):
            raise ValueError(f"unexpected indented line in frontmatter: {line!r}")
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"frontmatter line is not a key: {line!r}")
        key = key.strip()
        value = value.strip()
        if value in (">-", ">", "|", "|-"):
            block: list[str] = []
            index += 1
            while index < end and (
                lines[index].startswith((" ", "\t")) or not lines[index].strip()
            ):
                block.append(lines[index].strip())
                index += 1
            if value.startswith(">"):
                meta[key] = " ".join(part for part in block if part)
            else:
                meta[key] = "\n".join(block).strip()
            continue
        meta[key] = value
        index += 1

    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body


def _split_list(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None or not value.strip():
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


def load(source_root: Path | str) -> CanonicalAgent:
    """Read and validate ``agents/reviewer.prompt.md``."""
    path = Path(source_root) / CANONICAL_PATH
    meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    name = meta.get("name", "").strip()
    description = meta.get("description", "").strip()
    if not name:
        raise ValueError(f"{path} needs a name")
    if not description:
        raise ValueError(f"{path} needs a description")
    if not body.strip():
        raise ValueError(f"{path} needs a prompt body")
    mode = meta.get("mode", "subagent").strip() or "subagent"
    tools = _split_list(meta.get("tools"), DEFAULT_TOOLS)
    deny = _split_list(meta.get("deny"), DEFAULT_DENY)
    store_writes = meta.get("store_writes", "false").strip().lower() == "true"
    if store_writes:
        raise ValueError(f"{path} must not grant store writes")
    agent = CanonicalAgent(
        name=name,
        description=description,
        mode=mode,
        tools=tools,
        deny=deny,
        store_writes=store_writes,
        body=body.strip() + "\n",
    )
    if not agent.allows_read_only_tools:
        raise ValueError(f"{path} allows a tool it also denies")
    return agent


def render(provider_id: str, agent: CanonicalAgent) -> str:
    """Render the canonical agent for one host."""
    if provider_id not in HOST_DESTINATIONS:
        raise KeyError(f"no reviewer agent rendering for {provider_id!r}")
    lines = [
        "---",
        f"name: {agent.name}",
        "description: >-",
        f"  {agent.description}",
    ]
    if provider_id == "claude":
        lines.append(f"tools: {', '.join(agent.tools)}")
    elif provider_id == "opencode":
        lines.append(f"mode: {agent.mode}")
        lines.append("permissions:")
        permissions = {tool.lower(): "allow" for tool in agent.tools}
        for tool in agent.deny:
            key = "edit" if tool.lower() in ("edit", "notebookedit") else tool.lower()
            permissions[key] = "deny"
        permissions.setdefault("webfetch", "deny")
        for key, value in permissions.items():
            lines.append(f"  {key}: {value}")
    elif provider_id == "cursor":
        lines.append("readonly: true")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + agent.body


def generated_agent(
    source_root: Path | str, provider_id: str
) -> tuple[str, str] | None:
    """Return ``(destination-relative path, text)`` for a native host.

    ``None`` means this host has no generated-agent rendering or the canonical
    prompt is absent (an install without the agent still applies).
    """
    if provider_id not in HOST_DESTINATIONS:
        return None
    if not (Path(source_root) / CANONICAL_PATH).is_file():
        return None
    agent = load(source_root)
    return HOST_DESTINATIONS[provider_id], render(provider_id, agent)


def render_all(source_root: Path | str) -> dict[str, str]:
    """Every host rendering, keyed by provider id (for tests and docs)."""
    agent = load(source_root)
    return {
        provider_id: render(provider_id, agent) for provider_id in HOST_DESTINATIONS
    }
