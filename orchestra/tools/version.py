from __future__ import annotations

import re
from dataclasses import dataclass

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_version(output: str) -> Version:
    match = _VERSION_RE.search(output)
    if match is None:
        raise ValueError(f"no version found in output: {output!r}")
    major, minor, patch = match.groups()
    return Version(int(major), int(minor), int(patch) if patch else 0)
