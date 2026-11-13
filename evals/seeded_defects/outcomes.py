from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from orchestra.conductor.reviewer import ParsedReviewerOutput

IncompleteReason = Literal["failed", "usage_limit", "unparsable"]


@dataclass(frozen=True)
class Complete:
    parsed: ParsedReviewerOutput


@dataclass(frozen=True)
class Incomplete:
    reason: IncompleteReason


Outcome = Complete | Incomplete
