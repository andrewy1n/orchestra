"""Skill markdown must not write tdd/check check-runs or oracle-amendments.

A tdd or check result comes from ``orchestra check``. An oracle hash or test-id
change is a signed amendment in ``.affidavit/manifest.json``. ``aff verdict``
accepts or rejects that claim. Manual, review, and the suite module's
check-run write stay allowed.
"""

from __future__ import annotations

import re
from pathlib import Path

from conftest import REPO_ROOT
from skill_extraction import extract_invocations

SKILLS = REPO_ROOT / "skills"
EXECUTE = SKILLS / "execute-phase" / "SKILL.md"
VERIFY = SKILLS / "verify-work" / "SKILL.md"
SUITE_MODULE = REPO_ROOT / "orchestra" / "suite.py"

_RUNNER_METHODS = {"tdd", "check"}
_AMENDMENT_SENTENCE = (
    "An oracle hash or test-id change is a signed amendment in "
    "`.affidavit/manifest.json`."
)
_NOT_DONE = "A non-zero exit means the acceptance is not done."

_FORBIDDEN_FIXTURE = """\
```bash
canon create --type aff:check-run \\
  --subject "<task-slug>" \\
  --payload '{"criterion_id":"<acceptance-id>","result":"pass","method":"tdd"}'

canon correct --type aff:check-run --id <check-run-id> \\
  --payload '{"method":"check","result":"pass"}'

canon create --type aff:oracle-amendment \\
  --subject "<task-slug>" \\
  --payload '{"status":"requested"}'

canon supersede --type aff:oracle-amendment --id <amendment-id> \\
  --payload '{"status":"approved"}'
```
"""

_ALLOWED_FIXTURE = """\
```bash
canon create --type aff:check-run \\
  --subject "<task-slug>" \\
  --payload '{"criterion_id":"<acceptance-id>","result":"pass","method":"manual","signed_by":""}'

canon create --type aff:check-run \\
  --subject "<phase-slug>-review" \\
  --payload '{"criterion_id":"<phase-review-acceptance-id>","result":"pass","method":"review","evidence_kind":"review"}'

canon correct --type aff:check-run --id <check-run-id> \\
  --payload '{"signed_by":"<signer>"}'

canon create --type aff:check-run \\
  --subject "<phase-slug>-suite" \\
  --payload '{"criterion_id":"<phase-slug>-suite","result":"pass","method":"check","evidence_kind":"integration","output_sha256":"<digest>","failing_node_ids":"[]"}'
```
"""


def _payload(inv: dict) -> dict:
    payload = inv.get("payload")
    return payload if isinstance(payload, dict) else {}


def _is_suite_check_run(inv: dict) -> bool:
    """The suite check-run ``orchestra.suite.record_suite_check_run`` writes.

    Skills may still show that create. Its method is ``check`` and its
    subject is the phase suite, so it is not a task tdd/check result.
    """
    payload = _payload(inv)
    if payload.get("method") != "check":
        return False
    if payload.get("evidence_kind") != "integration":
        return False
    raw = inv.get("raw") or ""
    criterion = str(payload.get("criterion_id") or "")
    return "-suite" in criterion or "-suite" in raw


def boundary_violations(text: str) -> list[str]:
    """Create/correct of a tdd or check check-run, or create/supersede of an oracle-amendment."""
    found: list[str] = []
    for inv in extract_invocations(text):
        sub = inv.get("subcommand")
        rtype = inv.get("type")
        if rtype == "aff:check-run" and sub in {"create", "correct"}:
            method = _payload(inv).get("method")
            if method in _RUNNER_METHODS and not _is_suite_check_run(inv):
                found.append(f"{sub} aff:check-run method {method}")
        if rtype == "aff:oracle-amendment" and sub in {"create", "supersede"}:
            found.append(f"{sub} aff:oracle-amendment")
    return found


def scan_skills(skills_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(skills_root.rglob("*.md")):
        for item in boundary_violations(path.read_text()):
            violations.append(f"{path.relative_to(skills_root)}: {item}")
    return violations


def test_fixture_skill_with_forbidden_writes_fails_the_scanner(tmp_path: Path):
    skill = tmp_path / "skills" / "bad" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(_FORBIDDEN_FIXTURE)
    violations = scan_skills(tmp_path / "skills")
    assert any("create aff:check-run method tdd" in item for item in violations)
    assert any("correct aff:check-run method check" in item for item in violations)
    assert any("create aff:oracle-amendment" in item for item in violations)
    assert any("supersede aff:oracle-amendment" in item for item in violations)


def test_manual_review_and_suite_check_run_stay_allowed(tmp_path: Path):
    skill = tmp_path / "skills" / "ok" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(_ALLOWED_FIXTURE)
    assert scan_skills(tmp_path / "skills") == []

    def fenced(invocations: list[dict]) -> str:
        return "```bash\n" + "\n".join(inv["raw"] for inv in invocations) + "\n```"

    execute = EXECUTE.read_text()
    review = [
        inv
        for inv in extract_invocations(execute)
        if inv.get("type") == "aff:check-run"
        and inv.get("subcommand") == "create"
        and _payload(inv).get("method") == "review"
    ]
    assert review, "review check-run write must stay"
    assert boundary_violations(fenced(review)) == []

    suite_creates = [
        inv
        for inv in extract_invocations(execute)
        if inv.get("subcommand") == "create"
        and inv.get("type") == "aff:check-run"
        and _is_suite_check_run(inv)
    ]
    assert suite_creates, "suite check-run write must stay"
    assert boundary_violations(fenced(suite_creates)) == []

    verify = VERIFY.read_text()
    manual = [
        inv
        for inv in extract_invocations(verify)
        if inv.get("subcommand") == "create"
        and inv.get("type") == "aff:check-run"
        and _payload(inv).get("method") == "manual"
    ]
    assert manual, "manual check-run write must stay"
    assert boundary_violations(fenced(manual)) == []

    suite_source = SUITE_MODULE.read_text()
    assert "def record_suite_check_run" in suite_source
    assert 'record_type="aff:check-run"' in suite_source
    skill_paths = {path.resolve() for path in SKILLS.rglob("*.md")}
    assert SUITE_MODULE.resolve() not in skill_paths


def test_migrated_skills_pass_the_scanner():
    violations = scan_skills(SKILLS)
    assert not violations, "\n".join(violations)
    for path in (EXECUTE, VERIFY):
        assert _AMENDMENT_SENTENCE in path.read_text(), path


def test_execute_phase_and_verify_work_run_aff_verdict():
    for path in (EXECUTE, VERIFY):
        text = path.read_text()
        assert "aff verdict" in text, path
        assert ".affidavit/manifest.json" in text, path
        assert _NOT_DONE in text, path
        assert re.search(r"aff verdict\b[^\n]*<claim-id>", text), path
