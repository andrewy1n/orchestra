"""Classify assertion-level pytest reds for oracle-backed tdd (R2)."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence

# Short-test-summary / inline failure reasons that are not assertion-level.
_NON_ASSERTION_RE = re.compile(
    r"ImportError|ModuleNotFoundError|SyntaxError|ERROR collecting",
)

# Assertion failure markers in pytest tails (traceback + summary reason).
_ASSERTION_RE = re.compile(
    r"AssertionError|(?:^|\n)E\s+assert\b",
)

_SUMMARY_LINE_RE = re.compile(
    r"^(FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$",
    re.MULTILINE,
)


def _normalize_nodes(failing_node_ids: Sequence[str] | None) -> list[str]:
    return [str(n).strip() for n in (failing_node_ids or []) if str(n).strip()]


def _node_matches(reported: str, wanted: str) -> bool:
    """Match full node ids or collection ERROR paths (file without ``::``)."""
    if reported == wanted:
        return True
    # Collection errors report the module path; accept prefix of a node id.
    if "::" not in reported and wanted.startswith(reported):
        return True
    return False


def _section_for_node(output: str, node: str) -> str:
    """Best-effort slice of output mentioning this node (summary + nearby)."""
    chunks: list[str] = []
    for match in _SUMMARY_LINE_RE.finditer(output or ""):
        kind, reported, reason = match.group(1), match.group(2), match.group(3) or ""
        if _node_matches(reported, node) or _node_matches(node, reported):
            chunks.append(f"{kind} {reported} - {reason}")
    # Include traceback lines that name the node or its module path.
    module = node.split("::", 1)[0]
    for line in (output or "").splitlines():
        if node in line or (module and module in line):
            chunks.append(line)
    return "\n".join(chunks) if chunks else (output or "")


def is_assertion_level_failure(
    output: str,
    failing_node_ids: Sequence[str] | None,
) -> bool:
    """True when at least one failing node shows an assertion failure.

    ImportError, ModuleNotFoundError, SyntaxError, and collection ERROR alone
    are not assertion-level.
    """
    nodes = _normalize_nodes(failing_node_ids)
    if not nodes:
        return False
    text = output or ""
    for node in nodes:
        section = _section_for_node(text, node)
        if not section.strip():
            continue
        # Collection / import / syntax alone → not assertion-level for this node.
        if _NON_ASSERTION_RE.search(section) and not _ASSERTION_RE.search(section):
            continue
        if _ASSERTION_RE.search(section):
            return True
        # Summary FAILED without a non-assertion reason, but assert markers
        # elsewhere near this node already handled; require an assert marker.
    return False


def _payload_and_body(check_run: Mapping[str, Any]) -> tuple[Mapping[str, Any], str]:
    nested = check_run.get("payload")
    if isinstance(nested, dict):
        body = str(check_run.get("body") or nested.get("body") or nested.get("output") or "")
        return nested, body
    body = str(check_run.get("body") or check_run.get("output") or "")
    return check_run, body


def _parse_failing_nodes(raw: Any) -> list[str]:
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return _normalize_nodes(raw)
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(loaded, list):
            return _normalize_nodes(loaded)
    return []


def is_assertion_level_red(check_run: Mapping[str, Any]) -> bool:
    """True when check-run is result=fail with assertion-level failing nodes.

    Accepts a full check-run record (``payload`` + ``body``) or a flat
    payload-shaped mapping.
    """
    payload, body = _payload_and_body(check_run)
    if str(payload.get("result") or "") != "fail":
        return False
    nodes = _parse_failing_nodes(payload.get("failing_node_ids"))
    if not nodes:
        return False
    return is_assertion_level_failure(body, nodes)
