from __future__ import annotations

import string
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from itertools import product

from orchestra.canon.types import Record


@dataclass(frozen=True)
class PatternSegment:
    value: str
    tokens: tuple[str, ...]
    globstar: bool


@dataclass(frozen=True)
class TouchPattern:
    declaration: str
    segments: tuple[PatternSegment, ...]


@dataclass(frozen=True)
class TouchIssue:
    task: str
    declaration: str
    message: str


@dataclass(frozen=True)
class TouchValidation:
    patterns: tuple[TouchPattern, ...]
    issues: tuple[TouchIssue, ...]


_ANY_SEGMENT = PatternSegment("*", ("*",), False)


def validate_touches(item: Record) -> TouchValidation:
    subject = item["subject"]
    payload = item["payload"]
    if "touches" not in payload:
        return TouchValidation((), ())

    value = payload["touches"]
    if not isinstance(value, list):
        return TouchValidation(
            (), (TouchIssue(subject, repr(value), "touches must be a list of strings"),)
        )

    patterns: list[TouchPattern] = []
    issues: list[TouchIssue] = []
    for declaration in value:
        if not isinstance(declaration, str):
            issues.append(
                TouchIssue(
                    subject,
                    repr(declaration),
                    "touches entries must be strings",
                )
            )
            continue
        message = _invalid_declaration(declaration)
        if message is not None:
            issues.append(TouchIssue(subject, declaration, message))
            continue
        segments = tuple(_parse_segment(part) for part in declaration.split("/"))
        patterns.append(TouchPattern(declaration, segments))
    return TouchValidation(tuple(patterns), tuple(issues))


def overlap(left: TouchPattern, right: TouchPattern) -> str | None:
    pending: deque[tuple[int, int, tuple[str, ...], bool]] = deque([(0, 0, (), False)])
    visited: set[tuple[int, int, bool]] = set()
    while pending:
        left_index, right_index, path, consumed = pending.popleft()
        key = (left_index, right_index, consumed)
        if key in visited:
            continue
        visited.add(key)

        left_positions = _globstar_closure(left.segments, left_index)
        right_positions = _globstar_closure(right.segments, right_index)
        for left_position, right_position in product(left_positions, right_positions):
            if (
                consumed
                and left_position == len(left.segments)
                and right_position == len(right.segments)
            ):
                return "/".join(path)
            if left_position == len(left.segments) or right_position == len(right.segments):
                continue

            left_segment = left.segments[left_position]
            right_segment = right.segments[right_position]
            left_tokens = _ANY_SEGMENT.tokens if left_segment.globstar else left_segment.tokens
            right_tokens = _ANY_SEGMENT.tokens if right_segment.globstar else right_segment.tokens
            witness = _segment_overlap(left_tokens, right_tokens, not consumed)
            if witness is None:
                continue

            next_left = left_position if left_segment.globstar else left_position + 1
            next_right = right_position if right_segment.globstar else right_position + 1
            pending.append((next_left, next_right, (*path, witness), True))
    return None


def _invalid_declaration(value: str) -> str | None:
    if not value:
        return "path must not be empty"
    if value.startswith("/"):
        return "path must be repository-relative"
    if len(value) >= 2 and value[0] in string.ascii_letters and value[1] == ":":
        return "path must not have a drive prefix"
    if "\\" in value:
        return "backslashes are not supported"
    if "\x00" in value:
        return "NUL is not supported"
    for part in value.split("/"):
        if not part:
            return "path must not contain empty segments"
        if part in {".", ".."}:
            return "path must not contain '.' or '..' segments"
        if any(char in part for char in "[]{}"):
            return "brackets and braces are not supported"
        if "**" in part and part != "**":
            return "'**' must occupy a whole path segment"
    return None


def _parse_segment(value: str) -> PatternSegment:
    return PatternSegment(value, tuple(value), value == "**")


def _globstar_closure(segments: tuple[PatternSegment, ...], index: int) -> tuple[int, ...]:
    positions = [index]
    while positions[-1] < len(segments) and segments[positions[-1]].globstar:
        positions.append(positions[-1] + 1)
    return tuple(positions)


@lru_cache(maxsize=4096)
def _segment_overlap(left: tuple[str, ...], right: tuple[str, ...], first: bool) -> str | None:
    alphabet = _segment_alphabet(left, right)
    pending: deque[tuple[tuple[int, ...], tuple[int, ...], int, int, str]] = deque(
        [(_epsilon_closure(left, (0,)), _epsilon_closure(right, (0,)), 0, 0, "")]
    )
    visited: set[tuple[tuple[int, ...], tuple[int, ...], int, int]] = set()
    while pending:
        left_states, right_states, dot_state, drive_state, value = pending.popleft()
        key = (left_states, right_states, dot_state, drive_state)
        if key in visited:
            continue
        visited.add(key)
        if (
            len(left) in left_states
            and len(right) in right_states
            and dot_state == 3
            and (not first or drive_state != 2)
        ):
            return value

        for char in alphabet:
            next_left = _advance(left, left_states, char)
            if not next_left:
                continue
            next_right = _advance(right, right_states, char)
            if not next_right:
                continue
            next_dot = _dot_state(dot_state, char)
            next_drive = _drive_state(drive_state, char) if first else 0
            if first and next_drive == 2:
                continue
            pending.append((next_left, next_right, next_dot, next_drive, value + char))
    return None


def _segment_alphabet(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    literals = {token for token in (*left, *right) if token not in {"*", "?"}}
    candidates = set(string.ascii_letters + string.digits + string.punctuation + " ")
    candidates.update(literals)
    candidates.discard("/")
    candidates.discard("\\")
    candidates.discard("\x00")
    generic = next(
        char
        for codepoint in range(0xA1, 0x110000)
        if not 0xD800 <= codepoint <= 0xDFFF and (char := chr(codepoint)) not in literals
    )
    candidates.add(generic)
    priority = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ~"
    return tuple(
        sorted(
            candidates,
            key=lambda char: (
                char not in priority,
                priority.find(char) if char in priority else ord(char),
            ),
        )
    )


def _epsilon_closure(tokens: tuple[str, ...], positions: tuple[int, ...]) -> tuple[int, ...]:
    result = set(positions)
    pending = list(positions)
    while pending:
        position = pending.pop()
        if position < len(tokens) and tokens[position] == "*" and position + 1 not in result:
            result.add(position + 1)
            pending.append(position + 1)
    return tuple(sorted(result))


def _advance(tokens: tuple[str, ...], positions: tuple[int, ...], char: str) -> tuple[int, ...]:
    result: set[int] = set()
    for position in positions:
        if position >= len(tokens):
            continue
        token = tokens[position]
        if token == "*":
            result.add(position)
        elif token == "?" or token == char:
            result.add(position + 1)
    return _epsilon_closure(tokens, tuple(sorted(result)))


def _dot_state(state: int, char: str) -> int:
    if state == 0:
        return 1 if char == "." else 3
    if state == 1:
        return 2 if char == "." else 3
    return 3


def _drive_state(state: int, char: str) -> int:
    if state == 0:
        return 1 if char in string.ascii_letters else 3
    if state == 1:
        return 2 if char == ":" else 3
    return state
