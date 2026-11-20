from __future__ import annotations

from orchestra.canon.errors import StaleWriteError
from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.score.lookups import current_phase, live_work_items, owning_work_item
from orchestra.score.oracle_policy import resolve_oracle_policy

ROUTINE_CHECKS = ("documentation", "packaging", "final-verification")


def amend_acceptance(
    project: Project,
    acceptance_id: str,
    *,
    expected_revision: str,
    basis: str,
    equivalent_command: str | None = None,
    routine_check: str | None = None,
) -> Record:
    if (equivalent_command is None) == (routine_check is None):
        raise ValueError("choose one acceptance change")
    if not basis.strip():
        raise ValueError("give the reason and the evidence for the change")

    token = project.change_token()
    acceptance = project.get(acceptance_id, "score:acceptance")
    if acceptance["revision"] != expected_revision:
        raise StaleWriteError("acceptance changed since it was read")
    if acceptance["lifecycle_state"] != "active":
        raise ValueError("acceptance must be active")
    payload = acceptance["payload"]
    method, command = payload.get("method"), payload.get("verify_command")
    if method not in ("tdd", "check") or not isinstance(command, str) or not command.strip():
        raise ValueError("acceptance must have an automated verification command")

    phase, effort = payload.get("phase"), payload.get("effort")
    if not isinstance(phase, str) or not phase or not isinstance(effort, str):
        raise ValueError("acceptance must belong to an effort and phase")
    effort_record = project.resolve("score:effort", effort)
    if effort_record["payload"].get("autonomy") not in ("auto-plan", "auto-phases"):
        raise ValueError("acceptance changes require auto-plan or auto-phases")
    records = project.records()
    task = owning_work_item(acceptance["subject"], live_work_items(phase, records))
    if task is None or task["lifecycle_state"] != "in_progress":
        raise ValueError("the owning work-item must be in progress")
    phase_record = current_phase(phase, records)
    if phase_record is None or phase_record["payload"].get("effort") != effort:
        raise ValueError("acceptance phase does not belong to its effort")
    if payload.get("claim") or resolve_oracle_policy(payload, phase_record["payload"]) != "none":
        raise ValueError("use the existing review process for frozen or claim-backed acceptances")

    change: JsonObject
    if equivalent_command is not None:
        new_command = equivalent_command.strip()
        if not new_command or new_command == command.strip():
            raise ValueError("give a different non-empty verification command")
        change = {"op": "update", "payload": {"verify_command": new_command}}
        detail = f"Verification command changed from `{command}` to `{new_command}`."
    else:
        if method != "tdd" or routine_check not in ROUTINE_CHECKS:
            raise ValueError("only a routine TDD acceptance can change to check")
        change = {"op": "supersede", "payload": {"method": "check"}}
        detail = f"Verification method changed from `tdd` to `check` for {routine_check}."

    project.apply_at_snapshot(
        [
            {
                **change,
                "id": acceptance_id,
                "type": "score:acceptance",
                "expected_revision": expected_revision,
            },
            {
                "op": "create",
                "type": "conductor:assignment-amendment",
                "subject": task["subject"],
                "payload": {"work_item": task["subject"], "effort": effort},
                "body": f"## Correction\n\n{acceptance['subject']}. {detail}\n\n{basis.strip()}",
            },
        ],
        token,
    )
    return project.resolve("score:acceptance", acceptance["subject"])
