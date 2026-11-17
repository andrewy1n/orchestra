from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from canon_support import create, make_project
from phase_record_support import supersede_all, supersede_late

from orchestra.canon.project import Project
from orchestra.canon.types import JsonObject, Record
from orchestra.conductor.task_close import (
    CloseApproval,
    CloseDecision,
    CloseRefusal,
    CriterionRequest,
    decide_close,
)
from orchestra.tools import Git
from orchestra.tuner.manifest import DEFAULT_RUNNER

EFFORT = "ef"
PHASE = "ph"
CLAIM = "claim-widget"
ORACLE_REL = "tests/test_probe.py"
NODE = f"{ORACLE_REL}::test_probe"
ORACLE_V1 = b"def test_probe():\n    assert 1 == 2\n"
ORACLE_V2 = b"def test_probe():\n    assert 2 == 2\n"
RED_BODY = f"FAILED {NODE} - AssertionError\nE   assert 1 == 2\n"
IMPORT_RED_BODY = f"ERROR {NODE} - ImportError: no module named probe\n"
DIGEST = "a" * 64


def _sha(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _commit(git: Git, root: Path, relpath: str, content: bytes, message: str) -> str:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    git.run("add", relpath)
    result = git.run(
        "-c",
        "user.email=t@example.com",
        "-c",
        "user.name=t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
    )
    assert result.returncode == 0, result.stderr
    return git.head()


@dataclass
class Scenario:
    project: Project
    root: Path
    git: Git
    method: str
    acceptance: Record
    green: Record
    red: Record | None
    red_sha: str
    green_sha: str

    @property
    def aid(self) -> str:
        return self.acceptance["id"]


def _seeded_project(root: Path, phase: JsonObject | None = None) -> Project:
    project = make_project(root)
    create(project, "score:effort", EFFORT, {"goal": "g", "kind": "deliver"})
    payload: JsonObject = {"title": "Ph", "ordinal": 1, "effort": EFFORT}
    payload.update(phase or {})
    create(project, "score:phase", PHASE, payload)
    return project


def _check_run(
    project: Project, criterion: str, method: str, over: JsonObject, body: str = ""
) -> Record:
    payload: JsonObject = {
        "criterion_id": criterion,
        "result": "pass",
        "effort": EFFORT,
        "method": method,
        "signed_by": "",
        "runner": "orchestra",
    }
    payload.update(over)
    return project.create(record_type="tuner:check-run", subject="task", payload=payload, body=body)


def _scenario(
    tmp_path: Path,
    *,
    method: str = "tdd",
    frozen: bool = True,
    green_content: bytes = ORACLE_V1,
    acceptance: JsonObject | None = None,
    green: JsonObject | None = None,
    red: JsonObject | None = None,
    red_body: str = RED_BODY,
    phase: JsonObject | None = None,
) -> Scenario:
    project = _seeded_project(tmp_path / "store", phase)
    root = tmp_path / "work"
    root.mkdir()
    git = Git(root)
    git.run("init", "-q")
    red_sha = _commit(git, root, ORACLE_REL, ORACLE_V1, "red")
    green_sha = _commit(git, root, ORACLE_REL, green_content, "green")
    payload: JsonObject = {"method": method, "effort": EFFORT, "verify_command": "true"}
    if frozen:
        payload["test_ids"] = [NODE]
        payload["oracle_hashes"] = [f"{ORACLE_REL}:{_sha(ORACLE_V1)}"]
    payload.update(acceptance or {})
    acc = create(project, "score:acceptance", "criterion", payload)
    green_run = _check_run(project, acc["id"], method, {"revision": green_sha, **(green or {})})
    red_run: Record | None = None
    if method == "tdd":
        red_run = _check_run(
            project,
            acc["id"],
            method,
            {"revision": red_sha, "result": "fail", "failing_node_ids": [NODE], **(red or {})},
            red_body,
        )
    return Scenario(project, root, git, method, acc, green_run, red_run, red_sha, green_sha)


def _typed(values: dict[str, str | None]) -> CriterionRequest:
    def text(key: str) -> str:
        return values.get(key) or ""

    return {
        "criterion_id": text("criterion_id"),
        "method": values.get("method"),
        "result": text("result"),
        "revision": text("revision"),
        "signed_by": text("signed_by"),
        "check_run_id": text("check_run_id"),
        "red_check_run_id": text("red_check_run_id"),
        "red_result": text("red_result"),
        "red_runner": text("red_runner"),
        "red_revision": text("red_revision"),
        "red_diff_sha256": text("red_diff_sha256"),
        "red_body": text("red_body"),
        "red_failing_node_ids": text("red_failing_node_ids"),
        "runner": text("runner"),
        "_provided_fields": [key for key, value in values.items() if value is not None],
    }


def _entry(s: Scenario, **over: str | None) -> CriterionRequest:
    values: dict[str, str | None] = {
        "criterion_id": s.aid,
        "method": s.method,
        "result": "pass",
        "check_run_id": s.green["id"],
        "revision": s.green_sha,
    }
    if s.red is not None:
        values["red_check_run_id"] = s.red["id"]
        values["red_result"] = "fail"
        values["red_revision"] = s.red_sha
    values.update(over)
    return _typed(values)


def _decide(
    s: Scenario,
    *entries: CriterionRequest,
    ids: list[str] | None = None,
    transition: str = "done",
    has_finding: bool = False,
    project: Project | None = None,
) -> CloseDecision:
    return decide_close(
        project if project is not None else s.project,
        list(entries) or [_entry(s)],
        acceptance_ids=ids if ids is not None else [s.aid],
        cwd=s.root,
        transition=transition,
        has_finding=has_finding,
    )


def _reason(decision: CloseDecision) -> str:
    assert isinstance(decision, CloseRefusal), decision
    return decision.reason


def _approved(decision: CloseDecision) -> None:
    assert isinstance(decision, CloseApproval), decision


def _head_revision(s: Scenario, relpath: str, content: bytes, message: str) -> str:
    return _commit(s.git, s.root, relpath, content, message)


_CONFIG_TOML = (
    f'[verify.stages]\nphase = ["unit"]\n\n[verify.unit]\nrunner = {json.dumps(DEFAULT_RUNNER)}\n'
)


def _commit_manifest_text(s: Scenario, text: str) -> None:
    _commit(s.git, s.root, "orchestra.toml", _CONFIG_TOML.encode(), "config")
    sha = _commit(s.git, s.root, ".tuner/manifest.json", text.encode(), "manifest")
    s.green = _check_run(s.project, s.aid, s.method, {"revision": sha})
    s.green_sha = sha


def _claim(claim_id: str) -> JsonObject:
    return {"id": claim_id, "text": "t", "tests": [NODE], "oracle_hashes": {}}


def _write_manifest(s: Scenario, claims: object) -> None:
    _commit_manifest_text(s, json.dumps({"claims": claims}))


def _tuner_outcomes(monkeypatch: pytest.MonkeyPatch, verdict: str, recheck: str) -> None:
    monkeypatch.setattr("orchestra.tuner.verdict.run_verdict", lambda *_a: {"result": verdict})
    monkeypatch.setattr("orchestra.tuner.binding.recheck", lambda *_a: {"result": recheck})


def _check_scenario(
    tmp_path: Path, *, acceptance: JsonObject | None = None, green: JsonObject | None = None
) -> Scenario:
    return _scenario(tmp_path, method="check", frozen=False, acceptance=acceptance, green=green)


def test_r1_refuses_tdd_criterion_naming_no_check_run(tmp_path: Path) -> None:
    s = _scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, check_run_id=None)))

    assert (
        reason == f"criterion {s.aid!r}: check_run_id check_run_id '' not found in artifact store"
    )


def test_r1_refuses_check_criterion_naming_no_check_run(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, check_run_id=None)))

    assert (
        reason == f"criterion {s.aid!r}: check_run_id check_run_id '' not found in artifact store"
    )


def test_r1_refuses_check_run_the_runner_did_not_produce(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path, green={"runner": "hand"})

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: check-run is not runner-produced "
        "(runner must be 'orchestra', got 'hand')"
    )


def test_r1_passes_check_criterion_with_runner_check_run(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    _approved(_decide(s))


def test_r2_refuses_check_run_missing_from_store(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, check_run_id="rec-ghost")))

    assert reason == (
        f"criterion {s.aid!r}: check_run_id check_run_id 'rec-ghost' not found in artifact store"
    )


def test_r2_refuses_check_run_of_another_criterion(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path, green={"criterion_id": "rec-other"})

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: check-run criterion_id mismatch "
        f"(request={s.aid!r}, store='rec-other')"
    )


def test_r2_refuses_stated_result_that_differs_from_store(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, result="fail"), ids=[s.aid]))

    assert reason == (
        f"criterion {s.aid!r}: check-run result mismatch (request='fail', store='pass')"
    )


def test_r2_refuses_stated_revision_that_differs_from_store(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, revision="deadbeef")))

    assert reason == (
        f"criterion {s.aid!r}: check-run revision mismatch "
        f"(request='deadbeef', store={s.green_sha!r})"
    )


def test_r2_refuses_stated_runner_that_differs_from_store(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, runner="other")))

    assert reason == (
        f"criterion {s.aid!r}: check-run runner mismatch (request='other', store='orchestra')"
    )


def test_r2_refuses_stated_method_that_differs_from_acceptance(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, _entry(s, method="tdd")))

    assert reason == (
        f"criterion {s.aid!r}: acceptance method mismatch (request='tdd', store='check')"
    )


def test_r2_refuses_acceptance_missing_from_store(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    reason = _reason(_decide(s, ids=["rec-ghost"]))

    assert reason.startswith("criterion 'rec-ghost': acceptance could not be loaded: ")


@pytest.mark.parametrize(
    ("red_over", "entry_over", "expected"),
    [
        (
            {"criterion_id": "rec-other"},
            {},
            "red check-run criterion_id mismatch (request={aid!r}, store='rec-other')",
        ),
        (
            {"runner": "hand"},
            {"red_runner": "orchestra"},
            "red check-run runner mismatch (request='orchestra', store='hand')",
        ),
        (
            {},
            {"red_result": "pass"},
            "red check-run result mismatch (request='pass', store='fail')",
        ),
        (
            {},
            {"red_revision": "deadbeef"},
            "red check-run revision mismatch (request='deadbeef', store={red_sha!r})",
        ),
        (
            {},
            {"red_diff_sha256": DIGEST},
            "red check-run diff_sha256 mismatch (request='" + DIGEST + "', store=None)",
        ),
    ],
    ids=["criterion", "runner", "result", "revision", "diff"],
)
def test_r2_refuses_red_check_run_that_differs_from_the_request(
    tmp_path: Path, red_over: JsonObject, entry_over: dict[str, str | None], expected: str
) -> None:
    s = _scenario(tmp_path, frozen=False, red=red_over)

    reason = _reason(_decide(s, _entry(s, **entry_over)))

    assert reason == f"criterion {s.aid!r}: " + expected.format(aid=s.aid, red_sha=s.red_sha)


def test_r2_refuses_red_check_run_missing_from_store(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    reason = _reason(_decide(s, _entry(s, red_check_run_id="rec-ghost")))

    assert reason == (
        f"criterion {s.aid!r}: red_check_run_id check_run_id 'rec-ghost' not found in artifact store"
    )


def test_r2_passes_matching_red_and_green_check_runs(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    _approved(_decide(s, _entry(s, red_runner="orchestra", runner="orchestra")))


def test_r3_refuses_tdd_criterion_without_red_check_run(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    reason = _reason(_decide(s, _entry(s, red_check_run_id=None, red_result=None)))

    assert reason == (
        f"criterion {s.aid!r}: tdd done close requires "
        "red_check_run_id (runner-produced fail preceding the green)"
    )


@pytest.mark.parametrize(
    ("red_over", "expected"),
    [
        ({"result": "pass"}, "red evidence result must be 'fail', got 'pass'"),
        (
            {"runner": "hand"},
            "red check-run is not runner-produced (runner must be 'orchestra', got 'hand')",
        ),
        ({"revision": ""}, "red evidence missing revision"),
        ({"revision": "dirty"}, "dirty red requires non-empty diff_sha256"),
    ],
    ids=["red-passes", "red-not-runner", "red-no-revision", "dirty-red-no-digest"],
)
def test_r3_refuses_red_check_run_that_is_not_a_runner_fail(
    tmp_path: Path, red_over: JsonObject, expected: str
) -> None:
    s = _scenario(tmp_path, frozen=False, red=red_over)

    reason = _reason(
        _decide(
            s,
            _entry(s, red_result=None, red_runner=None, red_revision=None),
        )
    )

    assert reason == f"criterion {s.aid!r}: {expected}"


def test_r3_refuses_green_that_is_an_ancestor_of_red(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)
    red = _check_run(s.project, s.aid, "tdd", {"revision": s.green_sha, "result": "fail"})
    green = _check_run(s.project, s.aid, "tdd", {"revision": s.red_sha})

    reason = _reason(
        _decide(
            s,
            _entry(
                s,
                check_run_id=green["id"],
                red_check_run_id=red["id"],
                revision=s.red_sha,
                red_revision=s.green_sha,
            ),
        )
    )

    assert reason == (
        f"criterion {s.aid!r}: green revision is not equal to or "
        f"a git descendant of red revision (red={s.green_sha}, green={s.red_sha})"
    )


def test_r3_refuses_green_on_a_divergent_branch_from_red(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)
    s.git.run("checkout", "-q", "-b", "side", s.red_sha)
    side = _head_revision(s, "side.txt", b"side\n", "side")
    red = _check_run(s.project, s.aid, "tdd", {"revision": side, "result": "fail"})

    reason = _reason(_decide(s, _entry(s, red_check_run_id=red["id"], red_revision=side)))

    assert reason == (
        f"criterion {s.aid!r}: green revision is not equal to or "
        f"a git descendant of red revision (red={side}, green={s.green_sha})"
    )


def test_r3_refuses_red_revision_git_cannot_resolve(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False, red={"revision": "f" * 40})

    reason = _reason(_decide(s, _entry(s, red_revision=None)))

    assert reason.startswith(f"cannot check git ancestry of {'f' * 40} and {s.green_sha}: ")


def test_r3_refuses_sha_red_when_request_omits_green_revision(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    reason = _reason(_decide(s, _entry(s, revision=None)))

    assert reason == (
        f"criterion {s.aid!r}: green revision required for git-ancestry red-first check"
    )


def test_r3_refuses_sha_red_when_store_green_has_no_revision(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False, green={"revision": ""})

    reason = _reason(_decide(s, _entry(s, revision="")))

    assert reason == (
        f"criterion {s.aid!r}: green revision required for git-ancestry red-first check"
    )


def test_r3_refuses_sha_red_when_green_is_dirty(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False, green={"revision": "dirty"})

    reason = _reason(_decide(s, _entry(s, revision="dirty")))

    assert reason == (
        f"criterion {s.aid!r}: cannot verify red-first ordering "
        "when green revision is dirty and red is a SHA"
    )


def test_r3_passes_green_that_descends_from_red(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    _approved(_decide(s))


def test_r3_passes_dirty_red_with_diff_digest(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False, red={"revision": "dirty", "diff_sha256": DIGEST})

    _approved(_decide(s, _entry(s, red_revision=None)))


def test_r4_refuses_red_that_is_not_an_assertion_failure(tmp_path: Path) -> None:
    s = _scenario(tmp_path, red_body=IMPORT_RED_BODY)

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: oracle-backed tdd requires "
        "assertion-level red (fail with assertion failure); "
        "import/collection-only red is refused"
    )


def test_r4_refuses_red_that_names_no_failing_test(tmp_path: Path) -> None:
    s = _scenario(tmp_path, red={"failing_node_ids": []})

    reason = _reason(_decide(s))

    assert "assertion-level red" in reason


def test_r4_refuses_assertion_red_outside_the_frozen_test_ids(tmp_path: Path) -> None:
    other = "tests/test_other.py::test_other"
    s = _scenario(
        tmp_path,
        red={"failing_node_ids": [other]},
        red_body=f"FAILED {other} - AssertionError\nE   assert 1 == 2\n",
    )

    reason = _reason(_decide(s))

    assert reason == f"criterion {s.aid!r}: assertion red must identify frozen test ids"


def test_r4_refuses_when_the_tuner_library_is_not_importable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _scenario(tmp_path)
    monkeypatch.setitem(sys.modules, "orchestra.tuner.oracle_red", None)

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: tuner is not importable; close-batch needs tuner to "
        "classify assertion-level red for oracle-backed acceptances"
    )


def test_r4_passes_assertion_level_red_on_a_frozen_test(tmp_path: Path) -> None:
    s = _scenario(tmp_path)

    _approved(_decide(s))


def test_r5_refuses_freeze_with_hashes_but_no_test_ids(tmp_path: Path) -> None:
    s = _scenario(
        tmp_path, frozen=False, acceptance={"oracle_hashes": [f"{ORACLE_REL}:{_sha(ORACLE_V1)}"]}
    )

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: incomplete oracle freeze or invalid policy: "
        "test_ids must be a non-empty array"
    )


def test_r5_refuses_policy_none_with_freeze_metadata(tmp_path: Path) -> None:
    s = _scenario(tmp_path, acceptance={"oracle_policy": "none"})

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: incomplete oracle freeze or invalid policy: "
        "oracle_policy none conflicts with freeze metadata"
    )


def test_r5_passes_complete_freeze_with_valid_policy(tmp_path: Path) -> None:
    s = _scenario(tmp_path, acceptance={"oracle_policy": "frozen"})

    _approved(_decide(s))


def test_r6_refuses_oracle_file_that_differs_at_the_revision(tmp_path: Path) -> None:
    s = _scenario(tmp_path, green_content=ORACLE_V2)

    reason = _reason(_decide(s))

    assert reason == (
        f"criterion {s.aid!r}: oracle hash drift at green revision "
        f"{s.green_sha!r} without an approved oracle-amendment whose "
        "new_hashes match the tree (freeze hashes are the close authority)"
    )


def test_r6_refuses_requested_amendment_that_is_not_approved(tmp_path: Path) -> None:
    s = _scenario(tmp_path, green_content=ORACLE_V2)
    _amend(s, "requested", [f"{ORACLE_REL}:{_sha(ORACLE_V2)}"])

    assert "oracle hash drift" in _reason(_decide(s))


def test_r6_refuses_approved_amendment_with_invalid_hashes(tmp_path: Path) -> None:
    s = _scenario(tmp_path, green_content=ORACLE_V2)
    amendment = _amend(s, "approved", ["garbage"])

    reason = _reason(_decide(s))

    assert reason.startswith(
        f"approved oracle-amendment {amendment['id']!r} has invalid new_hashes: "
    )


def test_r6_refuses_oracle_file_missing_at_the_revision(tmp_path: Path) -> None:
    s = _scenario(
        tmp_path,
        method="check",
        acceptance={
            "test_ids": ["tests/test_gone.py::test_gone"],
            "oracle_hashes": [f"tests/test_gone.py:{_sha(ORACLE_V1)}"],
        },
    )

    reason = _reason(_decide(s))

    assert reason.startswith(
        f"criterion {s.aid!r}: oracle file missing at green revision {s.green_sha!r}: "
    )


def test_r6_refuses_green_revision_that_is_not_a_pinned_commit(tmp_path: Path) -> None:
    s = _scenario(
        tmp_path,
        green={"revision": "dirty"},
        red={"revision": "dirty", "diff_sha256": DIGEST},
    )

    reason = _reason(_decide(s, _entry(s, revision="dirty", red_revision=None)))

    assert reason == (
        f"criterion {s.aid!r}: green revision must be a pinned commit for the freeze check"
    )


def test_r6_passes_unchanged_oracle_file(tmp_path: Path) -> None:
    s = _scenario(tmp_path)

    _approved(_decide(s))


def test_r6_passes_changed_oracle_file_covered_by_approved_amendment(tmp_path: Path) -> None:
    s = _scenario(tmp_path, green_content=ORACLE_V2)
    _amend(s, "approved", [f"{ORACLE_REL}:{_sha(ORACLE_V2)}"])

    _approved(_decide(s))


def _amend(s: Scenario, status: str, new_hashes: list[str]) -> Record:
    return create(
        s.project,
        "tuner:oracle-amendment",
        "criterion",
        {
            "acceptance": "criterion",
            "effort": EFFORT,
            "phase": PHASE,
            "old_hashes": [f"{ORACLE_REL}:{_sha(ORACLE_V1)}"],
            "new_hashes": list(new_hashes),
            "status": status,
        },
    )


def _claim_scenario(tmp_path: Path) -> Scenario:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    _write_manifest(s, [_claim(CLAIM)])
    return s


def test_r8_refuses_claim_whose_verdict_does_not_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _claim_scenario(tmp_path)
    _tuner_outcomes(monkeypatch, "fail", "pass")

    reason = _reason(_decide(s))

    assert reason == f"tuner verdict refused for claim {CLAIM!r} at revision {s.green_sha!r}"


def test_r8_refuses_claim_whose_recheck_does_not_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _claim_scenario(tmp_path)
    _tuner_outcomes(monkeypatch, "pass", "fail")

    reason = _reason(_decide(s))

    assert reason == f"tuner recheck refused for claim {CLAIM!r} at revision {s.green_sha!r}"


def test_r8_refuses_claim_when_the_tuner_library_is_not_importable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _claim_scenario(tmp_path)
    monkeypatch.setitem(sys.modules, "orchestra.tuner.verdict", None)

    reason = _reason(_decide(s))

    assert reason == (f"tuner is not importable; cannot run verdict or recheck for claim {CLAIM!r}")


def test_r8_refuses_claim_missing_from_the_manifest(tmp_path: Path) -> None:
    s = _claim_scenario(tmp_path)
    _write_manifest(s, [_claim("claim-other")])

    reason = _reason(_decide(s))

    assert reason == (f"criterion {s.aid!r}: claim {CLAIM!r} is not listed in .tuner/manifest.json")


def test_r8_refuses_claim_when_the_manifest_is_missing(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})

    assert _reason(_decide(s)) == "claim manifest is missing"


def test_r8_refuses_claim_when_the_manifest_is_unreadable(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    _commit_manifest_text(s, "{")

    assert _reason(_decide(s)).startswith("claim manifest is unreadable or invalid: ")


@pytest.mark.parametrize(
    ("claims", "expected"),
    [
        ("nope", "claim manifest is invalid: manifest claims must be a list"),
        (["nope"], "claim manifest is invalid: claims[0] is not an object"),
        (
            [{**_claim(CLAIM), "id": 3}],
            "claim manifest is invalid: claims[0].id must be a non-empty string",
        ),
        (
            [_claim(" ")],
            "claim manifest is invalid: claim ids must be non-empty and unique",
        ),
        (
            [_claim(CLAIM), _claim(CLAIM)],
            "claim manifest is invalid: claim ids must be non-empty and unique",
        ),
    ],
    ids=["not-list", "not-object", "id-not-string", "id-blank", "id-duplicate"],
)
def test_r8_refuses_claim_when_the_manifest_is_invalid(
    tmp_path: Path, claims: object, expected: str
) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM})
    _write_manifest(s, claims)

    assert _reason(_decide(s)) == expected


def test_r8_refuses_claim_when_no_close_revision_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _check_scenario(tmp_path, acceptance={"claim": CLAIM}, green={"revision": ""})
    _tuner_outcomes(monkeypatch, "pass", "pass")

    reason = _reason(_decide(s, _entry(s, revision=None)))

    assert reason == (
        f"criterion {s.aid!r}: claim {CLAIM!r} requires a close revision for tuner verdict"
    )


def test_r8_passes_claim_whose_verdict_and_recheck_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _claim_scenario(tmp_path)
    _tuner_outcomes(monkeypatch, "pass", "pass")

    _approved(_decide(s))


def test_r9_refuses_done_with_unmet_criterion_and_no_finding(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)
    unmet = create(
        s.project,
        "score:acceptance",
        "second",
        {"method": "manual", "effort": EFFORT, "verify_command": "true"},
    )

    reason = _reason(_decide(s, ids=[s.aid, unmet["id"]]))

    assert reason == (
        "closing to done with unmet or unverified criterion(s) "
        f"{[unmet['id']]} and no finding -- refusing. Either resolve those "
        "criteria first, or supply `finding` (claim, basis, "
        "invalidated_when, body) to close anyway."
    )


def test_r9_refuses_tdd_criterion_that_did_not_pass(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False)

    reason = _reason(_decide(s, _entry(s, result="fail")))

    assert reason == f"criterion {s.aid!r}: TDD close requires a passing criterion"


def test_r9_passes_unmet_criterion_with_a_finding(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)
    unmet = create(
        s.project,
        "score:acceptance",
        "second",
        {"method": "manual", "effort": EFFORT, "verify_command": "true"},
    )

    _approved(_decide(s, ids=[s.aid, unmet["id"]], has_finding=True))


def test_r9_passes_unmet_criterion_when_the_transition_is_not_done(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)

    _approved(_decide(s, ids=[s.aid, "rec-unchecked"], transition="in_progress"))


def test_r10_approves_a_frozen_tdd_request_that_passes_every_gate(tmp_path: Path) -> None:
    s = _scenario(tmp_path)

    _approved(_decide(s))


def test_r10_approves_a_manual_criterion(tmp_path: Path) -> None:
    s = _check_scenario(tmp_path)
    manual = create(
        s.project,
        "score:acceptance",
        "manual",
        {"method": "manual", "effort": EFFORT, "verify_command": "true"},
    )
    entry = _typed(
        {
            "criterion_id": manual["id"],
            "method": "manual",
            "result": "pass",
            "revision": s.green_sha,
            "signed_by": "reviewer",
        }
    )

    _approved(_decide(s, _entry(s), entry, ids=[s.aid, manual["id"]]))


def test_r10_writes_nothing_to_the_store(tmp_path: Path) -> None:
    s = _scenario(tmp_path)
    before = {r["id"]: r["revision"] for r in s.project.records()}

    _approved(_decide(s))

    assert {r["id"]: r["revision"] for r in s.project.records()} == before


def test_r10_refuses_what_a_gate_refuses(tmp_path: Path) -> None:
    s = _scenario(tmp_path, green_content=ORACLE_V2)

    assert isinstance(_decide(s), CloseRefusal)


def _phase_versions(tmp_path: Path, *, stale: str, current: str) -> Scenario:
    s = _scenario(
        tmp_path, frozen=False, acceptance={"phase": PHASE}, phase={"oracle_policy": stale}
    )
    phase = s.project.resolve("score:phase", PHASE)
    supersede_late(
        s.project,
        phase,
        payload={"title": "Ph", "ordinal": 1, "effort": EFFORT, "oracle_policy": current},
    )
    return s


def test_r11_refuses_by_the_current_phase_when_a_superseded_record_is_newer(
    tmp_path: Path,
) -> None:
    s = _phase_versions(tmp_path, stale="none", current="frozen")

    reason = _reason(_decide(s))

    assert reason.startswith(f"criterion {s.aid!r}: incomplete oracle freeze or invalid policy")


def test_r11_passes_by_the_current_phase_when_a_superseded_record_is_newer(
    tmp_path: Path,
) -> None:
    s = _phase_versions(tmp_path, stale="frozen", current="none")

    _approved(_decide(s))


def test_r11_refuses_phase_whose_records_are_all_superseded(tmp_path: Path) -> None:
    s = _scenario(tmp_path, frozen=False, acceptance={"phase": PHASE})
    phase = s.project.resolve("score:phase", PHASE)
    supersede_all(s.project, phase, payload={"title": "Next", "ordinal": 1, "effort": EFFORT})

    reason = _reason(_decide(s))

    assert reason == "phase 'ph' policy unavailable: phase 'ph' not found"


def test_r12_decides_from_the_given_project_with_no_store_in_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _scenario(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    _approved(_decide(s))


def test_r12_refuses_from_the_given_project_not_the_store_in_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    s = _scenario(tmp_path)
    empty = _seeded_project(tmp_path / "empty-store")
    monkeypatch.chdir(s.project.project_root)

    reason = _reason(_decide(s, project=empty))

    assert reason.startswith(f"criterion {s.aid!r}: acceptance could not be loaded: ")
