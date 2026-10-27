# AGENTS.md

orchestra is one product: product planning through verified code, run
by agents. The move to one repo is planned in
`docs/plans/monorepo-plan.md`.

## Layout

| Path | Contents |
|---|---|
| `orchestra/` | CLI, views, sessions, dispatch |
| `orchestra/canon/` | Record store and the `canon` CLI |
| `orchestra/tuner/` | Evidence layer behind `orchestra verify` |
| `orchestra/schemas/` | `score` and `conductor` schema modules |
| `orchestra/tuner/schemas/` | `tuner` schema module |
| `skills/`, `agents/`, `hosts/`, `installer/` | Host integration |
| `dashboard/` | tmux and web dashboards |
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

## Testing

Run `scripts/test.sh` before you close a task. While you edit, run the
affected test files with `uv run --no-project --with pytest --with textual python -m pytest <files>`.
Add `--confcutdir=tests/canon` or `--confcutdir=tests/tuner` for those
trees.
