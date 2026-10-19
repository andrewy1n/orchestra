# Ensure the current project has an orchestra store

This plugin is installed once. Do **not** copy skills, rules, or this
repo into the work project. The store is created in the **current
working tree** the first time `init`, `plan-phase`, or `engage` needs
records.

Requires `adaptive-artifacts` and `orchestra` on PATH. Call both by
name. Never resolve a checkout path or a plugin root to run them.

## Which store

Dashboard and `orchestra store` resolve **one** store: `local`
(`<repo>/.artifacts`) or `global` (`~/.artifacts/<repo-name>`). See
the README (store binding). Skills that shell out to
`adaptive-artifacts` should use the resolved store — pass `--store`
and `--contract` explicitly, or call through `orchestra store run --
<args>` — so a personal shell function that forces
`--store ~/.artifacts/$proj`
cannot redirect writes. For a new work repo, `init` creates the
**local** store under `<repo>/.artifacts`; pin it with
`.artifacts/store-binding.json` `{"store":"local"}` when you want that
choice shared across clones.

## Runtime commands

The bundled design and the runtime entry points are named commands,
not files inside a checkout:

- `orchestra contract` prints the bundled design. Add `--write <path>`
  to write it.
- `orchestra project-field rewrite <design.json>` aligns the design's
  `"project"` field.
- `orchestra check` and `orchestra close-batch` run acceptance and
  close work.
- `orchestra review-brief` builds the phase-end reviewer brief.
  `orchestra suite policy`, `orchestra suite start`,
  `orchestra suite poll`, `orchestra suite collect`, and
  `orchestra suite record` run the contracted phase suite and write
  its check-run.
- `orchestra store path` prints the resolved store;
  `orchestra store run -- <args>` runs `adaptive-artifacts` against it.
- `adaptive-artifacts` writes and reads store records.
- `aff` judges a claim in `.affidavit/manifest.json`.

Do not hardcode a plugin directory or a home checkout in a command.

## First run in a work repo

The current project id is `orchestra`.

If `.artifacts/project-design.json` exists, align its `"project"` field
with `orchestra project-field rewrite .artifacts/project-design.json`
from the work repo:

```bash
orchestra project-field rewrite .artifacts/project-design.json
```

The command does not ask. It returns one of three outcomes:

- `current` — `"project"` is already `orchestra`. The file is unchanged.
- `rewritten` — `"project"` was `affidavit` and is now `orchestra` in
  place. Do not ask again. Continue.
- `stopped` — `"project"` is any other value. The file is unchanged.
  **Stop.** Do not overlay or replace the design.

When the outcome is `current` or `rewritten`, check that the design
lists a `phase` record, a `constraint` record, an `assignment` record,
and an `execution-report` record, and that `work-item` has
`required_sections`. A design is current only when it also lists
`specification`, `design`, `assessment`, `integration-report`,
`release`, `feedback`, `backlog-item`, and `milestone`. If those are
missing, the bundled contract is newer (it predates staged task
lifecycle, phase records, dependency edges, the
assignment/execution-report dispatch loop, the evidence-loop records,
backlog capture, or milestones): show the user and replace
`.artifacts/project-design.json` only if they approve,
then `adaptive-artifacts resolve`. Do not replace on a no. This is a
one-time upgrade check at first touch, not a standing gate — once the
design is current, nothing in the other skills re-checks it before
dispatching.

If the design file does not exist yet:

```bash
orchestra store ensure
adaptive-artifacts resolve
adaptive-artifacts init
```

`orchestra store ensure` creates `.artifacts/` in the current
worktree and writes the bundled design there when it is missing. It
does not overwrite an existing design. `adaptive-artifacts init`
needs a git repo. If cwd is not git, leave design-only and tell the
user. Do not write a plan document or extra skill copies.

## Committing store writes

`validate` accepts an uncommitted record rewrite when the record matches
its own op log, so an `update`, `supersede`, or `close` batch does not
have to be committed before validating or before `hook-stop` runs.

Still commit store writes as part of the work they belong to — the
record diff is what shows a reader what changed and why. The subject
is `type(scope): summary`, where type is `feat`, `fix`, `docs`,
`refactor`, `test`, or `chore`, and the body is one or two sentences
on why:

```bash
git add .artifacts && git commit -m "$(cat <<'EOF'
chore(records): <what changed>

Commit the store write so a reader can see what changed and why.

EOF
)"
```

A record edited by hand, outside the runtime, fails validation:

```
record revision tamper detected: .artifacts/records/.../rec-....md
```

Fix that by redoing the edit through `adaptive-artifacts update` rather
than by hand-patching the file.
