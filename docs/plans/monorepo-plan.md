# Monorepo plan

orchestra becomes one product in one repo. canon and affidavit move into
`~/orchestra`. This plan says what moves where, what every part is called, and
how each phase is proven.

## Decisions

| Topic | Decision |
|---|---|
| Host repo | `~/orchestra` absorbs canon (`~/adaptive-artifacts`) and affidavit (`~/affidavit`). |
| History | Squash on import: one commit per imported component. The old repos keep their history until Phase 3. |
| Packaging | One distribution, `orchestra`. One `pyproject.toml`. Local install only, no PyPI. |
| Imports | Every component is a subpackage: `orchestra.canon`, `orchestra.tuner`, and later `orchestra.composer`, `orchestra.score`, `orchestra.conductor`, `orchestra.stage`. |
| Binaries | `orchestra` for all work, and `canon` as the low-level store tool. `aff` and `aa` are removed. |
| CLI verbs | Task verbs: `orchestra idea`, `orchestra plan`, `orchestra run`, `orchestra verify`, `orchestra handoff`. Component names stay internal. |
| Namespaces | Namespace = package name: `composer`, `score`, `conductor`, `tuner`. |
| Store directory | `.artifacts/` → `.canon/`. `ARTIFACTS_STORE` → `CANON_STORE`. `~/.artifacts/<repo>` → `~/.canon/<repo>`. |
| Dependencies | No stdlib-only rule. Add a dependency when it pays for itself. |
| Phase gate | Full monorepo suite, `required`. |
| Store merge | One store in `~/orchestra/.canon/`. Same-subject efforts merge into one with `merged_from`. Other real subject conflicts get a component prefix. |
| Docs | `design/` holds specs. `docs/` holds plans, guides, usage and history. |
| Old remotes | Delete `andrewy1n/adaptive-artifacts` and `andrewy1n/affidavit` on GitHub after a `git bundle` backup and owner confirmation. |
| Old stores | Delete canon's `archive/`, `~/aa-plugin-dogfood`, and the empty `~/.artifacts/*` global stores. |
| Ideas | `composer:idea` and `composer:area` live in `orchestra.composer`; handoff, dashboard, and `engage` use ideas for parked work. |
| Execution | Run directly in a session. No work-items or acceptances. The effort and phase records track progress. |

## Names

| Component | Package | Namespace | Owns |
|---|---|---|---|
| Product | `orchestra` | — | CLI, views, dashboard, sessions |
| Record store | `orchestra.canon` | — | records, schemas, lifecycles, op log, validation |
| Product planning | `orchestra.composer` | `composer` | area, idea |
| Work planning | `orchestra.score` | `score` | effort, position, milestone, phase, specification, design, decision, constraint, work-item, acceptance, continuity-question |
| Dispatch | `orchestra.conductor` | `conductor` | assignment, execution-report, integration-report, assessment, release, proof-packet, failed-attempt |
| Evidence | `orchestra.tuner` | `tuner` | check-run, finding, evidence-binding, oracle-amendment, observations |
| Host adapters | `orchestra.stage` | — | hooks, installer, hosts |

### Rename map

| Old | New |
|---|---|
| `plan:<type>` | `score:<type>` |
| `run:<type>` | `conductor:<type>` |
| `aff:<type>` | `tuner:<type>` |
| `records/plan__<type>/` etc. | `records/score__<type>/` etc. |
| package `canon` | `orchestra.canon` |
| package `affidavit` | `orchestra.tuner` |
| `aff <command>` | `orchestra verify <command>` |
| `orchestra/aa.py` | `orchestra/store.py` |
| `.artifacts/` | `.canon/` |
| `ARTIFACTS_STORE` | `CANON_STORE` |
| `~/.artifacts/<repo>` | `~/.canon/<repo>` |
| entry point `plan`, `run` = `orchestra.schemas` | `score`, `conductor` = `orchestra.schemas` |
| entry point `aff` = `affidavit.schemas` | `tuner` = `orchestra.tuner.schemas` |

The entry point group stays `canon.schemas`, and `CANON_SCHEMA_PATH` keeps
its name. Both are canon's own names.

### Record subjects

A subject names a record. It is not a component name.

- Closed records keep their subject. Examples: `strip-aff-verbs`,
  `aa-cli-surface`. These subjects describe work as it was named when it was
  done.
- Live records rename a subject that carries an old name. A live record is an
  effort with status `open`, a staged record that is not `done` or
  `withdrawn`, or a question that is `open`. Rewrite every reference to it.
  Confirm the list with the owner before the rewrite.

## Phase 0: prepare

1. Review the two dirty worktrees with the owner: `orchestra
   phase/milestone-nav` (2 files) and `orchestra phase/web-dashboard` (1 file).
   Commit, merge or drop each one.
2. Drop `affidavit phase/pyproject-pypi`. PyPI is out of scope.
3. Remove every merged worktree and its branch in all three repos. Remove the
   `orchestra/.worktrees/adaptive-artifacts` symlink.
4. Write a `git bundle --all` of `~/orchestra`, `~/adaptive-artifacts` and
   `~/affidavit` to `~/backups/monorepo-2026-10/`. Run `git bundle verify` on
   each.
5. Delete `~/aa-plugin-dogfood` and the empty `~/.artifacts/` directory.

Done when: `git worktree list` shows only the primary checkout in each repo,
and the three bundles verify.

## Phase 1: move

Work on branch `phase/monorepo` in `~/orchestra`.

1. Import `~/adaptive-artifacts/src/canon` to `orchestra/canon/` in one
   commit. Import `~/affidavit/affidavit` to `orchestra/tuner/` in one commit.
2. Move tests to `tests/canon/` and `tests/tuner/`. orchestra's own tests stay
   in `tests/` until Phase 2.
3. Rewrite imports: `canon.` → `orchestra.canon.`, `affidavit.` →
   `orchestra.tuner.`. Remove the git-URL dependencies and the `evidence`
   extra. Declare test dependencies (`pytest`, `pytest-xdist`, `textual`) in
   `pyproject.toml`.
4. Expose two scripts: `orchestra` and `canon`. Fold the affidavit CLI into
   `orchestra verify`. Delete `bin/aff` and any `aa` alias. Rename
   `orchestra/aa.py` to `orchestra/store.py`.
5. Apply the store directory rename in canon, hooks, skills, agents, hosts and
   docs.
6. Apply the namespace rename. Move the module files to
   `orchestra/score/schemas/score.json`, `orchestra/conductor/schemas/conductor.json` and
   `orchestra/tuner/schemas/tuner.json`. Set each version to `1.0.0`. Update
   every type string in code, skills, agents, views and tests.
7. Add `canon merge <source-store>`. It copies records, history and logs into
   the target store, rewrites types by a namespace map, aborts on an id
   collision, and applies the subject rules above. Use it to build
   `~/orchestra/.canon/` from the orchestra, affidavit and canon stores.
   Known conflict: phase `evidence-kind` exists in both orchestra (effort
   `workflow-loop`) and affidavit (effort `evidence-layer`). The affidavit
   phase becomes `tuner-evidence-kind`.
8. Set `settings.conductor.phase_gate.suite` to the full suite with `gate:
   required`. Use `uv run pytest tests -q -n 4 -m "not tmux" && uv run pytest
   tests -q -m tmux`.
9. Delete `orchestra/canon/legacy.py` and `canon migrate-legacy`. No legacy
   store is left after Phase 0.
10. Re-create `~/website/.canon/` with `canon init --schemas
    score,conductor,tuner`. The old store there is empty and untracked.
11. Docs: move `schema-modules.md` to `design/canon/`. Move the canon
    migration plan to `docs/history/`. Move `DOGFOOD.md` to
    `docs/history/dogfood-trial.md`, and replace its header with one line
    that names the layout it describes. Merge the three READMEs into one root
    README. Merge the `AGENTS.md` files into one root file, and drop the
    stdlib-only rule.
12. Add `tests/test_names.py`. It fails when a tracked file outside
    `docs/history/` contains an old name: `affidavit`, `adaptive-artifacts`,
    `aff`, `aa`, `.artifacts`, `ARTIFACTS_STORE`, `plan:`, `run:`, `aff:`.
13. Reinstall with `uv tool install --editable ~/orchestra`.

Done when: the full suite passes, `canon validate` reports no errors on the
merged store, `orchestra handoff` renders every live effort, and
`tests/test_names.py` passes.

## Phase 2: split orchestra

1. Create `orchestra.score`, `orchestra.conductor` and `orchestra.stage`. Move
   each module to its owner. Draft map, settled at phase start from the import
   graph:

   | Module | Owner |
   |---|---|
   | `schemas/score.json`, effort rollup | `score` |
   | `schemas/conductor.json`, `suite.py`, `close_batch.py`, `policy.py`, `reviewer.py` | `conductor` |
   | `hooks.py`, `install.py`, `installer/`, `runtime_deps.py`, `hosts/` | `stage` |
   | `cli.py`, `views.py`, `view_cli.py`, `store.py`, `sessions.py`, `dashboard/` | `orchestra` |

2. Move each module file into its package. Update the entry points.
3. Add `tests/test_boundaries.py`. It fails on any import against this
   direction: `canon` ← `score` ← `conductor`; `canon` ← `tuner`; all
   components ← `stage` and `orchestra`. Settle whether `conductor` may import
   `tuner` at phase start.
4. Move tests to `tests/<component>/`. Add a short `AGENTS.md` to each
   component.

Done when: the full suite passes and `tests/test_boundaries.py` passes.

## Phase 3: retire the old repos

1. Confirm with the owner. Then delete `andrewy1n/adaptive-artifacts` and
   `andrewy1n/affidavit` on GitHub.
2. Delete `~/adaptive-artifacts` and `~/affidavit` after a second owner
   confirmation. The bundles from Phase 0 keep their history.

Done when: both remotes return 404, and the Phase 0 bundles still verify.

## Phase 4: host cutover

The `~/.claude/settings.json` hooks already call `orchestra hook-start
--claude` and `orchestra hook-stop --claude`. The adaptive-artifacts plugin is
still installed, so the session hooks fire twice.

1. Get owner approval. Then uninstall `adaptive-artifacts@adaptive-artifacts`
   and remove its marketplace entry and cache.
2. Start a new session in `~/orchestra`. Check that the handoff appears once
   and reads from `.canon/`.

Done when: one handoff appears per session start, and `orchestra hook-stop`
runs once per stop.

## Follow-up effort

- Composer ideas replace the old score backlog types; ship `orchestra idea`, a
  triage skill, and `orchestra view roadmap`.
- Teach `engage` to start from an untriaged idea.
- Docs ownership: the product manages its own `docs/` tree.
