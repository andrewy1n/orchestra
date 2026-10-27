---
{
  "id": "rec-9fad7caf-d2b2-4af0-9dce-f558e09d91c0",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "executor": "observation-cli",
    "work_item": "observation-cli"
  },
  "provenance": {
    "sources": [
      "observation-cli"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T09:08:07+00:00",
  "relationships": {},
  "revision": "sha256:3b991e05a92d7a87ff5b0b92c3f2a8e1096c76946c863618f1995380d8a5181b",
  "subject": "observation-cli",
  "time": {
    "observed": "2026-10-18T09:08:07+00:00",
    "recorded": "2026-10-18T09:08:07+00:00"
  }
}
---

## Orientation

Solo wave-2 task. Worktree: `/home/andrewyin/affidavit--evidence-interface` (already has R1 contract). Edit `affidavit/observation.py`, `affidavit/verdict.py` and/or `affidavit/cli.py` only as Approach says. Do not edit `.artifacts/`. Do not edit frozen oracle `tests/test_evidence_interface.py`. Commit on the phase branch excluding `.artifacts`.

Satisfy `tests/test_evidence_layout.py::test_no_store_tokens` by assembling forbidden substrings from fragments in source.

### Work-item (quote)

## Description

R2: After `aff verdict` finishes judging, when a usable artifact store is available for the subject repo, it creates one `project:evidence-observation` per invoked run via the `adaptive-artifacts` CLI (not a Python import of the runtime).
R3: `aff trail` lists evidence-observations from the store (filterable by claim id when the observation references claims) and prints them as JSON.

## Approach

1. Add `affidavit/observation.py` with helpers to detect a usable store under the subject cwd, create one evidence-observation via subprocess CLI, and list observations (optional claim / technique filters). Payload fields match the contract: technique, base_rev, head_rev, result, claim_ids, plus outcomes/replay as designed.
2. Satisfy `tests/test_evidence_layout.py::test_no_store_tokens`: do not leave the contiguous substrings `adaptive-artifacts`, `project:`, `SE_WORKFLOW_STORE`, or `store-binding.json` in any `affidavit/*.py` source. Assemble the CLI binary name and record-type string from fragments (or equivalent) so the seam still shells out without importing the runtime.
3. Hook `affidavit/verdict.py` (or the CLI path after judge) so a completed verdict run records one observation when a store is usable; when no store is present, stdout and exit code are unchanged (decision `observation-record-optional`). Recording failure must not flip a passing judge result — prefer stderr note and continue.
4. Extend `affidavit/cli.py` with `aff trail [--cwd DIR] [--claim ID] [--technique NAME]` printing a JSON list.
5. Do not edit `contract/project-design.json` (owned by observation-contract), do not edit frozen oracle test files, and do not change judge semantics (hashes, red/green, amendments).

### Requirements (quote by id)

R2: After `aff verdict` finishes judging, when a usable artifact store is available for the subject repo, it creates one `project:evidence-observation` per invoked run via the `adaptive-artifacts` CLI (not a Python import of the runtime).
R3: `aff trail` lists evidence-observations from the store (filterable by claim id when the observation references claims) and prints them as JSON.

### Design / decisions (quote)

## Invariants

- Judge path does not require a store.
- Observation records are append-only occurrences (no hand-edited store files).

## Assumptions

- `adaptive-artifacts` is on PATH in environments that record.
- Tests may build a disposable store from this contract (existing suite pattern).

Decisions:
- observation-record-optional: record evidence-observation only when a usable store is present (or explicitly targeted); verdict otherwise unchanged
- observation-ledger-home: store-backed project:evidence-observation in subject .artifacts via adaptive-artifacts
- aff-observation-seam: aff records and lists observations via adaptive-artifacts CLI subprocess; no runtime import; claims stay in git manifest

### Frozen oracle (do not edit)

Files listed in acceptance oracle_hashes for this task are frozen.
Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done.

Frozen: tests/test_evidence_interface.py
