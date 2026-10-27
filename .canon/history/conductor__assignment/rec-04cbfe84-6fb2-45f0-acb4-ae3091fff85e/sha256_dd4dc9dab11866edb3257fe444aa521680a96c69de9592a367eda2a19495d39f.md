---
{
  "id": "rec-04cbfe84-6fb2-45f0-acb4-ae3091fff85e",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "executor": "witness-lint",
    "work_item": "witness-lint"
  },
  "provenance": {
    "sources": [
      "witness-lint"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T03:16:34+00:00",
  "relationships": {},
  "revision": "sha256:dd4dc9dab11866edb3257fe444aa521680a96c69de9592a367eda2a19495d39f",
  "subject": "witness-lint",
  "time": {
    "observed": "2026-10-18T03:16:34+00:00",
    "recorded": "2026-10-18T03:16:34+00:00"
  }
}
---

## Orientation

Worktree: /home/andrewyin/affidavit--frozen-environment
Branch: phase/frozen-environment
Do not edit .artifacts. Do not call adaptive-artifacts.
Frozen oracle files (do not edit): tests/test_lint.py

### Work-item Description
R3: A lint command reports a witness test that contains no assertion (or equivalent outcome signal for the runner kind).
R4: A lint command, given base and head revisions, reports a witness id that is skipped at head and was not skipped at base.

### Work-item Approach
1. Add affidavit/lint.py with: (a) scan witness test source for missing assert/pytest.raises (AST); (b) compare skip/not_run sets between two revisions using run_tests or JUnit outcomes on the claim's witness ids.
2. Extend affidavit/cli.py with aff lint subcommands only (do not change verdict).
3. Tests cover a no-assert fixture and a base→head new-skip fixture. Do not edit manifest.py, amendment.py, or verdict.py (env-freeze owns those).

### Requirements
R3: A lint command reports a witness test that contains no assertion (or equivalent outcome signal for the runner kind).
R4: A lint command, given base and head revisions, reports a witness id that is skipped at head and was not skipped at base.

### Design Invariants
- Unsigned support or runner drift cannot yield verdict pass.
- Store tokens stay out of `affidavit/`.

### Design Assumptions
- One support list granularity (manifest-global or per-claim) is enough; plan-phase picks the smaller change that meets R1.
- Lint may be `aff lint` or a pytest-invoked helper in this phase.

### Decisions
- freeze-lint: a cheap lint reports no-assert witnesses and skips added between base and head; it does not change the verdict result by itself

### Territory
env-freeze owns affidavit/manifest.py, amendment.py, verdict.py and their tests (except frozen oracle lines — do not edit frozen oracle file content; only add production code).
witness-lint owns affidavit/lint.py and cli.py lint wiring and tests/test_lint.py is FROZEN — do not edit it; implement lint to satisfy it.
