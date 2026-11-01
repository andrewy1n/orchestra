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
store's revisions (or a dirty red with `diff_sha256`), unless the
request includes a finding escape.

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
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from orchestra.canon.errors import StoreError
from orchestra.canon.git_backend import run_git
from orchestra.canon.project import open_store
from orchestra.canon.types import Record
from orchestra.conductor.model_types import PlanningPayload
from orchestra.conductor.model_types import planning_payload as record_payload

RUNNER_METHODS = frozenset({"tdd", "check"})
RUNNER_MARKER = "orchestra"
_HASH_SEP = ":sha256:"

CheckRunLoader = Callable[[str], Record]
AcceptanceLoader = Callable[[str], Record]
AmendmentLister = Callable[[str], list[Record]]


class CloseRequestError(Exception):
    """Malformed close-request -- exit 1, distinct from a policy refusal."""


class CloseRefused(Exception):
    """Policy refusal -- exit 2, distinct from a malformed request."""


class OracleAdapterUnavailable(Exception):
    """Oracle-backed close needs the tuner library.

    An installed Orchestra CLI serves every other subcommand without tuner
    importable; this gate refuses clearly when the import fails.
    """


class AcceptanceStoreUnavailable(LookupError):
    """No acceptance store in the unit-test hook.

    ``build_batch`` callers that inject ``load_check_run`` without a store get
    this sentinel instead of a real lookup failure, so the claim gate can skip
    rather than refuse a close the test did not mean to gate.
    """


def _entry_passed(entry: dict[str, Any]) -> bool:
    return entry.get("result") == "pass"


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
    except StoreError as exc:
        raise LookupError(str(exc)) from exc


def default_load_acceptance(
    acceptance_id: str,
    *,
    store_root: Path | None = None,
) -> Record:
    """Load an acceptance from the store opened for the primary cwd."""
    try:
        return _open_project(store_root).get(acceptance_id, "score:acceptance")
    except StoreError as exc:
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
        if not isinstance(record, dict):
            continue
        if record.get("lifecycle_state") not in (None, "active"):
            continue
        if str(record_payload(record).get("acceptance")) in refs:
            matched.append(record)
    return matched


def parse_oracle_hashes(raw: list[str] | str | None) -> dict[str, str]:
    """Parse ``relpath:sha256:<hex>`` entries into ``{relpath: sha256:<hex>}``."""
    if not raw:
        return {}
    parts = raw.split(",") if isinstance(raw, str) else list(raw)
    out: dict[str, str] = {}
    for part in parts:
        chunk = str(part).strip()
        if not chunk:
            continue
        idx = chunk.find(_HASH_SEP)
        if idx <= 0:
            continue
        relpath = chunk[:idx]
        digest = chunk[idx + 1 :]  # keep leading "sha256:"
        if relpath and digest.startswith("sha256:"):
            out[relpath] = digest
    return out


def is_oracle_backed(acceptance_payload: Mapping[str, Any]) -> bool:
    """True when acceptance has freeze fields: non-empty test_ids and parseable hashes.

    ``oracle_hashes`` must parse to at least one ``relpath:sha256:<hex>`` entry.
    Placeholder or unparseable strings are treated as legacy (gates skipped).
    """
    if not acceptance_payload.get("test_ids"):
        return False
    return bool(parse_oracle_hashes(acceptance_payload.get("oracle_hashes")))


def _sha256_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def hash_file_at_revision(cwd: Path, revision: str, relpath: str) -> str:
    """Content hash of ``relpath`` at a store-backed check-run revision."""
    if revision == "dirty":
        path = cwd / relpath
        if not path.is_file():
            raise FileNotFoundError(relpath)
        return _sha256_digest(path.read_bytes())
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
    criterion_id: Any,
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
    criterion_id: Any,
    label: str,
    field: str,
    requested: Any,
    stored: Any,
) -> None:
    if requested != stored:
        raise CloseRefused(
            f"criterion {criterion_id!r}: {label} {field} mismatch "
            f"(request={requested!r}, store={stored!r})"
        )


def _resolve_green_check_run(
    entry: dict[str, Any],
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
    if "runner" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="check-run",
            field="runner",
            requested=entry.get("runner"),
            stored=stored_runner,
        )

    if "revision" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="check-run",
            field="revision",
            requested=entry.get("revision"),
            stored=payload.get("revision"),
        )

    return payload


def _resolve_red_check_run(
    entry: dict[str, Any],
    *,
    loader: CheckRunLoader,
) -> tuple[Record, PlanningPayload]:
    """Load and match the red check-run; return (full record, payload)."""
    criterion_id = entry.get("criterion_id")
    red_id = entry.get("red_check_run_id")
    if not red_id:
        raise CloseRefused(
            f"criterion {criterion_id!r}: tdd done close requires "
            "red_check_run_id (runner-produced fail preceding the green), "
            "or a finding escape naming the missing red"
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

    if "red_result" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="result",
            requested=entry.get("red_result"),
            stored=payload.get("result"),
        )
    if "red_runner" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="runner",
            requested=entry.get("red_runner"),
            stored=payload.get("runner"),
        )
    if "red_revision" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="revision",
            requested=entry.get("red_revision"),
            stored=payload.get("revision"),
        )
    if "red_diff_sha256" in entry:
        _match_field(
            criterion_id=criterion_id,
            label="red check-run",
            field="diff_sha256",
            requested=entry.get("red_diff_sha256"),
            stored=payload.get("diff_sha256"),
        )

    return record, payload


def _enforce_red_first_from_store(
    entry: dict[str, Any],
    *,
    green_payload: Mapping[str, Any],
    red_payload: Mapping[str, Any],
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
    if "revision" not in entry:
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

    if not _is_git_ancestor(red_revision, green_revision, cwd):
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision is not equal to or "
            f"a git descendant of red revision "
            f"(red={red_revision}, green={green_revision})"
        )


def _assertion_level_red(record: Mapping[str, Any]) -> bool:
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
        new_hashes = parse_oracle_hashes(payload.get("new_hashes"))
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
        data = json.loads(path.read_text(encoding="utf-8"))
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
        if not isinstance(verdict, dict) or verdict.get("result") != "pass":
            failed.append("verdict")
    try:
        outcome = recheck(cwd, claim_id)
    except Exception as exc:
        failed.append("recheck")
        details.append(f"recheck: {exc}")
    else:
        if not isinstance(outcome, dict) or outcome.get("result") != "pass":
            failed.append("recheck")
    if failed:
        clocks = " and ".join(failed)
        suffix = f" ({'; '.join(details)})" if details else ""
        raise CloseRefused(
            f"tuner {clocks} refused for claim {claim_id!r} at revision {revision!r}{suffix}"
        )


def _enforce_claim_gates(
    criteria: list[dict[str, Any]],
    *,
    green_by_criterion: dict[Any, Mapping[str, Any]],
    cwd: Path,
    load_acceptance: AcceptanceLoader,
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
        try:
            acceptance = load_acceptance(str(criterion_id))
        except AcceptanceStoreUnavailable:
            continue
        except LookupError as exc:
            raise CloseRefused(
                f"criterion {criterion_id!r}: acceptance could not be "
                "loaded; cannot run the claim gate"
            ) from exc
        payload = record_payload(acceptance)
        claim_id = str(payload.get("claim") or "").strip()
        if not claim_id:
            continue
        if claim_id not in claim_ids:
            raise CloseRefused(
                f"criterion {criterion_id!r}: claim {claim_id!r} is not "
                "listed in .tuner/manifest.json"
            )
        revision: Any = None
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
    entry: dict[str, Any],
    *,
    green_payload: Mapping[str, Any],
    red_record: Mapping[str, Any],
    cwd: Path,
    load_acceptance: AcceptanceLoader,
    list_oracle_amendments: AmendmentLister,
) -> None:
    """Refuse oracle-backed tdd done on hash drift or non-assertion red.

    Legacy acceptances without freeze fields skip these gates.
    """
    criterion_id = entry.get("criterion_id")
    try:
        acceptance = load_acceptance(str(criterion_id))
    except LookupError:
        return

    acceptance_payload = record_payload(acceptance)
    if not is_oracle_backed(acceptance_payload):
        return

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

    frozen = parse_oracle_hashes(acceptance_payload.get("oracle_hashes"))
    if not frozen:
        raise CloseRefused(
            f"criterion {criterion_id!r}: oracle_hashes freeze field is empty or unparseable"
        )

    green_revision = green_payload.get("revision")
    if not green_revision:
        raise CloseRefused(
            f"criterion {criterion_id!r}: green revision required for oracle freeze hash check"
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
    request: dict[str, Any],
    *,
    cwd: str | Path | None = None,
    store_root: str | Path | None = None,
    load_check_run: CheckRunLoader | None = None,
    load_acceptance: AcceptanceLoader | None = None,
    list_oracle_amendments: AmendmentLister | None = None,
) -> list[dict[str, Any]]:
    try:
        subject = request["subject"]
        effort = request["effort"]
        work_item_id = request["work_item_id"]
        transition = request["transition"]
        acceptance_ids = list(request["acceptance_ids"])
        criteria = list(request.get("criteria", []))
    except KeyError as exc:
        raise CloseRequestError(f"missing field: {exc}") from exc

    execution_report_id = request.get("execution_report_id")
    finding = request.get("finding")
    work_cwd = Path(cwd) if cwd is not None else Path.cwd()
    resolved_store = Path(store_root) if store_root is not None else None

    loader: CheckRunLoader
    if load_check_run is not None:
        loader = load_check_run
    else:

        def _store_check_run(check_run_id: str) -> Record:
            return default_load_check_run(check_run_id, store_root=resolved_store)

        loader = _store_check_run

    # Unit tests inject load_check_run without a store: skip oracle store
    # lookups unless the caller also injects acceptance/amendment hooks.
    acceptance_loader: AcceptanceLoader
    if load_acceptance is not None:
        acceptance_loader = load_acceptance
    elif load_check_run is None:

        def _store_acceptance(acceptance_id: str) -> Record:
            return default_load_acceptance(acceptance_id, store_root=resolved_store)

        acceptance_loader = _store_acceptance
    else:

        def _unavailable_acceptance(_acceptance_id: str) -> Record:
            raise AcceptanceStoreUnavailable("acceptance store not available in unit test hook")

        acceptance_loader = _unavailable_acceptance

    amendment_lister: AmendmentLister
    if list_oracle_amendments is not None:
        amendment_lister = list_oracle_amendments
    elif load_check_run is None:

        def _store_amendments(acceptance_id: str) -> list[Record]:
            return default_list_oracle_amendments(acceptance_id, store_root=resolved_store)

        amendment_lister = _store_amendments
    else:

        def _no_amendments(_acceptance_id: str) -> list[Record]:
            return []

        amendment_lister = _no_amendments

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
            if "result" not in entry:
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "copy result from the runner check-run"
                )
            # Invented create shape: signed_by without going through the
            # runner — refuse. For tdd, revision may be copied only when
            # red-first fields are present; for check it remains forbidden.
            if "signed_by" in entry:
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "not carry signed_by; reference check_run_id only"
                )
            if method == "check" and "revision" in entry:
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method={method!r} must "
                    "not carry revision/signed_by; reference check_run_id only"
                )
            if method == "tdd" and "revision" in entry and not entry.get("red_check_run_id"):
                raise CloseRequestError(
                    f"criteria entry {criterion_id!r} method=tdd must not "
                    "carry revision without red-first fields "
                    "(red_check_run_id); reference check_run_id only or "
                    "include red evidence"
                )
        elif method == "manual":
            for field in ("result", "revision"):
                if field not in entry:
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
    green_by_criterion: dict[Any, Mapping[str, Any]] = {}
    if transition == "done":
        for entry in criteria:
            if entry.get("method") not in RUNNER_METHODS:
                continue
            green_by_criterion[entry.get("criterion_id")] = _resolve_green_check_run(
                entry, loader=loader
            )
        _enforce_claim_gates(
            criteria,
            green_by_criterion=green_by_criterion,
            cwd=work_cwd,
            load_acceptance=acceptance_loader,
        )

    if transition == "done" and not finding:
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
                load_acceptance=acceptance_loader,
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

    ops: list[dict[str, Any]] = []
    for entry in criteria:
        method = entry["method"]
        if method in RUNNER_METHODS:
            # Runner already wrote the check-run; do not invent another.
            continue
        payload = {
            "criterion_id": entry["criterion_id"],
            "revision": entry["revision"],
            "result": entry["result"],
            "effort": effort,
            "method": method,
            "signed_by": entry.get("signed_by", ""),
        }
        informed_by = [entry["criterion_id"]]
        if execution_report_id:
            informed_by.append(execution_report_id)
        payload["informed_by"] = informed_by
        ops.append(
            {
                "op": "create",
                "type": "tuner:check-run",
                "subject": subject,
                "payload": payload,
            }
        )

    if finding:
        try:
            finding_payload = {
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
            {
                "op": "create",
                "type": "tuner:finding",
                "subject": subject,
                "payload": finding_payload,
                "body": finding_body,
            }
        )

    ops.append(
        {
            "op": "update",
            "type": "score:work-item",
            "id": work_item_id,
            "transition": transition,
            "expected_revision": "@current",
        }
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
