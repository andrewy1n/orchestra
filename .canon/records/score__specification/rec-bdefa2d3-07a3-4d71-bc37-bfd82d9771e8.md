---
{
  "id": "rec-bdefa2d3-07a3-4d71-bc37-bfd82d9771e8",
  "lifecycle_state": "active",
  "payload": {
    "effort": "evidence-layer",
    "phase": "ci-verdict-fixture",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4"
    ],
    "weight": "light"
  },
  "record_type": "score:specification",
  "recorded_at": "2026-10-18T05:58:56+00:00",
  "relationships": {},
  "revision": "sha256:6088be34b916101517e1f3cf1971ac2ed9f1209f1cf3ec46a5850702930be4c6",
  "subject": "ci-verdict-fixture",
  "time": {
    "as_of": "2026-10-18T05:58:56+00:00"
  }
}
---

## Requirements

R1: Tracked fixture templates under `tests/fixtures/verdict-repo/` (source tree without a nested `.git`) are sufficient to build a subject repo with claim `claim-widget`.
R2: The `affidavit-verdict` workflow builds a git repository at that path from the templates before it runs `aff verdict`.
R3: `aff verdict` for `claim-widget` at the built fixture HEAD returns pass.
R4: A pytest accepts only when the workflow contains an explicit fixture-build step and the templates (or builder script) exist — not merely the strings `verdict` and `attest`.

## Acceptance criteria

- Local or CI dry-run of the setup step leaves a git repo at `tests/fixtures/verdict-repo` with at least one commit.
- After setup, `bin/aff verdict --cwd tests/fixtures/verdict-repo --at <HEAD> claim-widget` exits 0 with a pass result.
- With fixture attest secrets present, the workflow completes emit and verify after verdict.
- `python3 -m pytest tests/test_attestation.py::test_ci_workflow_runs_verdict_and_attest -q` (or its successor) fails if the build step or templates are removed.

## Constraints

- Do not change attestation core signing/verify semantics (`affidavit/attestation.py` behavior for R1–R3 of signed-verdict stays).
- Fixture attest still uses repo secrets `AFFIDAVIT_ATTEST_KEY` and `AFFIDAVIT_ATTEST_ALLOWLIST`.
- No nested `.git` committed under `tests/fixtures/verdict-repo/`.

## Non-goals

- Rotating or provisioning the GitHub Actions attest secrets.
- Making this package repo itself the judged subject.
- Broader CI matrix beyond the existing `affidavit-verdict` job.

## Invariants

- Subject path default remains `tests/fixtures/verdict-repo` unless workflow_dispatch overrides `fixture_cwd`.
- Attestation namespace remains `affidavit-verdict`.

## Assumptions

- Runners have `git`, Python 3.12, and `pytest` as the workflow already installs.
- Fixture secrets are already configured on the GitHub repo (prior signed-verdict work).
