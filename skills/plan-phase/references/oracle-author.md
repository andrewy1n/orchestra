# Oracle author (deliver / repair)

Skip for incidental / evaluate without tdd oracles. After thin
`method=tdd` acceptances exist for this phase, dispatch **one**
phase-scoped oracle-author subagent covering every tdd acceptance that
should be oracle-backed.

Give it only original requirement / specification text (and the thin
acceptance subjects / requirement ids). Do **not** give it work-item
Approach, executor briefs, or implementation hints.

The oracle-author writes failing tests against the current tree and
returns the node ids and file paths. It does not call
`canon` and does not write freeze fields.

Parent then, for each such acceptance:

1. Set a provisional `verify_command` from the proposed `test_ids`
   (e.g. `python3 -m pytest <node-id> … -q`) if needed so
   `orchestra check` can run.
2. Run `orchestra check --acceptance <acceptance-id> --cwd <repo-or-worktree>`
   (expect fail).
3. Freeze **only** when that fail is assertion-level (use
   `tuner.oracle_red.is_assertion_level_red` on the check-run, or
   equivalent: `result=fail` with assertion failure for a failing node
   — not ImportError / collection ERROR alone).
4. On assertion-level red, parent writes freeze fields and the derived
   `verify_command`:

```bash
canon update --type score:acceptance --id <acceptance-id> \
  --expected-revision <revision> \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1","test_ids":["tests/test_<area>.py::test_<case>"],"oracle_hashes":["tests/test_<area>.py:sha256:<hex>"]}'
```

If the red is not assertion-level, do not freeze — send the
oracle-author back (still requirement text only) or drop that
acceptance from the oracle-backed set. Do not open plan review while
intended oracle-backed tdd acceptances lack freeze fields.

`test_ids` is a JSON array of pytest node ids; `oracle_hashes` is a
JSON array of `relpath:sha256:<hex>` for the files those ids live in. An acceptance with both non-empty is **oracle-backed**.
