# Ensure the current project has an orchestra store

This plugin is installed once. Do **not** copy skills, rules, or this
repo into the work project. The store is created in the **current
working tree** the first time `init`, `plan-phase`, or `engage` needs
records.

Requires `canon` and `orchestra` on PATH. Call both by name. Never
resolve a checkout path or a plugin root to run them.

## Which store

Dashboard and `orchestra store` resolve **one** store: `local`
(`<repo>/.canon`) or `global` (`~/.canon/<repo-name>`). See
the README (store binding). Skills that shell out to `canon` should
use the resolved store — pass `--store` explicitly, or call through
`orchestra store run -- <args>` — so a personal shell function that
forces `--store ~/.canon/$proj` cannot redirect writes. For a new
work repo, `init` creates the **local** store under
`<repo>/.canon`; pin it with `.canon/store-binding.json`
`{"store":"local"}` when you want that choice shared across clones.

## Runtime commands

These are named commands, not files inside a checkout:

- `canon` writes and reads store records.
- `orchestra handoff`, `orchestra view plan|status|verification`, and
  `orchestra brief <work-item>` print derived views. They write no
  files.
- `orchestra check` and `orchestra close-batch` run acceptance and
  close work.
- `orchestra review-brief` builds the phase-end reviewer brief.
  `orchestra suite policy`, `orchestra suite start`,
  `orchestra suite poll`, `orchestra suite collect`, and
  `orchestra suite record` run the configured phase suite and write
  its check-run.
- `orchestra store path` prints the resolved store;
  `orchestra store run -- <args>` runs `canon` against it.
- `aff` judges a claim in `.tuner/manifest.json`.

Do not hardcode a plugin directory or a home checkout in a command.

## Reference fields

A payload field that names another record holds that record's
**subject**, never its `rec-…` id. This covers `effort`, `milestone`,
`phase`, `work_item`, `assignment`, `acceptance`, and each entry of
`depends_on`. For example, an execution-report sets
`"assignment":"<task-slug>"`.

`canon` checks every reference when it writes. A write fails when no
record of the target type has that subject. Write the target record
first. An empty string skips the check.

Pinned fields take a record id instead: `informed_by` and
`contradicted_by` (JSON arrays of ids). The check-run `criterion_id`
is a plain string: an acceptance id, or a phase-level criterion such
as `<phase-slug>-review` or `<phase-slug>-suite`.

List fields are JSON arrays: `requirements`, `decisions`, `test_ids`,
`oracle_hashes`, `failing_node_ids`, `claim_ids`, `old_hashes`,
`new_hashes`, `merged_from`, `depends_on`.

## First run in a work repo

A store is marked by `.canon/config.json`. If it exists, the store
is ready. Do not run `init` again.

If it does not exist, run this from the work repo:

```bash
canon init --schemas score,conductor,tuner
```

`canon init` needs a git repo. If cwd is not git, say so and stop. Do
not write a plan document or extra skill copies.

After you upgrade orchestra or tuner, bring the store schemas up
to date:

```bash
canon schemas sync
```

`canon` validates against the schema snapshots in
`.canon/schemas/`, not against the installed tools.

## Phase gate

The phase suite policy lives in `.canon/config.json` under
`settings.conductor.phase_gate`:

```json
{"settings": {"conductor": {"phase_gate": {"suite": {"mode": "none", "command": "", "gate": "required"}}}}}
```

Read it with `orchestra suite policy`. Do not waive it. A human
changes it in `config.json`.

## Committing store writes

`validate` accepts an uncommitted record rewrite when the record matches
its own op log, so an `update`, `supersede`, or `close` batch does not
have to be committed before validating or before the Stop hook runs.

Still commit store writes as part of the work they belong to — the
record diff is what shows a reader what changed and why. The subject
is `type(scope): summary`, where type is `feat`, `fix`, `docs`,
`refactor`, `test`, or `chore`, and the body is one or two sentences
on why:

```bash
git add .canon && git commit -m "$(cat <<'EOF'
chore(records): <what changed>

Commit the store write so a reader can see what changed and why.

EOF
)"
```

A record edited by hand, outside the runtime, fails validation:

```
record revision tamper detected: .canon/records/.../rec-....md
```

Fix that by redoing the edit through `canon update` rather than by
hand-patching the file.
