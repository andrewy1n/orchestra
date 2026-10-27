---
{
  "id": "rec-1e0a4ed8-7c6d-400f-9aaa-0be6aa23a1d5",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "evidence-layer",
    "executor": "claim-cli",
    "work_item": "claim-cli"
  },
  "provenance": {
    "sources": [
      "claim-cli"
    ]
  },
  "record_type": "conductor:assignment",
  "recorded_at": "2026-10-18T03:52:20+00:00",
  "relationships": {},
  "revision": "sha256:bfdda6d04b8c6293fbc07ff7b36907e40a8d37710176fc568f344363f6b9fa5a",
  "subject": "claim-cli",
  "time": {
    "observed": "2026-10-18T03:52:20+00:00",
    "recorded": "2026-10-18T03:52:20+00:00"
  }
}
---

## Orientation

Worktree: /home/andrewyin/affidavit--claim-authoring
Branch: phase/claim-authoring
Code writes only under the worktree. Do not edit .artifacts or call adaptive-artifacts.

Concurrent with task human-claim in the same worktree. Territory: you own affidavit/authoring.py, affidavit/lint.py, affidavit/cli.py. Do not edit affidavit/manifest.py, affidavit/verdict.py, or affidavit/human_claim.py. Python 3 stdlib only. Check with the R1-R3 tests: `python3 -m pytest tests/test_claim_authoring.py -k 'r1 or r2 or r3' -q`. Regression command: `python3 -m pytest tests/test_verdict.py tests/test_standalone_cli.py tests/test_runner.py tests/test_manifest.py tests/test_amendment.py tests/test_attestation.py tests/test_lint.py tests/test_provenance.py tests/test_evidence_kind.py -q`.

### Work-item (quote)

## Description

R1: `aff claim add` writes a new claim entry into the committed manifest format without requiring orchestra.
R2: `aff freeze` records oracle (and support) file hashes for claims into the manifest.
R3: A lint reports a compound claim (more than one observable behavior in the claim text, per the phase's lint rules).

## Approach

1. Add `affidavit/authoring.py` with `add_claim(cwd, claim_id, text, tests)` and `freeze(cwd, claim_ids)` that read and rewrite `.affidavit/manifest.json` (indent 2, trailing newline), preserving every other key (runner, support_files, amendments, other claims). Duplicate id, unknown claim id, and a missing oracle or support file exit non-zero and leave the manifest unchanged.
2. Extend `affidavit/lint.py` with a claims lint over the working-tree manifest: compound text contains ` and `, ` as well as `, `;`, or two or more sentences; trust-scoped text names agent-supplied input (for example `agent-supplied` or `supplied by the agent`). Findings print as `<claim-id>: compound claim` and `<claim-id>: trust-scoped claim`.
3. `affidavit/cli.py`: add `aff claim add`, `aff freeze`, and `aff lint claims` exactly as in decision `claim-authoring-interface`. No import of orchestra or the store.
4. Do not edit `affidavit/manifest.py` or `affidavit/verdict.py` (human-claim owns them) or `tests/test_claim_authoring.py` (frozen oracle) or any existing test.


### Requirements (quote by id)

R1: `aff claim add` writes a new claim entry into the committed manifest format without requiring orchestra.
R2: `aff freeze` records oracle (and support) file hashes for claims into the manifest.
R3: A lint reports a compound claim (more than one observable behavior in the claim text, per the phase's lint rules).

### Design / decisions (quote)

#### Invariants
- Standalone authoring works offline from orchestra.

#### Assumptions
- Prior phases have landed freeze-related hash fields.

- `claim-cli`: ship aff claim add and aff freeze to write and hash manifest entries; lint compound and trust-scoped wording; allow an allowlist-signed human claim as a witness instead of red-green tests
- `claim-authoring-interface`: aff claim add --cwd DIR --id ID --text TEXT --test NODE (repeatable) appends a claim with empty oracle_hashes to DIR/.affidavit/manifest.json, creating it when absent and refusing a duplicate id; aff freeze [--cwd DIR] [CLAIM...] sets each claim's oracle_hashes to sha256 of the working-tree file for every distinct path in its test node ids and refuses a missing file (support files are frozen by being listed in support_files; freeze requires each to exist); aff lint claims [--cwd DIR] prints '<claim-id>: compound claim' for text containing ' and ', ' as well as ', ';' or two or more sentences, and '<claim-id>: trust-scoped claim' for text naming agent-supplied input, exiting 1 on any finding; a claim with witness 'human' carries an ssh signature string over 'affidavit-claim v1\nclaim: <id>\ntext: <text>\n' in namespace affidavit-claim, verified against .affidavit/allowed_signers at --at, with reasons 'human signature missing' and 'human signature invalid'

### Frozen oracle (do not edit)

Frozen files: tests/test_claim_authoring.py. Do not edit them. An oracle hash or test-id change is a signed amendment in `.affidavit/manifest.json`. aff verdict accepts or rejects it. A non-zero exit means the acceptance is not done.
