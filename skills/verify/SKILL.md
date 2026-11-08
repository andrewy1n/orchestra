---
name: verify
description: >-
  Assess recorded task or phase evidence and report the next required step.
  Use when the workflow routes to verification.
---

# Verify evidence

Requires `canon` and `orchestra` on PATH. Follow
[ensure-store.md](references/ensure-store.md),
[kinds-and-focus.md](references/kinds-and-focus.md), and
[record-mechanics.md](references/record-mechanics.md). Follow
[assess.md](references/assess.md), [close-batch.md](references/close-batch.md),
and [verify-mechanics.md](references/verify-mechanics.md). For phase closure,
follow [phase-end.md](references/phase-end.md). Follow
[verification-policy.md](references/verification-policy.md) for oracle gates.

## Verify

### Task verification

1. Resolve the active work-item and its acceptances. Read the latest execution
   report and verify each command, test, diff, or metric it names.
2. Run `orchestra check --acceptance <id>` for each TDD or check acceptance.
   Keep runner output and revision. Do not create those check-runs yourself.
3. For TDD, include the runner's red and green records in close-batch. Enforce
   frozen-oracle checks when the acceptance has frozen oracle fields.
4. For manual evidence, record the unsigned manual result. Do not claim pass
   without evidence the user accepts. For repair or evaluation, record
   observations and findings before closing.
5. Use one `orchestra close-batch` request and one `canon apply`. Keep failed,
   blocked, insufficient, or human-needed work open. Never reopen a done task.
6. Read `orchestra view verification --effort <focus>` and report each
   requirement's evidence status and the next required step.
7. Run `canon validate`. If same-phase work remains, report task status and
   stop at verify.

## Phase verification

When no same-focus work-item remains planned or in progress:

1. Run `orchestra analyze <phase> --stage close`. Resolve error findings
   before review.
2. Read `orchestra suite policy` and run the required suite under its
   configured policy.
3. Run the phase reviewer once at the current head. Record its review
   check-run and actionable findings. Create fix tasks for code findings;
   do not let the reviewer edit files or write records.
4. Record the semantic integration report from reviewer evidence when the
   phase has a multi-task wave. A clean merge is not enough.
5. Run `orchestra gate` and write the proof packet at the phase head.
   With a Landing section, verify ends here. Verify does not commit, push,
   or run land. Hand off to the Land section of `phase-end.md`.
6. Without a Landing section, close the phase only when all required terms
   pass.
7. Run `canon validate`. After close, read effort autonomy. Plan the next
   phase only at `auto-phases`; ask first for `gated` or `auto-plan`.

Report what the evidence proves and the next required step. Keep evidence,
assessment, review, suite, and human approval distinct.

## Do not

- Mark a requirement verified from narrative without a passing check-run
- Close a task with an unmet acceptance unless a human accepts the finding
- Skip assertion-level red or frozen-oracle checks
- Treat task completion as phase completion
- Continue past a failed check or a needs-human finding
