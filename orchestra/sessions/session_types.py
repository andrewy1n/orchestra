from __future__ import annotations

from datetime import datetime
from typing import TypeAlias, TypedDict

from orchestra.score.effort_rollup import EffortRollup

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]


class TranscriptEvent(TypedDict, total=False):
    attributionSkill: JsonValue
    sessionId: JsonValue
    cwd: JsonValue
    gitBranch: JsonValue
    type: JsonValue
    timestamp: JsonValue
    totalCostUSD: JsonValue
    isMeta: JsonValue
    isSidechain: JsonValue
    message: JsonValue


class SessionFields(TypedDict):
    session_id: JsonValue
    cwd: JsonValue
    branch: JsonValue
    start: str | None
    end: str | None
    duration_seconds: float | None
    turns: int
    cost_usd: float | None
    skills: dict[str, int]


class RecordMetadata(TypedDict):
    id: str
    record_type: str
    subject: str | None
    effort: str | None
    recorded_at: datetime | str
    lifecycle_state: str | None
    store: str


class RecordJoinBucket(TypedDict):
    records: list[str]
    ambiguous: list[str]


class RecordJoinResult(TypedDict):
    by_session: dict[str, RecordJoinBucket]
    unattached: list[str]


class ToolCount(TypedDict):
    calls: int
    errors: int
    retries: int


class ToolMetrics(TypedDict):
    tools: dict[str, ToolCount]
    totals: ToolCount


class SessionRecordSummary(TypedDict):
    total: int
    by_type: dict[str, int]
    efforts: list[str]
    tasks: list[str]
    ambiguous: int


class SessionSummary(SessionFields):
    tools: ToolMetrics
    bad_lines: int


class SessionReport(SessionSummary, total=False):
    project: str
    file: str
    records: SessionRecordSummary


class SessionError(TypedDict):
    project: str
    file: str
    error: str


SessionOutput: TypeAlias = SessionReport | SessionError


class ToolRollup(TypedDict):
    name: str
    calls: int
    errors: int
    error_rate: float
    retries: int
    sessions: int


class SkillRollup(TypedDict):
    name: str
    invocations: int
    sessions: int


class SessionOutlier(TypedDict):
    session_id: JsonValue
    file: JsonValue
    project: JsonValue
    branch: JsonValue
    efforts: list[JsonValue]
    value: int | float


class SessionCaveats(TypedDict):
    attached_records: int
    ambiguous_records: int
    ambiguous_share: float
    note: str
    sessions_with_cost: int
    sessions_without_cost: int
    cost_note: str
    bad_input_lines: int


class SessionAggregate(TypedDict):
    sessions: int
    efforts: dict[str, EffortRollup]
    tools: list[ToolRollup]
    skills: list[SkillRollup]
    outliers: dict[str, list[SessionOutlier]]
    caveats: SessionCaveats
