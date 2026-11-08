# Phase end

Run this sequence only after no same-focus task remains planned or in progress.
Incidental work skips reviewer, integration report, and suite.

1. Run `orchestra analyze <phase> --stage close`. Fix every error before review.
2. Build a restricted `orchestra review-brief`. Use a read-only reviewer.
   Record one review check-run and each actionable finding. Do not rerun the
   reviewer after fix tasks.
3. For a multi-task wave, write one semantic integration report from the
   reviewer's integration notes. A clean merge alone does not prove
   integration. Use all four required body sections: Interfaces, Assumptions,
   Invariants, and Conflicts.
4. Read `orchestra suite policy`. Follow its mode and gate. Do not waive a
   required suite or record a passing suite from a dirty-only run.
5. Run `orchestra gate`. Do not close when a required term fails.
6. Write the proof packet with a human-facing check, machine evidence, open
   attention, and diff summary. Confirm the packet matches the phase head.
7. With Landing, commit the phase branch from its phase worktree and run
   `orchestra land --phase <phase>`. Ask the user before landing unless an
   active constraint authorizes it. Do not push from phase close.
8. Run `canon validate`.

After close, read the effort autonomy. At `auto-phases`, plan and promote the
next phase. At `gated` or `auto-plan`, ask first. A failed check, human-needed
finding, push, or merge remains a stop.
