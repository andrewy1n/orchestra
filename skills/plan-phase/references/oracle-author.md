# Oracle author (selected frozen acceptances)

Skip oracle authoring when no acceptance selects `oracle_policy: frozen`.
Ordinary TDD does not require an oracle author or tests during planning.
After drafting methods and policies, dispatch **one** phase-scoped
oracle-author subagent for only the selected frozen acceptances.
Run it before those acceptances exist.

Give it only original requirement / specification text, the method,
and drafted acceptance subjects / requirement ids. Do **not** give it
work-item Approach, executor briefs, or implementation hints.

The oracle-author writes tests against the current tree and returns
the node ids and file paths. It does not call `canon` or write freeze fields.

Parent then, for each selected frozen acceptance:

1. Run the proposed node ids directly, for example
   `python3 -m pytest <node-id> … -q`. No acceptance exists yet.
2. For `method=tdd`, require assertion-level red for each failing node.
   ImportError / collection ERROR alone is insufficient.
   For `method=check`, no red is required; a passing test can be frozen.
3. Compute `oracle_hashes` for the files. Create the acceptance once
   in the plan batch with `oracle_policy`, `test_ids`, `oracle_hashes`,
   and the derived `verify_command` together:

```bash
canon create --type score:acceptance \
  --subject "<task-slug>-frozen" \
  --payload '{"method":"tdd","oracle_policy":"frozen","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"python3 -m pytest tests/test_<area>.py::test_<case> -q","requirement":"R1","test_ids":["tests/test_<area>.py::test_<case>"],"oracle_hashes":["tests/test_<area>.py:sha256:<hex>"]}'
```

4. After the batch, run `orchestra check --acceptance <acceptance-id>
   --cwd <repo-or-worktree>`. For frozen TDD, expect fail and run
   `orchestra verify assertion-red` on its check-run JSON. Frozen check needs no red.

If frozen TDD cannot reach assertion-level red, return to the author
or obtain explicit parent approval to change policy. Do not silently
remove freeze fields or change `tdd` to `check`. Do not open plan review
while selected frozen acceptances lack complete freeze metadata.

`test_ids` is a JSON array of pytest node ids. `oracle_hashes` is a JSON
array of `relpath:sha256:<hex>` for their files. Never update an
existing acceptance to add a freeze after implementation starts.
