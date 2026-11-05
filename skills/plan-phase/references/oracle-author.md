# Oracle author (deliver / repair)

Skip for incidental / evaluate without tdd oracles. Run before any
acceptance exists. After the tdd acceptances are drafted (subject,
requirement id, `method=tdd`), dispatch **one** phase-scoped
oracle-author subagent covering every tdd acceptance that should be
oracle-backed.

Give it only original requirement / specification text (and the
drafted acceptance subjects / requirement ids). Do **not** give it
work-item Approach, executor briefs, or implementation hints.

The oracle-author writes failing tests against the current tree and
returns the node ids and file paths. It does not call
`canon` and does not write freeze fields.

Parent then, for each such drafted acceptance:

1. Run the proposed node ids directly in the work tree, for example
   `python3 -m pytest <node-id> … -q`. No acceptance record exists
   yet, so `orchestra check` does not apply.
2. Freeze **only** when that fail is assertion-level: `result=fail`
   with an assertion failure for each failing node — not ImportError /
   collection ERROR alone.
3. On assertion-level red, compute `oracle_hashes` for the files those
   ids live in and put `test_ids`, `oracle_hashes`, and the derived
   `verify_command` into the drafted acceptance payload. The
   acceptance is then created once, with the plan batch (plan-phase
   step 9):

```json
{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1","test_ids":["tests/test_<area>.py::test_<case>"],"oracle_hashes":["tests/test_<area>.py:sha256:<hex>"]}
```

4. After the batch, run `orchestra check --acceptance <acceptance-id>
   --cwd <repo-or-worktree>` (expect fail) so the runner records the
   red check-run. Run `orchestra verify assertion-red` on its JSON to
   confirm it is assertion-level.

If the red is not assertion-level, do not freeze — send the
oracle-author back (still requirement text only) or draft that
acceptance without `test_ids` and `oracle_hashes`. Never create an
oracle-backed acceptance first and update it later. Do not open plan
review while intended oracle-backed tdd acceptances lack freeze
fields.

`test_ids` is a JSON array of pytest node ids; `oracle_hashes` is a
JSON array of `relpath:sha256:<hex>` for the files those ids live in. An acceptance with both non-empty is **oracle-backed**.
