---
{
  "id": "rec-cee9a85f-4a46-475f-9343-b77df3affcd4",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "subagent-check",
    "decisions": [
      "se-workflow-cli",
      "dirty-pass-policy"
    ],
    "depends_on": [
      "check-run-contract"
    ],
    "effort": "workflow-loop",
    "estimate_minutes": 45,
    "executor": "subagent",
    "kind": "deliver",
    "phase": "check-runner",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R7",
      "R8"
    ],
    "size": "L",
    "title": "se-workflow CLI check subcommand"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-10T22:15:20+00:00",
  "relationships": {},
  "revision": "sha256:8b07d8855774ca4cc17f4aa7828d33e5a132878ded91b5675582c4dffe45d370",
  "subject": "se-workflow-check"
}
---

## Description

Ship the `se-workflow` CLI shell and a real `check` subcommand that runs verify_command and writes machine-produced check-runs.

## Approach

1. Add `bin/se-workflow` (thin launcher) and `se_workflow/` package with a subcommand dispatcher; implement `check` with `--acceptance`, `--cwd`, `--allow-dirty`, `--execution-report`, `--timeout`.
2. Load acceptance via adaptive-artifacts; refuse `method=manual` with sign-off guidance; capture HEAD + dirty state; apply dirty-pass policy (refuse dirty pass without override; `--allow-dirty` → revision dirty + diff_sha256; fail may be dirty).
3. Run verify_command with timeout; map 0→pass, non-zero→fail, timeout/missing→blocked; create `project:check-run` through adaptive-artifacts with runner fields and informed_by the acceptance.
4. Update `scripts/sync-plugin.sh` to copy `bin/` and `se_workflow/`; document invocation in README next to dashboard/bin.
5. Tests in `tests/test_se_workflow_check.py`: unit policy + throwaway-store integration through the CLI entry point for pass and fail (and blocked where cheap).
