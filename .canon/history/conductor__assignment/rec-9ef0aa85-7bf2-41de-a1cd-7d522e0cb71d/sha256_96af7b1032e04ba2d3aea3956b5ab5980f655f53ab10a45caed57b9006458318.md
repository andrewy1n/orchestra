---
{
  "id": "rec-9ef0aa85-7bf2-41de-a1cd-7d522e0cb71d",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "ci",
    "executor": "inline",
    "work_item": "fix-review-minors"
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-29T06:01:50+00:00",
  "relationships": {},
  "revision": "sha256:96af7b1032e04ba2d3aea3956b5ab5980f655f53ab10a45caed57b9006458318",
  "subject": "fix-review-minors"
}
---

## Orientation

Inline fix task for two minor reviewer findings. Write root: `/home/andrewyin/orchestra/.worktrees/ci-workflow--fix-review-minors`

### Work-item (quote)

## Description

R1: `.github/workflows/ci.yml` exists and `.github/workflows/tuner-verdict.yml` is unchanged.
R29: `README.md` lists the four pytest commands under Testing. `CLAUDE.md` and `AGENTS.md` point to that section.

The phase-end reviewer found two minor gaps. The R1 test only detects uncommitted edits. The README Testing paragraph has two sentences joined onto one long line.

## Approach

In `tests/test_ci_workflow.py`, make `test_r1_*` diff `tuner-verdict.yml` against the merge base with `origin/main` or `main`, whichever resolves first. When neither ref resolves (a shallow CI checkout), fall back to the diff against `HEAD`. In `README.md`, rewrap the paragraph that holds the `--reruns 2` and empty-command fallback sentences to the surrounding line width. Run the R1 and README-pinned tests and ruff. Commit on the task branch.

### Requirements (quote by id)

R1: `.github/workflows/ci.yml` exists and `.github/workflows/tuner-verdict.yml` is unchanged.
R29: `README.md` lists the four pytest commands under Testing. `CLAUDE.md` and `AGENTS.md` point to that section.

### Design / decisions (quote)

ci-test-job-layout: parallel jobs calling uv run pytest directly; scripts/test.sh removed, README Testing and the phase suite command hold the same four commands
