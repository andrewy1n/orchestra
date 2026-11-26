## Steps

1. Resolve the focus and phase from the handoff. Read the active specification
   or the phase `## Requirements`, current spec/design reviews, decisions,
   constraints, assessments, and `orchestra view plan`. Refuse to plan against
   a stale or unapproved contract.
2. Use stable atomic requirement ids. Map every `deliver` or `repair`
   work-item to its requirement ids. Pin current input reviews in its
   `source_reviews` array. Give each acceptance one requirement, unless a
   single check proves several requirements together.
3. Split independent work first. Add `depends_on` only for real ordering or
   data dependencies. Tasks that must rewrite the same function get a
   `depends_on` edge. Make the closing verification task depend on every
   other phase task.
4. Give each work-item `## Description`, `## Approach`, `size`
   (`XS`|`S`|`M`|`L`|`XL`) and `estimate_minutes` (agent wall-clock, not padded).
   Dispatch derives the executor from wave size, estimates, and project
   settings. Add `executor` only as an explicit `inline` or `subagent`
   override. Explicit overrides in one wave must agree. Every task in one
   wave uses the same resolved executor.
   Guidance: XS 1–2, S 2–5, M 5–10, L 10–20, XL 20–40.
   Phase body records session shape (`one sitting` | `more than one`), human
   stops, and shared areas. Use focused tasks and reserve whole-phase verification
   for the final task.
5. For oracle-backed TDD, freeze `test_ids` and `oracle_hashes` in the initial
   acceptance create. Run the oracle author before the batch. Freeze only
   after assertion-level red.
6. Draft records, then apply all phase work-items and acceptances through one
   ordered NDJSON batch. Put prerequisites first and acceptances after their
   work-item. Do not create records one by one.
7. Run and inspect this command:

```bash
orchestra analyze {phase} --stage plan
```

   Refuse plan review if this command exits 1. Fix each finding. Follow the phase
   autonomy and plan review gate. Do not start execution here.

For `next: plan`, add only tasks that cover the missing requirements. Review
the delta through the plan review gate.

No Landing → not ready for plan review. Incidental has no Landing.
Open the plan review gate (skip incidental). Do not open until task recipes,
wave executor choices, phase run facts, proof, Landing, and frozen oracle
fields pass review. Executor choices derive from wave shape and project
settings; written `executor` values are optional overrides. If the effort
has no `autonomy`, run
`orchestra effort autonomy {effort} auto-plan` first. Skip this gate at
`auto-plan` and `auto-phases`. Only an explicit `gated` opens it.

The phase body records its `## Proof` kind as `demo`, `commands`, `claims`,
`audit-triage`, or `mixed`. A light phase may use one acceptance with a
`requirements` array when one check proves each listed requirement.

```bash
canon create --type score:continuity-question \
  --subject "{effort}" \
  --payload '{"owner":"user","blocking":true,"scope":"plan-review:{phase}"}' \
  --body "Review the phase plan. Approve, change, or send it back to spec."
```

After approval, answer the plan-review question and record the task review:

```bash
orchestra workflow review {phase} tasks \
  --artifact <phase-record-id> \
  --authority user-approval \
  --basis "<user's approval>"
```

For `auto-plan` or `auto-phases`, record the policy review instead:

```bash
orchestra workflow review {phase} tasks \
  --artifact <phase-record-id> \
  --authority task-plan-policy \
  --basis "Effort autonomy permits task planning."
```

Start execution only after the task review is current and the blocking
question is clear.

Landing names branch, worktree, base and repo only. `orchestra.toml` `[land]`
and `[suite]` configure them.
