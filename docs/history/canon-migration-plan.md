# canon migration plan

The target format is in `design/schema-modules.md`. Read it first. This plan
says who builds what, in which order, and how each part is proven.

## Decisions

| Topic | Decision |
|---|---|
| Name | The store becomes `canon`: Python package `canon`, CLI `canon`. The local directory `~/adaptive-artifacts` and the GitHub repo keep their names for now. The owner renames them later. |
| Cutover | Hard cut. canon reads only the new format. A one-shot migration converts each store. |
| Views | Orchestra renders views on demand. `.artifacts/views/` leaves git. |
| Domain write commands | Out of scope. Skills keep calling the store CLI, now `canon`. |
| Placement | `finding` and `investigation-observation` go to `aff`. `failed-attempt` and `proof-packet` go to `run`. |
| Unmerged affidavit branches | `phase/human-gates` and `phase/pyproject-pypi` stay as they are. Migrate them on rebase. |
| Landing | One branch per repo. Merge to the default branch after every suite passes and every store validates. No push. |
| Plugin | adaptive-artifacts stops being a plugin. Orchestra owns the session hooks. |
| Env vars | `ADAPTIVE_ARTIFACTS_ROOT` → `CANON_ROOT`. `ADAPTIVE_ARTIFACTS_READONLY` → `CANON_READONLY`. The default root stays `~/adaptive-artifacts`. |

## Repos and branches

| Repo | Default branch | Work branch | Worktree |
|---|---|---|---|
| `~/adaptive-artifacts` (canon) | `master` | `phase/canon` | `~/adaptive-artifacts/.worktrees/canon` |
| `~/adaptive-artifacts` (canon) | `master` | `phase/canon-migrate` | `~/adaptive-artifacts/.worktrees/canon-migrate` |
| `~/orchestra` | `main` | `phase/canon` | `~/orchestra/.worktrees/canon` |
| `~/orchestra` | `main` | `phase/canon-skills` | `~/orchestra/.worktrees/canon-skills` |
| `~/affidavit` | `main` | `phase/canon` | `~/affidavit/.worktrees/canon` |

## Rules for every task

- Work only in your worktree. Do not touch any repo's primary checkout.
- Do not write to any real store: no `.artifacts/` outside a test's temporary
  directory. Do not run the old `adaptive-artifacts` CLI against a real store.
- Do not change files under `~/.claude`, and do not install tools.
- Commit on your branch. Use Conventional Commits with an imperative, short
  subject and no ticket IDs. Add a body only when the subject cannot carry
  it. End every message with this trailer line:
  `Claude-Session: https://claude.ai/code/session_017bGRcqjs6WKsxYVALekj3x`
- Do not push. Do not merge.
- Add no comments that explain a change. Add a comment only for a fact the
  code cannot show.
- Finish with a report: what you built, the test command and its result, and
  every deviation from this plan, with the reason.

## Type map

| Old type | New type |
|---|---|
| `project:active-goal` | `plan:effort` |
| `project:current-position` | `plan:position` |
| `project:milestone`, `phase`, `specification`, `design`, `decision`, `constraint`, `work-item`, `acceptance`, `backlog-item`, `feedback`, `continuity-question` | `plan:<same>` |
| `project:assignment`, `assignment-amendment`, `execution-report`, `integration-report`, `assessment`, `release`, `proof-packet`, `failed-attempt` | `run:<same>` |
| `project:check-run`, `evidence-observation`, `evidence-binding`, `oracle-amendment`, `investigation-observation`, `finding` | `aff:<same>` |

Lifecycle map: old pattern `current-status` and `definition` and `decision`
→ `current`; `phase` and `task` → `staged`; `event`, `observation`, and
`instruction` → `event`; `question` → `question`; `finding` → `claim`.

## List fields

These string fields hold comma-separated values today. They become lists.
Split on `,`, strip each item, and drop empty items. An empty string becomes
`[]`.

| Type | Field | Item form |
|---|---|---|
| `plan:work-item` | `decisions` | `{"ref": "plan:decision"}` |
| `plan:work-item` | `requirements` | `{"type": "string"}` |
| `plan:design` | `decisions` | `{"ref": "plan:decision"}` |
| `plan:specification` | `requirements` | `{"type": "string"}` |
| `plan:acceptance` | `test_ids` | `{"type": "string"}` |
| `plan:acceptance` | `oracle_hashes` | `{"type": "string"}` |
| `plan:effort` | `merged_from` | `{"type": "string"}` (some records already hold a list) |
| `aff:check-run` | `failing_node_ids` | `{"type": "string"}` |
| `aff:evidence-observation` | `claim_ids` | `{"type": "string"}` |
| `aff:oracle-amendment` | `old_hashes`, `new_hashes` | `{"type": "string"}`, only if the old contract text or the data shows comma-separated values |

Prose fields stay strings, even when they contain commas: `decision.choice`,
`decision.alternatives`, `position.position`, `finding.basis`,
`constraint.applies_to`, and the singular `requirement` fields.

## Reference fields

Every old `payload_references` entry becomes a subject `ref`. Every `effort`
field becomes `{"ref": "plan:effort"}`. `relationships` change like this:

| Old relationship | New form |
|---|---|
| `supersedes`, `corrects` | Stay in `relationships`, ids unchanged |
| `depends_on` (ids) | `payload.depends_on`: the subjects of the target records |
| `informed_by` (ids) | `payload.informed_by`, pinned ids. Targets are `plan:acceptance` and `run:execution-report`. |
| `contradicted_by` (ids) | `payload.contradicted_by`, pinned ids |

`run:execution-report.assignment` holds a `rec-` id in 3 orchestra records.
The migration replaces each id with that record's subject.

## Waves

### Wave 1: run in parallel

**W1a: canon core.** Worktree `adaptive-artifacts/.worktrees/canon`.

1. Rename the package `src/adaptive_artifacts` to `src/canon`. Rename the
   distribution to `canon`. Expose only the `canon` script. Remove `aa` and
   `adaptive-artifacts`.
2. Remove the `tools/` shims. Move the suite in `tools/runtime/tests` into
   `tests/`.
3. Add the schema-module loader: the five built-in lifecycles, module
   validation, `config.json`, snapshots under `.artifacts/schemas/`, the
   `canon.schemas` entry point group, and declarative migrations.
4. Rewrite validation for the new field forms. Validate every write,
   references included. `validate` checks the whole store, and
   `--format json` prints the error list.
5. Make `depends_on` a payload field. Keep derive output the same: `ready`,
   `wave`, `corrected`, and inverse links.
6. Add `schemas sync`, `schemas add`, `schemas show`, and
   `init --schemas`.
7. Delete `design/contracts/`, `design/DESIGN.md`, `skills/`, `hooks/`, the
   plugin manifests, `.cursor/`, and the
   commands `resolve`, `lock`, `capture`, `contradict`, `handoff`, `view`,
   `watch`, `brief`, `hook-start`, and `hook-stop`. Delete `handoff.py`,
   `session_hooks.py`, `watch.py`, and `terminal.py` if nothing else
   uses them.
8. Update `README.md` and `AGENTS.md` for canon. Keep both short.

Done when: the suite passes with fixture modules in two namespaces, a
cross-namespace reference is checked on write, and each lifecycle's
transitions are covered by a test.

**W1b: schema modules.** Two worktrees: `orchestra/.worktrees/canon` and
`affidavit/.worktrees/canon`.

1. Write `orchestra/schemas/plan.json` and `orchestra/schemas/run.json`
   from `orchestra/contract/project-design.json`, the type map, the list
   fields, and the reference fields.
2. Write `affidavit/schemas/aff.json` from
   `affidavit/contract/project-design.json`, the same way.
3. Register each module in its `pyproject.toml` under
   `[project.entry-points."canon.schemas"]`, and include the JSON in the
   package data.
4. Translate the payload keys this way: required = `payload` minus
   `optional_payload`; `payload_enum` → `enum`; `required_sections` →
   `sections`; `purpose` stays. Infer scalar types from the data in
   `~/orchestra/.artifacts/records` and `~/affidavit/.artifacts/records`:
   read them, but never write to them.
5. Write `schemas/MAPPING.md` in orchestra. It lists every old type, every
   old field, and where each one went.

Done when: each module parses as JSON, matches the format in
`schema-modules.md`, and covers every type and field in the old contracts.

**W1c: legacy transform.** Worktree `adaptive-artifacts/.worktrees/canon-migrate`.

1. Write `src/canon/legacy.py`: a pure function from one old record dict to
   one new record dict. It applies the type map, the list fields, the
   reference fields, and the envelope rules from `schema-modules.md`. It does
   not compute revisions.
2. Write a store-level pass that resolves `depends_on` ids to subjects and
   execution-report assignment ids to subjects. It reports every reference it
   cannot resolve.
3. Test it on fixtures copied from real records: one or more per old type.

Done when: the tests pass, and a dry run over a copy of
`~/orchestra/.artifacts/records` reports counts per type and every broken
reference. Run the dry run on a copy in a temporary directory only.

### Wave 2: after Wave 1

The parent merges `phase/canon-migrate` into canon's `phase/canon` first.

**W2a: orchestra code.** Worktree `orchestra/.worktrees/canon`.

1. Replace every `adaptive_artifacts` import with `canon`. Replace every
   `adaptive-artifacts` CLI call in code with `canon`.
2. Port the views to orchestra code: `orchestra handoff`,
   `orchestra view plan|status|verification`, and
   `orchestra brief <work-item>`. Keep the current output as close as you
   can. The old renderers in canon's `handoff.py` and `derive.py` are the
   reference.
3. Add `orchestra hook-start` (inject the handoff) and `orchestra hook-stop`
   (validate, and block only on errors absent from the baseline). Port them
   from canon's `session_hooks.py`. Point `hosts/*` at them.
4. Update the dashboard: new type names, list fields, `payload.depends_on`,
   and `plan:effort`.
5. Delete `contract/project-design.json`, `orchestra/contract.py`,
   `orchestra/project_field.py`, and their CLI commands. `phase_gate` moves
   to `config.json` `settings.run`. Update `orchestra/suite.py` to read it
   there.
6. Rewrite `test_contract_self_consistency.py` and
   `test_skill_contract_consistency.py` against the schema modules. Update
   every fixture.
7. Remove the plugin dependency on adaptive-artifacts from
   `.claude-plugin/plugin.json` and from the marketplace file.
8. Add `.artifacts/views/` to `.gitignore`.

Done when: the full orchestra suite passes against canon `phase/canon`
(`CANON_ROOT=~/adaptive-artifacts/.worktrees/canon`).

**W2b: orchestra skills and docs.** Worktree `orchestra/.worktrees/canon-skills`.

1. In `skills/`, `agents/`, and `README.md`: rename every type with the type
   map. Replace `adaptive-artifacts` with `canon`. Pass list fields as JSON
   arrays. Pass `depends_on` and `informed_by` as payload fields, not
   `--rel`.
2. Replace view regeneration steps with the orchestra commands from W2a.
   Remove steps that write `views/` files.
3. Rewrite `skills/ensure-store.md` for `config.json`, `canon init
   --schemas plan,run,aff`, and `canon schemas sync`. Remove
   `project-field` and the contract-replace procedure.
4. Fold the rules that orchestra still needs from adaptive-artifacts'
   `artifact-runtime` skill into `skills/kinds-and-focus.md`: capture at the
   event, single writer, views are derived.
5. Update the install sections of `README.md`: no adaptive-artifacts
   plugin, `uv tool install` for canon.

Done when: no file names `project:`, `adaptive-artifacts`, `--rel
depends_on`, or `views/` paths, except in a changelog.

**W2c: affidavit.** Worktree `affidavit/.worktrees/canon`.

1. Replace imports and CLI calls with `canon`.
2. Remove the resolved-contract logic in `affidavit/observation.py`.
3. Delete `contract/project-design.json`. Tests build stores with
   `canon init --schemas plan,run,aff`.
4. Update `README.md`, `AGENTS.md`, and `CLAUDE.md`.

Done when: the affidavit suite passes against canon `phase/canon`.

### Wave 3: parent, inline

1. Merge `phase/canon-skills` into orchestra `phase/canon`.
2. Add `canon migrate-legacy <store>`. It reads the old store, applies
   `legacy.py`, seeds one op chain per record through canon's op-log API,
   rewrites `history/` with the same transform, writes `config.json` and the
   snapshots, and removes `meta.json`, `project-design.json`,
   `resolved-contract.json`, and `views/`.
3. Migrate the stores in the work worktrees: orchestra, affidavit, and
   canon's own store.
4. Prove each migration:
   - The record count per type equals the count before.
   - `ready` and `wave` are equal for every work-item, before and after.
   - `canon validate` reports no errors.
   - `dashboard --once` prints the same frame before and after.
5. Resolve the one known broken reference by hand: phase effort
   `evidence-layer` in orchestra's store.

### Wave 4: landing

1. Run every suite. Merge each `phase/canon` into its default branch.
2. Migrate the primary checkouts' stores, then commit each store.
3. Migrate `~/website` and `~/aa-plugin-dogfood`. Leave them uncommitted.
4. With the owner's approval: install canon and orchestra with
   `uv tool install`, point `~/.claude/settings.json` hooks at
   `orchestra hook-start` and `orchestra hook-stop`, and uninstall the
   adaptive-artifacts plugin. Today both the settings hook and the plugin run
   `hook-start`, so the hooks fire twice.

## Out of scope

- Domain write commands in orchestra and affidavit.
- The planner split out of orchestra.
- The GitHub repo rename and the local directory rename.
- The phase-close step (see the open question in `schema-modules.md`).
