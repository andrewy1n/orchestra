# AGENTS.md

orchestra is one product: product planning through verified code, run
by agents. The move to one repo is planned in
`docs/plans/monorepo-plan.md`.

## Layout

| Path | Contents |
|---|---|
| `orchestra/` | CLI, views, sessions, store access |
| `orchestra/canon/` | Record store and the `canon` CLI |
| `orchestra/tuner/` | Evidence layer behind `orchestra verify` |
| `orchestra/score/` | Work planning: the `score` schema module |
| `orchestra/conductor/` | Dispatch: check, close-batch, suite, reviewer, and the `conductor` schema module |
| `orchestra/stage/` | Session hooks and the install bridge |
| `skills/`, `agents/`, `hosts/`, `installer/` | Host integration |
| `dashboard/` | web dashboard |
| `design/` | Specs |
| `docs/` | Plans, guides and history |

## Live protocol

This repo's memory is `.canon/`. Write records with the `canon` CLI.
Never edit a record file by hand. Run `canon validate` before you finish,
and fix every error.

Only the parent session writes the store. Subagents return evidence in
their response. They do not call `canon`.

## Rules

- Tests build temporary stores. Never write to a real `.canon/` store in
  a test.
- Do not add comments that explain a change. Comment only a fact the
  code cannot show.
- Use Conventional Commits. Keep the subject short and imperative.
- The Python type gate is basedpyright. Annotate all new code. Do not
  use or suggest mypy.
- After `ruff --fix`, a bulk replace, or a rename script, review
  `git diff --stat` and the removed lines. Grep for the old name inside
  strings, f-strings, module paths and entry points. Run the affected
  tests before you go on.

## Git

- `main` is protected. Never push to it. Push a branch and open a PR.
- A PR merges only when all CI checks pass. Admins follow the same rule.
- Merge with `gh pr merge --squash`. `main` requires linear history.
- Canon records live in the shared SQLite database at
  `~/.canon/<repo-name>/canon.db`. Do not stage or commit database changes.
- Commit changes to versioned store metadata such as `.canon/config.json`,
  `.canon/store-binding.json`, and `.canon/schemas/` with the code they affect.
- Run `canon validate` before you push.
- Run `canon` from any worktree in this repository. The global binding points
  each worktree to the same database.
- Run `canon backup` to create a retained database backup before maintenance.
- Ask the user before you merge, unless an active constraint says otherwise.

## Testing

While you edit, run the affected test files with `uv run pytest <files>`.
Add `--confcutdir=tests/canon` or `--confcutdir=tests/tuner` for those
trees.

Before you close a task, run the test files for the code you changed.
Run the three pytest commands in the README Testing section only at phase
end, or when you change shared code (config, store, CLI entry points).
CI runs the full suite on every push.

## TypeScript and Svelte

The dashboard UI lives in `dashboard/frontend`. Run the commands below from that directory.

- Use strict types. Do not use `any` or `@ts-ignore` without a one-line reason.
- Follow the comment rule in Rules.
- Put one component in each `.svelte` file.
- Put tests beside the source as `*.test.ts`.
- Do not format by hand. Let the formatter do it.
- Before you close a task, run `npm run lint`, `npm run check`, and `npm test`.
