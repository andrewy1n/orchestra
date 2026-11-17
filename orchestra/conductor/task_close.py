"""Decide whether a landed task may close to done."""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, TypeGuard

from orchestra.canon import record_payload
from orchestra.canon.errors import StoreError
from orchestra.canon.project import Project, StoreBindingError
from orchestra.canon.types import JsonValue, Record
from orchestra.conductor import land_task, wave
from orchestra.conductor.model_types import PlanningPayload, planning_payload
from orchestra.conductor.oracle_freeze import parse_freeze, parse_hashes
from orchestra.score.lookups import current_phase
from orchestra.score.oracle_policy import OraclePolicy, resolve_oracle_policy
from orchestra.tools import Git, ToolError

if TYPE_CHECKING:
    from orchestra.conductor.verification import VerificationRun

CODE_DONE = 0
CODE_FAILED = 1
CODE_PENDING_HUMAN = 3
MANUAL_EXIT = 3
RUNNER_METHODS = frozenset({"tdd", "check"})
RUNNER_MARKER = "orchestra"

CheckRunLoader = Callable[[str], Record]
AcceptanceLoader = Callable[[str], Record]
PhaseLoader = Callable[[str], Record]
AmendmentLister = Callable[[str], list[Record]]


class CloseRefused(Exception):
    """Policy refusal -- exit 2, distinct from a malformed request."""


class OracleAdapterUnavailable(Exception):
    """Oracle-backed close needs the tuner library.

    An installed Orchestra CLI serves every other subcommand without tuner
    importable; this gate refuses clearly when the import fails.
    """


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


@dataclass(frozen=True)
class CloseRefusal:
    reason: str


@dataclass(frozen=True)
class CloseApproval:
    pass


CloseDecision = CloseRefusal | CloseApproval


@dataclass(frozen=True)
class CloseRecords:
    check_run: CheckRunLoader
    acceptance: AcceptanceLoader
    phase: PhaseLoader
    amendments: AmendmentLister


def entry_has(entry: CriterionRequest, key: str) -> bool:
    return key in entry["_provided_fields"]


def _entry_passed(entry: CriterionRequest) -> bool:
    return entry.get("result") == "pass"


def _is_git_ancestor(ancestor: str, descendant: str, cwd: Path) -> bool:
    """True when ancestor == descendant or ancestor is a git ancestor of descendant."""
    if ancestor == descendant:
        return True
    try:
        return Git(cwd).is_ancestor(ancestor, descendant)
    except ToolError as error:
        detail = error.stderr.strip() or str(error)
        raise CloseRefused(
            f"cannot check git ancestry of {ancestor} and {descendant}: {detail}"
        ) from error


def _sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_file_at_revision(cwd: Path, revision: str, relpath: str) -> str:
    """Content hash of ``relpath`` at a store-backed check-run revision."""
    content = Git(cwd).show_bytes(revision, relpath)
    if content is None:
        raise FileNotFoundError(relpath)
    return _sha256_digest(content)


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
    payload = planning_payload(record)

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
    if entry_has(entry, "runner"):
        _match_field(
            criterion_id=criterion_id,
            label="check-run",
            field="runner",
            requested=entry.get("runner"),
            stored=stored_runner,
        )

    if entry_has(entry, "revision"):
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
    payload = planning_payload(record)

    _match_field(
        criterion_id=criterion_id,
        label="red check-run",
        field="criterion_id",
        requested=criterion_id,
        stored=payload.get("criterion_id"),
    )

    if entry_has(entry, "red_result"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="result",
            requested=entry.get("red_result"),
            stored=payload.get("result"),
        )
    if entry_has(entry, "red_runner"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="runner",
            requested=entry.get("red_runner"),
            stored=payload.get("runner"),
        )
    if entry_has(entry, "red_revision"):
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="revision",
            requested=entry.get("red_revision"),
            stored=payload.get("revision"),
        )
    if entry_has(entry, "red_diff_sha256"):
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
    if not entry_has(entry, "revision"):
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


def assertion_level_red(record: Record) -> bool:
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
        payload = planning_payload(record)
        if str(payload.get("status") or "") != "approved":
            continue
        try:
            new_hashes = parse_hashes(payload.get("new_hashes"))
        except ValueError as exc:
            raise CloseRefused(
                f"approved oracle-amendment {record['id']!r} has invalid new_hashes: {exc}"
            ) from exc
        if new_hashes and new_hashes == tree_hashes:
            return True
    return False


def _manifest_claim_ids(cwd: Path) -> set[str]:
    """Return valid claim ids from the repository manifest."""
    path = cwd / ".tuner" / "manifest.json"
    if not path.is_file():
        raise CloseRefused("claim manifest is missing")
    try:
        data: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CloseRefused(f"claim manifest is unreadable or invalid: {exc}") from exc
    claims = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claims, list):
        raise CloseRefused("claim manifest is invalid: claims must be a list")
    ids: set[str] = set()
    for claim in claims:
        if not _is_object(claim):
            raise CloseRefused("claim manifest is invalid: each claim needs a string id")
        raw_claim_id = claim.get("id")
        if not isinstance(raw_claim_id, str):
            raise CloseRefused("claim manifest is invalid: each claim needs a string id")
        claim_id = raw_claim_id.strip()
        if not claim_id or claim_id in ids:
            raise CloseRefused("claim manifest is invalid: claim ids must be non-empty and unique")
        ids.add(claim_id)
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
    claim_ids: set[str] | None = None
    for entry in criteria:
        criterion_id = entry.get("criterion_id")
        acceptance = acceptances[entry["criterion_id"]]
        payload = planning_payload(acceptance)
        claim_id = str(payload.get("claim") or "").strip()
        if not claim_id:
            continue
        if claim_ids is None:
            claim_ids = _manifest_claim_ids(cwd)
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
    red_record: Record | None,
    cwd: Path,
    acceptance: Record,
    list_oracle_amendments: AmendmentLister,
) -> None:
    criterion_id = entry["criterion_id"]
    try:
        acceptance_payload = planning_payload(acceptance)
        frozen = parse_freeze(acceptance_payload)
    except ValueError as exc:
        raise CloseRefused(f"criterion {criterion_id!r}: incomplete oracle freeze: {exc}") from exc

    if entry["method"] == "tdd":
        if red_record is None:
            raise CloseRefused(f"criterion {criterion_id!r}: frozen tdd requires red evidence")
        try:
            assertion_red = assertion_level_red(red_record)
        except OracleAdapterUnavailable as exc:
            raise CloseRefused(f"criterion {criterion_id!r}: {exc}") from exc
        if not assertion_red:
            raise CloseRefused(
                f"criterion {criterion_id!r}: oracle-backed tdd requires "
                "assertion-level red (fail with assertion failure); "
                "import/collection-only red is refused"
            )

        failing_nodes = planning_payload(red_record).get("failing_node_ids")
        test_ids = planning_payload(acceptance).get("test_ids") or []
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


def project_records(project: Project) -> CloseRecords:
    def check_run(check_run_id: str) -> Record:
        try:
            return project.get(check_run_id, "tuner:check-run")
        except StoreError as exc:
            raise LookupError(str(exc)) from exc

    def acceptance(acceptance_id: str) -> Record:
        try:
            return project.get(acceptance_id, "score:acceptance")
        except StoreError as exc:
            raise LookupError(str(exc)) from exc

    def phase(slug: str) -> Record:
        record = current_phase(slug, project.list("score:phase"))
        if record is None:
            raise LookupError(f"phase {slug!r} not found")
        return record

    def amendments(acceptance_id: str) -> list[Record]:
        refs = {acceptance_id}
        with contextlib.suppress(StoreError):
            refs.add(str(project.get(acceptance_id, "score:acceptance")["subject"]))
        return [
            record
            for record in project.list("tuner:oracle-amendment")
            if record.get("lifecycle_state") in (None, "active")
            and str(planning_payload(record).get("acceptance")) in refs
        ]

    return CloseRecords(check_run, acceptance, phase, amendments)


def _oracle_policy(records: CloseRecords, acceptance: Record) -> OraclePolicy:
    payload = planning_payload(acceptance)
    phase_payload = None
    phase = payload.get("phase")
    if (
        "oracle_policy" not in payload
        and "test_ids" not in payload
        and "oracle_hashes" not in payload
        and isinstance(phase, str)
        and phase
    ):
        try:
            phase_payload = planning_payload(records.phase(phase))
        except (LookupError, StoreBindingError, StoreError, OSError) as exc:
            raise CloseRefused(f"phase {phase!r} policy unavailable: {exc}") from exc
    try:
        return resolve_oracle_policy(payload, phase_payload)
    except ValueError as exc:
        raise CloseRefused(
            f"criterion {acceptance['id']!r}: incomplete oracle freeze or invalid policy: {exc}"
        ) from exc


def _enforce_close_gates(
    records: CloseRecords,
    criteria: Sequence[CriterionRequest],
    *,
    acceptance_ids: Sequence[str],
    cwd: Path,
    transition: str,
    has_finding: bool,
) -> None:
    if transition != "done":
        return
    acceptances: dict[str, Record] = {}
    for aid in acceptance_ids:
        try:
            acceptances[aid] = records.acceptance(aid)
        except (LookupError, StoreBindingError, StoreError, OSError) as exc:
            raise CloseRefused(f"criterion {aid!r}: acceptance could not be loaded: {exc}") from exc
    policies = {aid: _oracle_policy(records, acceptance) for aid, acceptance in acceptances.items()}
    passed_ids = {entry["criterion_id"] for entry in criteria if _entry_passed(entry)}
    for aid, acceptance in acceptances.items():
        if planning_payload(acceptance).get("method") == "tdd" and aid not in passed_ids:
            raise CloseRefused(f"criterion {aid!r}: TDD close requires a passing criterion")
    green_by_criterion: dict[JsonValue, Mapping[str, object]] = {}
    for entry in criteria:
        aid = entry["criterion_id"]
        _match_field(
            criterion_id=aid,
            label="acceptance",
            field="method",
            requested=entry["method"],
            stored=planning_payload(acceptances[aid]).get("method"),
        )
        if entry.get("method") not in RUNNER_METHODS:
            continue
        green_by_criterion[entry.get("criterion_id")] = _resolve_green_check_run(
            entry, loader=records.check_run
        )
    _enforce_claim_gates(
        list(criteria),
        green_by_criterion=green_by_criterion,
        cwd=cwd,
        acceptances=acceptances,
    )

    for entry in criteria:
        if not _entry_passed(entry) or entry.get("method") not in RUNNER_METHODS:
            continue
        green_payload = green_by_criterion[entry["criterion_id"]]
        red_record = None
        if entry["method"] == "tdd":
            red_record, red_payload = _resolve_red_check_run(entry, loader=records.check_run)
            _enforce_red_first_from_store(
                entry,
                green_payload=green_payload,
                red_payload=red_payload,
                cwd=cwd,
            )
        if policies[entry["criterion_id"]] == "frozen":
            _enforce_oracle_gates(
                entry,
                green_payload=green_payload,
                red_record=red_record,
                cwd=cwd,
                acceptance=acceptances[entry["criterion_id"]],
                list_oracle_amendments=records.amendments,
            )

    unmet = [aid for aid in acceptance_ids if aid not in passed_ids]
    if unmet and not has_finding:
        raise CloseRefused(
            "closing to done with unmet or unverified criterion(s) "
            f"{unmet} and no finding -- refusing. Either resolve those "
            "criteria first, or supply `finding` (claim, basis, "
            "invalidated_when, body) to close anyway."
        )


def decide_close_with(
    records: CloseRecords,
    criteria: Sequence[CriterionRequest],
    *,
    acceptance_ids: Sequence[str],
    cwd: Path,
    transition: str = "done",
    has_finding: bool = False,
) -> CloseDecision:
    try:
        _enforce_close_gates(
            records,
            criteria,
            acceptance_ids=acceptance_ids,
            cwd=cwd,
            transition=transition,
            has_finding=has_finding,
        )
    except CloseRefused as exc:
        return CloseRefusal(str(exc))
    return CloseApproval()


def decide_close(
    project: Project,
    criteria: Sequence[CriterionRequest],
    *,
    acceptance_ids: Sequence[str],
    cwd: Path,
    transition: str = "done",
    has_finding: bool = False,
) -> CloseDecision:
    return decide_close_with(
        project_records(project),
        criteria,
        acceptance_ids=acceptance_ids,
        cwd=cwd,
        transition=transition,
        has_finding=has_finding,
    )


@dataclass(frozen=True)
class Closure:
    state: str
    code: int
    reasons: tuple[str, ...]
    question_id: str = ""


def _earlier_red_id(project: Project, criterion: str, green: Record) -> str:
    earlier = [
        r
        for r in project.list("tuner:check-run")
        if record_payload(r).get("criterion_id") == criterion
        and record_payload(r).get("result") == "fail"
        and r["id"] != green["id"]
        and r["recorded_at"] <= green["recorded_at"]
    ]
    return max(earlier, key=lambda r: r["recorded_at"])["id"] if earlier else ""


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _criterion_request(project: Project, check: land_task.CheckResult) -> CriterionRequest:
    acceptance = project.get(check.acceptance_id, "score:acceptance")
    green = project.get(check.check_run_id, "tuner:check-run")
    method = record_payload(acceptance).get("method")
    green_payload = record_payload(green)
    provided = ["criterion_id", "method", "result"]
    request: CriterionRequest = {
        "criterion_id": check.acceptance_id,
        "method": method if isinstance(method, str) else None,
        "result": _text(green_payload.get("result")),
        "revision": "",
        "signed_by": "",
        "check_run_id": "",
        "red_check_run_id": "",
        "red_result": "",
        "red_runner": "",
        "red_revision": "",
        "red_diff_sha256": "",
        "red_body": "",
        "red_failing_node_ids": "",
        "runner": "",
        "_provided_fields": provided,
    }
    if method == "manual":
        request["revision"] = _text(green_payload.get("revision"))
        request["signed_by"] = _text(green_payload.get("signed_by"))
        provided += ["revision", "signed_by"]
        return request
    request["check_run_id"] = check.check_run_id
    provided.append("check_run_id")
    red = _earlier_red_id(project, check.acceptance_id, green)
    if method == "tdd" and red:
        request["red_check_run_id"] = red
        request["revision"] = _text(green_payload.get("revision"))
        provided += ["red_check_run_id", "revision"]
    return request


def close(
    project: Project,
    landed: land_task.LandedTask,
    verified: frozenset[str],
    *,
    verification: VerificationRun | None = None,
) -> Closure:
    item = land_task.work_item(project, landed.task)
    tree = Path(str(record_payload(item).get("write_root") or project.project_root))
    if wave.is_closing_task(project.records(), landed.phase, item):
        from orchestra.conductor.verification import run_closing_checks

        result = verification if verification is not None else run_closing_checks(project, landed)
        if result.refusal:
            return Closure("in_progress", CODE_FAILED, (result.refusal,))
        landed = replace(landed, checks=result.checks)
        verified = verified | result.verified
    reasons: list[str] = []
    failed = False
    pending = False
    question_id = ""

    if landed.evidence_result != "pass":
        reasons.append(f"evidence result is {landed.evidence_result}")
        failed = True
    if landed.needs_human:
        question = wave.block(project, landed.phase, f"human:{landed.task}")
        question_id = question["id"]
        reasons.append("the executor reported needs_human; record and resolve the decision")
        pending = True
    elif landed.verdict != "pass":
        reasons.append(f"evidence verdict is {landed.verdict}, not pass")
        failed = True
    for check in landed.checks:
        if check.exit_code == MANUAL_EXIT:
            reasons.append(f"{check.subject}: manual acceptance needs a human sign-off")
            pending = True
        elif check.exit_code != 0:
            reasons.append(f"{check.subject}: {check.message or 'check failed'}")
            failed = True

    wanted = record_payload(item).get("requirements")
    required = [r for r in wanted if isinstance(r, str)] if isinstance(wanted, list) else []
    if not landed.checks and not required:
        reasons.append("no acceptance check ran and the task names no requirement")
        failed = True
    if not failed and not pending:
        unverified = [r for r in required if r not in verified]
        if unverified:
            reasons.append(f"requirements not verified: {', '.join(unverified)}")
            failed = True
    if not failed and not pending and landed.checks:
        decision = decide_close(
            project,
            [_criterion_request(project, check) for check in landed.checks],
            acceptance_ids=[check.acceptance_id for check in landed.checks],
            cwd=tree,
        )
        if isinstance(decision, CloseRefusal):
            reasons.append(decision.reason)
            failed = True

    if failed or pending:
        return Closure(
            "in_progress",
            CODE_FAILED if failed else CODE_PENDING_HUMAN,
            tuple(reasons),
            question_id,
        )
    project.update(item["id"], record_type="score:work-item", transition="done")
    return Closure("done", CODE_DONE, (), question_id)
