"""Payload fields shared by the built-in planning and evidence schemas."""

from typing import TypedDict

from orchestra.canon import record_payload
from orchestra.canon.types import JsonObject, Record


class PlanningPayload(TypedDict, total=False):
    acceptance: str
    alternatives: str
    answer: str
    applies_to: str
    area: str
    assignee: str
    assignment: str
    attempted_action: str
    attempts: int
    base: str
    base_rev: str
    basis: str
    blocking: bool
    choice: str
    claim: str
    claim_id: str
    claim_ids: list[str]
    confidence: str
    contradicted_by: list[str]
    criterion: str
    criterion_id: str
    decisions: list[str]
    depends_on: list[str]
    diff_sha256: str
    duration_s: int | float
    effort: str
    environment: str
    estimate_minutes: int
    evidence_kind: str
    executor: str
    exit_code: int
    failing_node_ids: list[str]
    goal: str
    head_rev: str
    informed_by: list[str]
    invalidated_when: str
    kind: str
    level: str
    merged_from: list[str]
    method: str
    milestone: str
    missing: str
    needs: str
    new_hashes: list[str]
    next: str
    observation_id: str
    observed_time: str
    old_hashes: list[str]
    oracle_hashes: list[str]
    ordinal: int
    output_sha256: str
    owner: str
    phase: str
    position: str
    question: str
    replay: str
    requirement: str
    requirements: list[str]
    resolution_note: str
    result: str
    retired: bool
    retry_when: str
    revision: str
    runner: str
    scope: str
    severity: str
    signed_by: str
    signed_note: str
    size: str
    source: str
    state: str
    statement: str
    status: str
    technique: str
    test_ids: list[str]
    title: str
    verdict: str
    verify_command: str
    weight: str
    what_was_observed: str
    work_item: str


def planning_payload(record: Record | JsonObject) -> PlanningPayload:
    # Built-in schemas validate these field types before model reads.
    return record_payload(record)  # pyright: ignore[reportReturnType]
