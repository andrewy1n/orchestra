---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-4fd46abe-2bb7-48d7-86b2-eb2a42de99ec",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "workflow-loop",
    "phase": "red-first",
    "requirements": "R1,R2,R3,R4,R5,R6",
    "weight": "full"
  },
  "record_type": "project:specification",
  "recorded_at": "2026-10-10T22:42:31+00:00",
  "relationships": {},
  "revision": "sha256:c33a8749f539e1652888e9d5959f005e09d40c36bc7aa99744400b196cc4b6ed",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "red-first",
  "time": {
    "as_of": "2026-10-10T22:42:31+00:00"
  }
}
---

## Requirements

R1: When closing a work-item to `done`, every active acceptance with `method: tdd` must have a runner-produced fail check-run for that criterion that precedes the closing pass, or the close must include a finding escape.
R2: The close-request carries the red evidence as `red_check_run_id` (and copied fail fields needed for the gate); `close_batch.py` does not query the store for prior check-runs.
R3: "Preceding" means the green revision is a git descendant of (or equal to) the red revision when both are SHAs; a dirty red is accepted only when it carries `diff_sha256`.
R4: Closing without a valid red is allowed only when the same close-request supplies a `project:finding` with `needs` forced to `human` whose claim names the missing red (same escape shape as unmet criteria today).
R5: Acceptances with `method: check` or `method: manual` are unaffected by the red-first gate.
R6: `skills/verify-work/SKILL.md` describes the enforced behavior and drops the claim that the engine does not enforce red-first.

## Acceptance criteria

- `close_batch.py` exits 2 for a `tdd` criterion whose close-request has only a passing check-run and no finding, and names the criterion on stderr.
- A request with a valid fail→pass pair (runner ids, order/ancestry or dirty+`diff_sha256`) is accepted when all other close rules pass.
- Wrong order (pass recorded/used as red, or green SHA not descended from red SHA) is refused.
- Finding escape permits the close and forces `needs: human`.
- `check` and `manual` criteria close as they do today without red fields.
- Tests in `tests/test_close_batch.py` cover pass-only refusal, fail→pass acceptance, wrong-order refusal, dirty-red with digest, and finding override.
- `tests/test_skill_contract_consistency.py` stays green after the verify-work text change.

## Constraints

- Binary `tdd`/`check` check-runs remain runner-authored only (`check-run-authority`); close still references ids and copies `result`, it does not invent pass/fail.
- Dirty pass policy from check-runner is unchanged; this phase only adds the red-before-green rule for `tdd` closes.

## Non-goals

- `validate --strict` warnings or dashboard badges for historical pass-only `done` work-items.
- Store lookup inside `close_batch.py` for red check-runs.
- Changing retry loops, tiered verification, or the phase-end reviewer.
- Measuring post-phase red-first rate (may use analyze-sessions later; not a delivery gate here).

## Invariants

- A successful `done` close for a `tdd` criterion either has a validated red→green pair in the close-request or a human-needs finding that names the missing red.
- `check`/`manual` close paths do not require `red_check_run_id`.

## Assumptions

- verify-work (or the parent) can resolve the red check-run id from the store when building the close-request.
- Git is available in the cwd used for ancestry checks when both revisions are SHAs.
- Runner-produced fail check-runs set `runner` (or equivalent) so close can reject hand-authored reds the same way it rejects invented greens.
