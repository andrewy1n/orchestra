# Close batch (simple work)

`close` is the simple-work batch for verify-work steps 3–5 (no phase
specification, and incidental). It skips assessment and release. Do
not route `blocked` or `insufficient` through `close`. Structured
work uses `orchestra check` (or a `manual` create) with `requirement`
/ `evidence_kind`, then Assess — `close` does not copy those fields.

Use once every active acceptance has a runner-produced check-run
(`tdd`/`check`) or a judged `manual` result, and any diagnose/eval
records from step 2 are written. It still leaves `in_progress` on
`fail` (step 6) or drives `withdrawn` (step 7) — `close` covers the
`done` path, including the deliberate "done anyway" path that needs
a `finding`. It **refuses** the batch (prints unmet criteria, writes
nothing) when `transition` is `done`, a criterion is unmet/unchecked,
and no `finding` was given. It also refuses a pass-only `tdd` `done`
without valid request-carried red evidence (and no `finding`). For
oracle-backed `tdd`, do not close when the claim is in
`.affidavit/manifest.json` and `aff verdict` exits non-zero. Do not
`create`/`supersede` `project:oracle-amendment`. Close-batch still
refuses without a qualifying assertion-level red for frozen tests.
Do not hand-write the batch to route around a refusal.

For `tdd`/`check`, `orchestra close-batch` does **not** invent
pass/fail or create check-runs — it references runner-produced
`check_run_id`s and copies each run's `result` for the refusal gate.
For `tdd` on `done`, also carry red-first fields from a prior runner
fail (oracle-backed red must be assertion-level). `manual` criteria
still carry `result` / `revision` / `signed_by` so the batch can
create those check-runs. `check` and `manual` do not require
`red_check_run_id`.

CLI: `orchestra close-batch` (see
[ensure-store.md](references/ensure-store.md)).

1. Active acceptances only (superseded definitions are retired):

```bash
adaptive-artifacts list --type project:acceptance --subject "<task-slug>" --state active
```

2. Most recent execution-report (omit / leave `execution_report_id`
   `null` when verified without one):

```bash
adaptive-artifacts list --type project:execution-report --subject "<task-slug>" --full --order-by recorded_at
```

   Take the last entry (`recorded_at` sorts oldest first).
3. For each active acceptance, use step 3's check-runs. For
   `tdd`/`check`, take the runner check-run's `id` and `result`. For
   `tdd` closing to `done` with `result` `pass`, also list check-runs
   and pick a prior runner fail for that criterion as the red:

```bash
adaptive-artifacts list --type project:check-run --subject "<task-slug>" --full --order-by recorded_at
```

   Copy from the red: `red_check_run_id`, `red_result` (`fail`),
   `red_revision`, `red_runner` (`orchestra`), and when
   `red_revision` is `dirty`, non-empty `red_diff_sha256` from that
   run's `diff_sha256`. Copy the green run's `revision` onto the
   criteria entry (ancestry: green equals or is a git descendant of
   red SHA; dirty red skips SHA ancestry and only needs
   `red_diff_sha256`). Do not invent red fields; if none, keep
   `in_progress` or use the finding escape. For `manual`, use
   `revision` from `git rev-parse HEAD` once committed and
   `signed_by` once reviewed.

   Write a close-request: `criteria` = acceptances actually checked;
   `acceptance_ids` = **every** active acceptance from step 1.
   Leave `finding` `null` when every criterion passed and each `tdd`
   pass carries valid red:

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>", "<acceptance-id-2>"],
  "criteria": [
    {
      "criterion_id": "<acceptance-id-1>",
      "method": "tdd",
      "check_run_id": "<green-runner-check-run-id>",
      "result": "pass",
      "revision": "<green-sha>",
      "red_check_run_id": "<red-runner-check-run-id>",
      "red_result": "fail",
      "red_revision": "<red-sha>",
      "red_runner": "orchestra"
    },
    {"criterion_id": "<acceptance-id-2>", "method": "check", "check_run_id": "<runner-check-run-id-2>", "result": "pass"}
  ],
  "finding": null
}
EOF
```

   Dirty red: `red_revision` `"dirty"` plus `red_diff_sha256` (green
   `revision` still copied; no SHA ancestry):

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>"],
  "criteria": [
    {
      "criterion_id": "<acceptance-id-1>",
      "method": "tdd",
      "check_run_id": "<green-runner-check-run-id>",
      "result": "pass",
      "revision": "<green-sha-or-dirty>",
      "red_check_run_id": "<red-runner-check-run-id>",
      "red_result": "fail",
      "red_revision": "dirty",
      "red_runner": "orchestra",
      "red_diff_sha256": "<digest-from-red-check-run-diff_sha256>"
    }
  ],
  "finding": null
}
EOF
```

   Closing anyway (unmet/unverified, or `tdd` pass without red):
   `finding` carries step 5's fields (`needs` forced to `"human"`):

```bash
cat > /tmp/close-request.json <<'EOF'
{
  "subject": "<task-slug>",
  "effort": "<effort-slug>",
  "work_item_id": "<work-item-record-id>",
  "transition": "done",
  "execution_report_id": "<execution-report-record-id-or-null>",
  "acceptance_ids": ["<acceptance-id-1>"],
  "criteria": [
    {"criterion_id": "<acceptance-id-1>", "method": "check", "check_run_id": "<runner-check-run-id>", "result": "fail"}
  ],
  "finding": {
    "claim": "<task-slug> closed done with an unmet or unverified criterion",
    "basis": "<why it was closed anyway>",
    "invalidated_when": "<what would undo this acceptance>",
    "body": "## Evidence\n\n<the failing/missing check-run and why closing proceeded anyway>\n\n## Consequence\n\n<what remains unverified>\n\n## Follow-up\n\n<what someone should do to close the gap, or \"none\">"
  }
}
EOF
```

4. Build the batch. Pass `--cwd` for phase worktrees (git-ancestry
   red-first against that repo):

```bash
orchestra close-batch \
  --input /tmp/close-request.json \
  --out /tmp/close-batch.ndjson \
  --cwd <repo-or-worktree>
```

   Exit `0` → run `apply`. Exit `2` → refused (unmet/unverified with
   no `finding`, or pass-only `tdd` without valid red/ancestry);
   stderr names criteria; go back to step 3 — do **not** `apply`.
   Exit `1` → malformed JSON; fix and retry.
5. Only after exit `0`, apply — one `project:check-run` create per
   `manual` criterion (`informed_by` acceptance + execution-report);
   `tdd`/`check` check-runs already exist from `orchestra check`. Then
   the `finding` if given, then the work-item transition:

```bash
adaptive-artifacts apply /tmp/close-batch.ndjson
```

6. Regenerate views and validate (verify-work step 8).
