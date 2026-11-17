"""Build the NDJSON `apply` batch that closes a work-item.

Reads a close-request JSON describing the work-item's active acceptances,
each criterion's evidence, and the transition to apply.

For `method` `tdd` or `check`, the binary check-run must already exist
(from `orchestra check`). The request references that runner-produced
`check_run_id` and copies its `result` for the refusal gate — this
script does not invent pass/fail or emit a `tuner:check-run` create
for those methods.

On a `done` transition, each referenced check-run is loaded from the
artifact store (same discovery as `orchestra check`: store from process cwd,
`--cwd` for git ancestry only) and matched on criterion_id, runner,
result, and revision when the request carries them. Fabricated ids or
field mismatches refuse the batch.

For `method` `tdd` on a `done` transition, the request must also carry
red-first evidence (`red_check_run_id` and copied fail fields). The red
check-run is resolved from the store the same way; ancestry uses the
store's revisions (or a dirty red with `diff_sha256`), with a non-empty diff digest.

For `method` `manual`, the request carries `result` / `revision` /
`signed_by` and this script emits one `tuner:check-run` create per
entry (linked `informed_by` both its acceptance and the
execution-report when there is one).

An optional `tuner:finding` and the work-item transition follow, in
that order -- ready to feed straight into `canon apply`.

What it enforces: closing to `done` while a criterion is unmet or was
never checked requires a `finding` in the same request, or the batch
is refused outright rather than silently written without one. Pass-only
`tdd` closes without red evidence are refused the same way.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict, TypeGuard

from orchestra.canon.errors import StoreError
from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.model_types import planning_payload as record_payload
from orchestra.conductor.task_close import (
    RUNNER_METHODS,
    AcceptanceLoader,
    AmendmentLister,
    CheckRunLoader,
    CloseRecords,
    CloseRefusal,
    CloseRefused,
    CriterionRequest,
    PhaseLoader,
    decide_close_with,
)
from orchestra.conductor.task_close import entry_has as _entry_has
from orchestra.score.lookups import current_phase


class FindingRequest(TypedDict):
    claim: str
    basis: str
    invalidated_when: str
    body: str
    phase: str | None


class CloseRequest(TypedDict):
    subject: str
    effort: str
    work_item_id: str
    transition: str
    acceptance_ids: list[str]
    criteria: list[CriterionRequest]
    execution_report_id: str | None
    finding: FindingRequest | None


class CloseRequestError(Exception):
    """Malformed close-request -- exit 1, distinct from a policy refusal."""


def _is_object_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, Mapping)


def _is_object_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _parse_close_request(raw: Mapping[str, object]) -> CloseRequest:
    required = ("subject", "effort", "work_item_id", "transition")
    fields: dict[str, str] = {}
    for key in required:
        value = raw.get(key)
        if not isinstance(value, str):
            raise CloseRequestError(f"missing field: '{key}'")
        fields[key] = value

    acceptance_ids = raw.get("acceptance_ids")
    if not _is_object_list(acceptance_ids) or not all(
        isinstance(value, str) for value in acceptance_ids
    ):
        raise CloseRequestError("missing field: 'acceptance_ids'")
    parsed_acceptance_ids: list[str] = [value for value in acceptance_ids if isinstance(value, str)]

    raw_criteria = raw.get("criteria", [])
    if not _is_object_list(raw_criteria):
        raise CloseRequestError("field 'criteria' must be a list")
    criteria: list[CriterionRequest] = []
    criterion_fields = (
        "criterion_id",
        "method",
        "result",
        "revision",
        "signed_by",
        "check_run_id",
        "red_check_run_id",
        "red_result",
        "red_runner",
        "red_revision",
        "red_diff_sha256",
        "red_body",
        "red_failing_node_ids",
        "runner",
    )
    for raw_entry in raw_criteria:
        if not _is_object_mapping(raw_entry):
            raise CloseRequestError("each criteria entry must be an object")
        if "_provided_fields" in raw_entry:
            raise CloseRequestError("field '_provided_fields' is reserved")
        criterion_values: dict[str, str] = {}
        for key in criterion_fields:
            value = raw_entry.get(key)
            if key in raw_entry and not isinstance(value, str):
                raise CloseRequestError(f"criterion field '{key}' must be a string")
            criterion_values[key] = value if isinstance(value, str) else ""
        entry: CriterionRequest = {
            "criterion_id": criterion_values["criterion_id"],
            "method": criterion_values["method"] if "method" in raw_entry else None,
            "result": criterion_values["result"],
            "revision": criterion_values["revision"],
            "signed_by": criterion_values["signed_by"],
            "check_run_id": criterion_values["check_run_id"],
            "red_check_run_id": criterion_values["red_check_run_id"],
            "red_result": criterion_values["red_result"],
            "red_runner": criterion_values["red_runner"],
            "red_revision": criterion_values["red_revision"],
            "red_diff_sha256": criterion_values["red_diff_sha256"],
            "red_body": criterion_values["red_body"],
            "red_failing_node_ids": criterion_values["red_failing_node_ids"],
            "runner": criterion_values["runner"],
            "_provided_fields": [key for key in criterion_fields if key in raw_entry],
        }
        criteria.append(entry)

    execution_report_id = raw.get("execution_report_id")
    if execution_report_id is not None and not isinstance(execution_report_id, str):
        raise CloseRequestError("field 'execution_report_id' must be a string")
    raw_finding = raw.get("finding")
    finding: FindingRequest | None = None
    if raw_finding is not None:
        if not _is_object_mapping(raw_finding):
            raise CloseRequestError("field 'finding' must be an object")
        finding_fields = ("claim", "basis", "invalidated_when", "body", "phase")
        values: dict[str, str] = {}
        for key in finding_fields:
            value = raw_finding.get(key)
            if key == "phase" and value is None:
                values[key] = ""
                continue
            if not isinstance(value, str):
                raise CloseRequestError(f"finding missing field: '{key}'")
            values[key] = value
        finding = {
            "claim": values["claim"],
            "basis": values["basis"],
            "invalidated_when": values["invalidated_when"],
            "body": values["body"],
            "phase": values["phase"] or None,
        }

    return {
        "subject": fields["subject"],
        "effort": fields["effort"],
        "work_item_id": fields["work_item_id"],
        "transition": fields["transition"],
        "acceptance_ids": parsed_acceptance_ids,
        "criteria": criteria,
        "execution_report_id": execution_report_id,
        "finding": finding,
    }


def _open_project(store_root: Path | None):
    return open_store(store_root if store_root is not None else Path.cwd())


def default_load_check_run(
    check_run_id: str,
    *,
    store_root: Path | None = None,
) -> Record:
    """Load a check-run from the store opened for the primary cwd."""
    try:
        return _open_project(store_root).get(check_run_id, "tuner:check-run")
    except (StoreBindingError, StoreError, OSError) as exc:
        raise LookupError(str(exc)) from exc


def default_load_acceptance(
    acceptance_id: str,
    *,
    store_root: Path | None = None,
) -> Record:
    """Load an acceptance from the store opened for the primary cwd."""
    try:
        return _open_project(store_root).get(acceptance_id, "score:acceptance")
    except (StoreBindingError, StoreError, OSError) as exc:
        raise LookupError(str(exc)) from exc


def default_load_phase(phase: str, *, store_root: Path | None = None) -> Record:
    record = current_phase(phase, _open_project(store_root).list("score:phase"))
    if record is None:
        raise LookupError(f"phase {phase!r} not found")
    return record


def default_list_oracle_amendments(
    acceptance_id: str,
    *,
    store_root: Path | None = None,
) -> list[Record]:
    """Active oracle-amendment records whose payload.acceptance is the id or the subject."""
    try:
        project = _open_project(store_root)
        records = project.list("tuner:oracle-amendment")
    except StoreError:
        return []
    refs = {str(acceptance_id)}
    with contextlib.suppress(StoreError):
        refs.add(str(project.get(acceptance_id, "score:acceptance")["subject"]))
    matched: list[Record] = []
    for record in records:
        if record.get("lifecycle_state") not in (None, "active"):
            continue
        if str(record_payload(record).get("acceptance")) in refs:
            matched.append(record)
    return matched


def build_batch(
    request: Mapping[str, object],
    *,
    cwd: str | Path | None = None,
    store_root: str | Path | None = None,
    load_check_run: CheckRunLoader | None = None,
    load_acceptance: AcceptanceLoader | None = None,
    load_phase: PhaseLoader | None = None,
    list_oracle_amendments: AmendmentLister | None = None,
) -> list[JsonObject]:
    parsed_request = _parse_close_request(request)
    try:
        subject = parsed_request["subject"]
        effort = parsed_request["effort"]
        work_item_id = parsed_request["work_item_id"]
        transition = parsed_request["transition"]
        acceptance_ids = list(parsed_request["acceptance_ids"])
        criteria = list(parsed_request.get("criteria", []))
    except KeyError as exc:
        raise CloseRequestError(f"missing field: {exc}") from exc

    execution_report_id = parsed_request.get("execution_report_id")
    finding = parsed_request.get("finding")
    work_cwd = Path(cwd) if cwd is not None else Path.cwd()
    resolved_store = Path(store_root) if store_root is not None else None

    loader: CheckRunLoader
    if load_check_run is not None:
        loader = load_check_run
    else:

        def _store_check_run(check_run_id: str) -> Record:
            return default_load_check_run(check_run_id, store_root=resolved_store)

        loader = _store_check_run

    def acceptance_loader(acceptance_id: str) -> Record:
        if load_acceptance is not None:
            return load_acceptance(acceptance_id)
        return default_load_acceptance(acceptance_id, store_root=resolved_store)

    def phase_loader(phase: str) -> Record:
        if load_phase is not None:
            return load_phase(phase)
        return default_load_phase(phase, store_root=resolved_store)

    def amendment_lister(acceptance_id: str) -> list[Record]:
        if list_oracle_amendments is not None:
            return list_oracle_amendments(acceptance_id)
        return default_list_oracle_amendments(acceptance_id, store_root=resolved_store)

    for entry in criteria:
        criterion_id = entry.get("criterion_id")
        if criterion_id not in acceptance_ids:
            raise CloseRequestError(
                f"criteria entry {criterion_id!r} is not in acceptance_ids {acceptance_ids}"
            )
        method = entry.get("method")
        if method is None:
            raise CloseRequestError("criteria entry missing field: 'method'")
        if method in RUNNER_METHODS:
            if not entry.get("check_run_id"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "reference a runner-produced check_run_id (from "
                    "orchestra check); do not invent pass/fail"
                )
            if not _entry_has(entry, "result"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "copy result from the runner check-run"
                )
            # Invented create shape: signed_by without going through the
            # runner — refuse. For tdd, revision may be copied only when
            # red-first fields are present; for check it remains forbidden.
            if _entry_has(entry, "signed_by"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "not carry signed_by; reference check_run_id only"
                )
            if method == "check" and _entry_has(entry, "revision"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "not carry revision/signed_by; reference check_run_id only"
                )
            if (
                method == "tdd"
                and _entry_has(entry, "revision")
                and not entry.get("red_check_run_id")
            ):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method=tdd must not "
                    "carry revision without red-first fields "
                    "(red_check_run_id); reference check_run_id only or "
                    "include red evidence"
                )
        elif method == "manual":
            for field in ("result", "revision"):
                if not _entry_has(entry, field):
                    raise CloseRequestError(f"criteria entry missing field: '{field}'")
            if entry.get("check_run_id"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method=manual must not "
                    "carry check_run_id; create the manual check-run via the batch"
                )
        else:
            raise CloseRequestError(
                f"criteria entry {criterion_id!r} has unknown method {method!r}"
            )

    records = CloseRecords(
        check_run=loader,
        acceptance=acceptance_loader,
        phase=phase_loader,
        amendments=amendment_lister,
    )
    decision = decide_close_with(
        records,
        criteria,
        acceptance_ids=acceptance_ids,
        cwd=work_cwd,
        transition=transition,
        has_finding=bool(finding),
    )
    if isinstance(decision, CloseRefusal):
        raise CloseRefused(decision.reason)

    ops: list[JsonObject] = []
    for entry in criteria:
        method = entry["method"]
        if method in RUNNER_METHODS:
            # Runner already wrote the check-run; do not invent another.
            continue
        payload: JsonObject = {
            "criterion_id": entry["criterion_id"],
            "revision": entry["revision"],
            "result": entry["result"],
            "effort": effort,
            "method": method,
            "signed_by": entry.get("signed_by", ""),
        }
        informed_by: list[JsonValue] = [entry["criterion_id"]]
        if execution_report_id:
            informed_by.append(execution_report_id)
        payload["informed_by"] = informed_by
        ops.append(
            JsonObject(
                {
                    "op": "create",
                    "type": "tuner:check-run",
                    "subject": subject,
                    "payload": payload,
                }
            )
        )

    if finding:
        try:
            phase: object = finding.get("phase")
            if phase is None:
                work_item = _open_project(resolved_store).get(work_item_id, "score:work-item")
                phase = record_payload(work_item).get("phase")
            if not isinstance(phase, str):
                raise CloseRequestError(f"work-item {work_item_id!r} has no phase")
            finding_payload: JsonObject = {
                "claim": finding["claim"],
                "basis": finding["basis"],
                "invalidated_when": finding["invalidated_when"],
                "effort": effort,
                "phase": phase,
                # Hardcoded, not passed through: this finding exists to
                # surface a deferred/unmet criterion under handoff's Needs
                # Human role, which only fires on needs="human".
                "needs": "human",
            }
            finding_body = finding["body"]
        except KeyError as exc:
            raise CloseRequestError(f"finding missing field: {exc}") from exc
        ops.append(
            JsonObject(
                {
                    "op": "create",
                    "type": "tuner:finding",
                    "subject": subject,
                    "payload": finding_payload,
                    "body": finding_body,
                }
            )
        )

    ops.append(
        JsonObject(
            {
                "op": "update",
                "type": "score:work-item",
                "id": work_item_id,
                "transition": transition,
                "expected_revision": "@current",
            }
        )
    )
    return ops


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write(path: str, text: str) -> None:
    if path == "-":
        sys.stdout.write(text)
        return
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", default="-", help="close-request JSON path, or '-' for stdin (default)"
    )
    parser.add_argument(
        "--out", default="-", help="NDJSON output path, or '-' for stdout (default)"
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="git cwd for red-first ancestry checks (default: process cwd)",
    )
    args = parser.parse_args(argv)

    try:
        request = json.loads(_read(args.input))
    except json.JSONDecodeError as exc:
        print(f"close-request is not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        ops = build_batch(request, cwd=args.cwd)
    except CloseRefused as exc:
        print(f"close refused: {exc}", file=sys.stderr)
        return 2
    except CloseRequestError as exc:
        print(f"close-request malformed: {exc}", file=sys.stderr)
        return 1

    _write(args.out, "\n".join(json.dumps(op) for op in ops) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
