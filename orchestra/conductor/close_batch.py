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
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TypedDict, TypeGuard

from orchestra.canon.errors import StoreError
from orchestra.canon.git_backend import run_git
from orchestra.canon.project import StoreBindingError, open_store
from orchestra.canon.types import JsonObject, JsonValue, Record
from orchestra.conductor.model_types import PlanningPayload
from orchestra.conductor.model_types import planning_payload as record_payload
from orchestra.conductor.oracle_freeze import parse_freeze, parse_hashes

RUNNER_METHODS = frozenset({"tdd", "check"})
RUNNER_MARKER = "orchestra"

CheckRunLoader = Callable[[str], Record]
AcceptanceLoader = Callable[[str], Record]
AmendmentLister = Callable[[str], list[Record]]


class FindingRequest(TypedDict):
    claim: str
    basis: str
    invalidated_when: str
    body: str


class CriterionRequest(TypedDict):
    criterion_id: str
    method: str | None
    result: str
    revision: str
    signed_by: str
    check_run_id: str
    red_check_run_id: str
    red_result: str
    red_runner: str
    red_revision: str
    red_diff_sha256: str
    red_body: str
    red_failing_node_ids: str
    runner: str
    _provided_fields: list[str]


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


class CloseRefused(Exception):
    """Policy refusal -- exit 2, distinct from a malformed request."""


class OracleAdapterUnavailable(Exception):
    """Oracle-backed close needs the tuner library.

    An installed Orchestra CLI serves every other subcommand without tuner
    importable; this gate refuses clearly when the import fails.
    """


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
        finding_fields = ("claim", "basis", "invalidated_when", "body")
        values: dict[str, str] = {}
        for key in finding_fields:
            value = raw_finding.get(key)
            if not isinstance(value, str):
                raise CloseRequestError(f"finding missing field: '{key}'")
            values[key] = value
        finding = {
            "claim": values["claim"],
            "basis": values["basis"],
            "invalidated_when": values["invalidated_when"],
            "body": values["body"],
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


def _entry_passed(entry: CriterionRequest) -> bool:
    return entry.get("result") == "pass"


def _entry_has(entry: CriterionRequest, key: str) -> bool:
    return key in entry["_provided_fields"]


def _is_git_ancestor(ancestor: str, descendant: str, cwd: Path) -> bool:
    """True when ancestor == descendant or ancestor is a git ancestor of descendant."""
    if ancestor == descendant:
        return True
    result = run_git(
        cwd,
        "merge-base",
        "--is-ancestor",
        ancestor,
        descendant,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


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


def _sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_file_at_revision(cwd: Path, revision: str, relpath: str) -> str:
    """Content hash of ``relpath`` at a store-backed check-run revision."""
    result: subprocess.CompletedProcess[bytes] = run_git(
        cwd, "show", f"{revision}:{relpath}", capture_output=True
    )  # pyright: ignore[reportAssignmentType]  # No text or encoding options are passed.
    if result.returncode != 0:
        raise FileNotFoundError(relpath)
    return _sha256_digest(result.stdout)


def tree_oracle_hashes(
    cwd: Path,
    revision: str,
    frozen: dict[str, str],
) -> dict[str, str]:
    """Hash each frozen oracle path at ``revision`` in ``cwd``."""
    out: dict[str, str] = {}
    for relpath in frozen:
        out[relpath] = hash_file_at_revision(cwd, revision, relpath)
    return out


def _load_check_run(
    check_run_id: str,
    *,
    criterion_id: JsonValue,
    label: str,
    loader: CheckRunLoader,
) -> Record:
    try:
        return loader(check_run_id)
    except LookupError as exc:
        raise CloseRefused(
            f"criterion {criterion_id!r}: {label} check_run_id "
            f"{check_run_id!r} not found in artifact store"
        ) from exc


def _match_field(
    *,
    criterion_id: JsonValue,
    label: str,
    field: str,
    requested: JsonValue,
    stored: JsonValue,
) -> None:
    if requested != stored:
        raise CloseRefused(
            f"criterion {criterion_id!r}: {label} {field} mismatch "
            f"(request={requested!r}, store={stored!r})"
        )


def _resolve_green_check_run(
    entry: CriterionRequest,
    *,
    loader: CheckRunLoader,
) -> PlanningPayload:
    """Load and match the green/primary check-run; return its payload."""
    criterion_id = entry.get("criterion_id")
    check_run_id = entry["check_run_id"]
    record = _load_check_run(
        check_run_id,
        criterion_id=criterion_id,
        label="check_run_id",
        loader=loader,
    )
    payload = record_payload(record)

    _match_field(
        criterion_id=criterion_id,
        label="check-run",
        field="criterion_id",
        requested=criterion_id,
        stored=payload.get("criterion_id"),
    )
    _match_field(
        criterion_id=criterion_id,
        label="check-run",
        field="result",
        requested=entry.get("result"),
        stored=payload.get("result"),
    )

    stored_runner = payload.get("runner")
    if stored_runner != RUNNER_MARKER:
        raise CloseRefused(
            f"criterion {criterion_id!r}: check-run is not runner-produced "
            f"(runner must be {RUNNER_MARKER!r}, got {stored_runner!r})"
        )
    if _entry_has(entry, "runner"):
        _match_field(
            criterion_id=criterion_id,
            label="check-run",
            field="runner",
            requested=entry.get("runner"),
            stored=stored_runner,
        )

    if _entry_has(entry, "revision"):
        _match_field(
            criterion_id=criterion_id,
            label="check-run",
            field="revision",
            requested=entry.get("revision"),
            stored=payload.get("revision"),
        )

    return payload


def _resolve_red_check_run(
    entry: CriterionRequest,
    *,
    loader: CheckRunLoader,
) -> tuple[Record, PlanningPayload]:
    """Load and match the red check-run; return (full record, payload)."""
    criterion_id = entry.get("criterion_id")
    red_id = entry.get("red_check_run_id")
    if not red_id:
        raise CloseRefused(
            f"criterion {criterion_id!r}: tdd done close requires "
            "red_check_run_id (runner-produced fail preceding the green)"
        )

    record = _load_check_run(
        red_id,
        criterion_id=criterion_id,
        label="red_check_run_id",
        loader=loader,
    )
    payload = record_payload(record)

    _match_field(
        criterion_id=criterion_id,
        label="red check-run",
        field="criterion_id",
        requested=criterion_id,
        stored=payload.get("criterion_id"),
    )

    if _entry_has(entry, "red_result"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="result",
            requested=entry.get("red_result"),
            stored=payload.get("result"),
        )
    if _entry_has(entry, "red_runner"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="runner",
            requested=entry.get("red_runner"),
            stored=payload.get("runner"),
        )
    if _entry_has(entry, "red_revision"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="revision",
            requested=entry.get("red_revision"),
            stored=payload.get("revision"),
        )
    if _entry_has(entry, "red_diff_sha256"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="diff_sha256",
            requested=entry.get("red_diff_sha256"),
            stored=payload.get("diff_sha256"),
        )

    return record, payload


def _enforce_red_first_from_store(
    entry: CriterionRequest,
    *,
    green_payload: Mapping[str, object],
    red_payload: Mapping[str, object],
    cwd: Path,
) -> None:
    """Refuse tdd done closes whose store red does not precede store green."""
    criterion_id = entry.get("criterion_id")

    red_result = red_payload.get("result")
    if red_result != "fail":
        raise CloseRefused(
            f"criterion {criterion_id!r}: red evidence result must be 'fail', got {red_result!r}"
        )

    red_runner = red_payload.get("runner")
    if red_runner != RUNNER_MARKER:
        raise CloseRefused(
            f"criterion {criterion_id!r}: red check-run is not runner-produced "
            f"(runner must be {RUNNER_MARKER!r}, got {red_runner!r})"
        )

    red_revision = red_payload.get("revision")
    if not red_revision:
        raise CloseRefused(f"criterion {criterion_id!r}: red evidence missing revision")

    if red_revision == "dirty":
        digest = red_payload.get("diff_sha256") or ""
        if not digest:
            raise CloseRefused(
                f"criterion {criterion_id!r}: dirty red requires non-empty diff_sha256"
            )
        return

    # SHA red: request must still carry green revision (anti-gap), and it
    # must match the store; ancestry uses the store revision.
    if not _entry_has(entry, "revision"):
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision required for git-ancestry red-first check"
        )
    green_revision = green_payload.get("revision")
    if not green_revision:
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision required for git-ancestry red-first check"
        )
    if green_revision == "dirty":
        raise CloseRefused(
            f"criterion {criterion_id!r}: cannot verify red-first ordering "
            "when green revision is dirty and red is a SHA"
        )

    if not isinstance(red_revision, str) or not isinstance(green_revision, str):
        raise CloseRefused(f"criterion {criterion_id!r}: revisions must be strings")
    if not _is_git_ancestor(red_revision, green_revision, cwd):
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision is not equal to or "
            f"a git descendant of red revision "
            f"(red={red_revision}, green={green_revision})"
        )


def _assertion_level_red(record: Record) -> bool:
    """Ask tuner whether red failed at assertion level.

    The import stays inside this function so ``orchestra --help`` does not
    import tuner. A missing import raises OracleAdapterUnavailable.
    """
    try:
        from orchestra.tuner.oracle_red import is_assertion_level_red
    except ImportError as exc:
        raise OracleAdapterUnavailable(
            "tuner is not importable; close-batch needs tuner to "
            "classify assertion-level red for oracle-backed acceptances"
        ) from exc
    return bool(is_assertion_level_red(record))


def _approved_amendment_covers_tree(
    amendments: list[Record],
    tree_hashes: dict[str, str],
) -> bool:
    """True when an active approved amendment's new_hashes equal tree hashes."""
    for record in amendments:
        payload = record_payload(record)
        if str(payload.get("status") or "") != "approved":
            continue
        try:
            new_hashes = parse_hashes(payload.get("new_hashes"))
        except ValueError:
            continue
        if new_hashes and new_hashes == tree_hashes:
            return True
    return False


def _manifest_claim_ids(cwd: Path) -> set[str] | None:
    """Claim ids in ``.tuner/manifest.json``, or None when it is absent.

    An empty set means the manifest exists but lists no usable claims, so a
    non-empty ``payload.claim`` is not listed and must refuse.
    """
    path = cwd / ".tuner" / "manifest.json"
    if not path.is_file():
        return None
    try:
        data: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    claims = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claims, list):
        return set()
    ids: set[str] = set()
    for claim in claims:
        if isinstance(claim, dict) and claim.get("id"):
            ids.add(str(claim["id"]))
    return ids


def _run_tuner_claim_gate(claim_id: str, *, cwd: Path, revision: str) -> None:
    """Refuse unless tuner verdict and recheck both pass for the claim.

    Imports stay inside this function so ``orchestra --help`` does not import
    tuner. A missing import raises an error that names tuner.
    """
    try:
        from orchestra.tuner.binding import recheck
        from orchestra.tuner.verdict import run_verdict
    except ImportError as exc:
        raise CloseRefused(
            f"tuner is not importable; cannot run verdict or recheck for claim {claim_id!r}"
        ) from exc
    failed: list[str] = []
    details: list[str] = []
    try:
        verdict = run_verdict(cwd, revision, None, [claim_id])
    except Exception as exc:
        failed.append("verdict")
        details.append(f"verdict: {exc}")
    else:
        if not _is_pass_result(verdict):
            failed.append("verdict")
    try:
        outcome = recheck(cwd, claim_id)
    except Exception as exc:
        failed.append("recheck")
        details.append(f"recheck: {exc}")
    else:
        if not _is_pass_result(outcome):
            failed.append("recheck")
    if failed:
        clocks = " and ".join(failed)
        suffix = f" ({'; '.join(details)})" if details else ""
        raise CloseRefused(
            f"tuner {clocks} refused for claim {claim_id!r} at revision {revision!r}{suffix}"
        )


def _is_pass_result(value: object) -> bool:
    return _is_object(value) and value.get("result") == "pass"


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _enforce_claim_gates(
    criteria: list[CriterionRequest],
    *,
    green_by_criterion: dict[JsonValue, Mapping[str, object]],
    cwd: Path,
    acceptances: Mapping[str, Record],
) -> None:
    """Manifest-backed acceptances need tuner verdict and recheck on done.

    The claim id comes only from the acceptance payload field ``claim``.
    An acceptance that cannot be loaded refuses, and so does a claim id
    that the manifest does not list. An empty claim is not gated.
    """
    claim_ids = _manifest_claim_ids(cwd)
    if claim_ids is None:
        return
    for entry in criteria:
        criterion_id = entry.get("criterion_id")
        acceptance = acceptances[entry["criterion_id"]]
        payload = record_payload(acceptance)
        claim_id = str(payload.get("claim") or "").strip()
        if not claim_id:
            continue
        if claim_id not in claim_ids:
            raise CloseRefused(
                f"criterion {criterion_id!r}: claim {claim_id!r} is not "
                "listed in .tuner/manifest.json"
            )
        revision: object = None
        green = green_by_criterion.get(criterion_id)
        if green is not None:
            revision = green.get("revision")
        if not revision:
            revision = entry.get("revision")
        if not revision:
            raise CloseRefused(
                f"criterion {criterion_id!r}: claim {claim_id!r} requires "
                "a close revision for tuner verdict"
            )
        _run_tuner_claim_gate(claim_id, cwd=cwd, revision=str(revision))


def _enforce_oracle_gates(
    entry: CriterionRequest,
    *,
    green_payload: Mapping[str, object],
    red_record: Record,
    cwd: Path,
    acceptance: Record,
    list_oracle_amendments: AmendmentLister,
) -> None:
    criterion_id = entry["criterion_id"]
    try:
        frozen = parse_freeze(acceptance["payload"])
    except ValueError as exc:
        raise CloseRefused(f"criterion {criterion_id!r}: incomplete oracle freeze: {exc}") from exc

    try:
        assertion_red = _assertion_level_red(red_record)
    except OracleAdapterUnavailable as exc:
        raise CloseRefused(f"criterion {criterion_id!r}: {exc}") from exc
    if not assertion_red:
        raise CloseRefused(
            f"criterion {criterion_id!r}: oracle-backed tdd requires "
            "assertion-level red (fail with assertion failure); "
            "import/collection-only red is refused"
        )

    failing_nodes = record_payload(red_record).get("failing_node_ids")
    test_ids = record_payload(acceptance)["test_ids"]
    if (
        not isinstance(failing_nodes, list)
        or not failing_nodes
        or any(node not in test_ids for node in failing_nodes)
    ):
        raise CloseRefused(
            f"criterion {criterion_id!r}: assertion red must identify frozen test ids"
        )

    green_revision = green_payload.get("revision")
    if not isinstance(green_revision, str) or not re.fullmatch(
        r"(?:[0-9a-f]{40}|[0-9a-f]{64})", green_revision
    ):
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision must be a pinned commit for the freeze check"
        )

    try:
        tree = tree_oracle_hashes(cwd, str(green_revision), frozen)
    except FileNotFoundError as exc:
        raise CloseRefused(
            f"criterion {criterion_id!r}: oracle file missing at green "
            f"revision {green_revision!r}: {exc}"
        ) from exc

    if tree == frozen:
        return

    amendments = list_oracle_amendments(str(criterion_id))
    if _approved_amendment_covers_tree(amendments, tree):
        return

    raise CloseRefused(
        f"criterion {criterion_id!r}: oracle hash drift at green revision "
        f"{green_revision!r} without an approved oracle-amendment whose "
        "new_hashes match the tree (freeze hashes are the close authority)"
    )


def build_batch(
    request: Mapping[str, object],
    *,
    cwd: str | Path | None = None,
    store_root: str | Path | None = None,
    load_check_run: CheckRunLoader | None = None,
    load_acceptance: AcceptanceLoader | None = None,
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

    # Store authority for done closes: resolve every runner check-run id.
    green_by_criterion: dict[JsonValue, Mapping[str, object]] = {}
    if transition == "done":
        acceptances: dict[str, Record] = {}
        for aid in acceptance_ids:
            try:
                acceptances[aid] = acceptance_loader(aid)
            except (LookupError, StoreBindingError, StoreError, OSError) as exc:
                raise CloseRefused(
                    f"criterion {aid!r}: acceptance could not be loaded: {exc}"
                ) from exc
        passed_ids = {entry["criterion_id"] for entry in criteria if _entry_passed(entry)}
        for aid, acceptance in acceptances.items():
            if record_payload(acceptance).get("method") == "tdd" and aid not in passed_ids:
                raise CloseRefused(f"criterion {aid!r}: TDD close requires a passing criterion")
        for entry in criteria:
            aid = entry["criterion_id"]
            _match_field(
                criterion_id=aid,
                label="acceptance",
                field="method",
                requested=entry["method"],
                stored=record_payload(acceptances[aid]).get("method"),
            )
            if entry.get("method") not in RUNNER_METHODS:
                continue
            green_by_criterion[entry.get("criterion_id")] = _resolve_green_check_run(
                entry, loader=loader
            )
        _enforce_claim_gates(
            criteria,
            green_by_criterion=green_by_criterion,
            cwd=work_cwd,
            acceptances=acceptances,
        )

        for entry in criteria:
            if entry.get("method") != "tdd":
                continue
            if not _entry_passed(entry):
                continue
            green_payload = green_by_criterion[entry.get("criterion_id")]
            red_record, red_payload = _resolve_red_check_run(entry, loader=loader)
            _enforce_red_first_from_store(
                entry,
                green_payload=green_payload,
                red_payload=red_payload,
                cwd=work_cwd,
            )
            _enforce_oracle_gates(
                entry,
                green_payload=green_payload,
                red_record=red_record,
                cwd=work_cwd,
                acceptance=acceptances[entry["criterion_id"]],
                list_oracle_amendments=amendment_lister,
            )

    passed_ids = {entry["criterion_id"] for entry in criteria if _entry_passed(entry)}
    unmet = [aid for aid in acceptance_ids if aid not in passed_ids]

    if transition == "done" and unmet and not finding:
        raise CloseRefused(
            "closing to done with unmet or unverified criterion(s) "
            f"{unmet} and no finding -- refusing. Either resolve those "
            "criteria first, or supply `finding` (claim, basis, "
            "invalidated_when, body) to close anyway."
        )

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
            finding_payload: JsonObject = {
                "claim": finding["claim"],
                "basis": finding["basis"],
                "invalidated_when": finding["invalidated_when"],
                "effort": effort,
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
    except OracleAdapterUnavailable as exc:
        print(f"close-batch: {exc}", file=sys.stderr)
        return 2
    except CloseRequestError as exc:
        print(f"close-request malformed: {exc}", file=sys.stderr)
        return 1

    _write(args.out, "\n".join(json.dumps(op) for op in ops) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
