# Ensure the current project has an orchestra store

This plugin is installed once. Do **not** copy skills, rules, or this
repo into the work project. Store selection comes from the versioned
`.canon/config.json` and `.canon/store-binding.json`. In this repository,
records live in the shared SQLite database outside the worktree. Planning
commands opened from any worktree use that same database.

Requires `canon` and `orchestra` on PATH. Call both by name. Never
resolve a checkout path or a plugin root to run them.

## Which store

Dashboard and `orchestra store` resolve one SQLite database for this
repository: `~/.canon/<repo-name>/canon.db`. The tracked
`.canon/store-binding.json` selects `{"store":"global"}`, so every
worktree uses the same records. `.canon/config.json` selects the SQLite
backend, and `.canon/schemas/` keeps the schema snapshots used for
validation.

Run `canon` from any worktree in this repository. Do not pass a checkout
path or a plugin path to select the database. Use `orchestra store path`
to inspect the resolved location.

Run `canon backup` to create a retained backup under
`~/.canon/<repo-name>/backups/` before maintenance. SessionStart checks
the newest backup and creates one when it is older than 24 hours.

## Runtime commands

These are named commands, not files inside a checkout:

- `canon` writes and reads store records.
- `orchestra handoff`, `orchestra view plan|status|verification`, and
  `orchestra brief <work-item>` print derived views. They write no
  files.
- `orchestra check` and `orchestra close-batch` run acceptance and
  close work.
- `orchestra analyze <phase-slug>` checks a phase's specification,
  work-items, and acceptances for consistency. It writes no files.
- `orchestra review-brief` builds the phase-end reviewer brief.
  `orchestra suite policy`, `orchestra suite start`,
  `orchestra suite poll`, `orchestra suite collect`, and
  `orchestra suite record` run the configured phase suite and write
  its check-run.
- `orchestra store path` prints the resolved store;
  `orchestra store run -- <args>` runs `canon` against it.
- `orchestra verify` judges a claim in `.tuner/manifest.json`.

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

## Store records and commits

Records are stored in the SQLite database outside the Git worktree.
Database writes are not Git changes and must not be staged or committed.
The config, binding, and schema snapshots under `.canon/` are versioned
metadata and should be committed with code changes when they change.

A record edited by hand, outside the runtime, fails validation:

```
record revision tamper detected: .canon/records/.../rec-....md
```

Fix that by redoing the edit through `canon update` rather than by
hand-patching the file.
