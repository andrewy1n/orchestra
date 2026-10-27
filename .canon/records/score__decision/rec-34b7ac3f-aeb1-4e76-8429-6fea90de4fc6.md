---
{
  "id": "rec-34b7ac3f-aeb1-4e76-8429-6fea90de4fc6",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "fold the audit into aff verdict as a failing rule; shell out to an off-the-shelf mutator",
    "choice": "aff audit --cwd DIR --base REV --head REV [--test NODE ...] [--mutants FILE] [--max-mutants N] prints one advisory JSON object and exits 0 (2 on usage or git errors). Claim tests are the tests of every claim in the head manifest plus any --test ids; the runner is the head manifest runner or the default. Blocks are the hunks of git diff -U0 base head, excluding .artifacts/**, test files (a path component tests or test, basename test_*.py, *_test.py, conftest.py) and prose (.md .rst .txt or under docs/). Each block is {file,start,end,label,text} with new-file lines and the added text; label is noticed when reverting the block makes a claim test fail an assertion, not_noticed when every claim test still passes, inconclusive otherwise. Only claim tests that pass at head can notice. Mutants come from a JSON file {mutants:[{id,file,patch:{old,new}}]}; a mutant is planted only when patch.old occurs in a noticed block of that file, and is reported as {id,file,status} with status killed, survived, invalid, or skipped. The output lists blocks, mutants, and survivors (ids); verdict is unaffected",
    "effort": "evidence-layer",
    "phase": "phase-end-evidence"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-18T04:10:41+00:00",
  "relationships": {},
  "revision": "sha256:26ae682674e8d102a8f3b9eeaea5f55c6cfa0349e41346c64bd8d2fe442ea784",
  "subject": "audit-interface",
  "time": {
    "as_of": "2026-10-18T04:10:41+00:00"
  }
}
---

## Rationale

A fixed JSON shape and fixed labels let CI and orchestra consume the audit without parsing prose. Taking mutant proposals from a file keeps the proposer (LLM or tool) outside the judge; only a test run decides killed or survived.

## Counter-argument

A failing rule inside verdict would make the audit hard to ignore. It would also fail claims for hunks no claim named, which the phase non-goals rule out.
