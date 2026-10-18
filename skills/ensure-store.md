# Ensure the current project has an orchestra store

This plugin is installed once. Do **not** copy skills, rules, or this
repo into the work project. The store is created in the **current
working tree** the first time `init`, `plan-phase`, or `engage` needs
records.

Requires `adaptive-artifacts` on PATH.

## Which store

Dashboard and `orchestra.aa` resolve **one** store: `local`
(`<repo>/.artifacts`) or `global` (`~/.artifacts/<repo-name>`). See
the README (store binding). Skills that shell out to
`adaptive-artifacts` should use the resolved store — pass `--store`
and `--contract` explicitly, or call through `orchestra.aa` — so a
personal shell function that forces `--store ~/.artifacts/$proj`
cannot redirect writes. For a new work repo, `init` creates the
**local** store under `<repo>/.artifacts`; pin it with
`.artifacts/store-binding.json` `{"store":"local"}` when you want that
choice shared across clones.

## Plugin root

This skill file lives at `<plugin>/skills/<name>/SKILL.md`. The bundled
design is `<plugin>/contract/project-design.json`.

Resolve `<plugin>` in order:

1. `$CLAUDE_PLUGIN_ROOT` if that path contains `contract/project-design.json`
2. `$CURSOR_PLUGIN_ROOT` if that path contains `contract/project-design.json`
3. Directory two levels above this `SKILL.md` (skill-relative layout)

Do not hardcode `~/.cursor/plugins/local/orchestra` as a primary
path. Local sync installs still work when skills run from that tree
via step 3.

## First run in a work repo

The current project id is `orchestra`.

If `.artifacts/project-design.json` exists, align its `"project"` field
with `rewrite_project_field` in `<plugin>/orchestra/project_field.py`
before any overlay. From the plugin root, with cwd the work repo:

```bash
PYTHONPATH="<plugin>" python3 -c 'from orchestra.project_field import rewrite_project_field; print(rewrite_project_field(".artifacts/project-design.json"))'
```

The function does not ask. It returns one of three outcomes:

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
mkdir -p .artifacts
cp "<plugin>/contract/project-design.json" .artifacts/project-design.json
adaptive-artifacts resolve
adaptive-artifacts init
```

`adaptive-artifacts init` needs a git repo. If cwd is not git, leave
design-only and tell the user. Do not write a plan document or extra
skill copies.

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
