# AGENTS.md

Orchestra runs product planning through verified code. See the [component map](README.md#components)
and [import boundaries](tests/test_boundaries.py) before moving code across packages.

Update the relevant `AGENTS.md` in the same change when an instruction becomes inaccurate.
Keep each rule at the narrowest scope where it applies, and link to its source when it already lives elsewhere.

## Canon

- Write records through `canon`. Only the parent session writes the store.
  Subagents return evidence and do not call `canon`.
- Run `canon validate` before finishing and before pushing. Fix every error.
- Worktrees share `~/.canon/<repo-name>/canon.db`. Run `canon` from any worktree.
  Never commit database changes. Commit relevant changes to versioned metadata
  under `.canon/` with the code they affect. Run `canon backup` before database maintenance.
- Tests use temporary stores. Keep test writes away from the real store.

## Code

- Call external programs through `CliTool` from `orchestra.tools`. See
  [the subprocess allowlist](tests/test_subprocess_rule.py) for existing exceptions.
- Comment only facts the code cannot show.
- Annotate all new code, including Python function and method parameters and return values.
  Avoid explicit `Any` and `typing.cast`. Narrow values instead.
  Each ignore comment must name the checker rule and give a factual reason in
  `# pyright: ignore[ruleName]`. See [basedpyright configuration](pyproject.toml).
- Use a fallback only when the product contract defines a substitute. Report
  required read failures as failures.
- Exercise the owning production API in regression tests. Mock only boundaries
  outside the behavior under test.

## Testing

- Run affected tests with `uv run pytest <files>`. Add
  `--confcutdir=tests/canon` or `--confcutdir=tests/tuner` for those trees.
- Before you close a task, run `uv run basedpyright`, Ruff check
  (`uvx ruff@0.13.1 check .`), and Ruff format check (`uvx ruff@0.13.1 format --check .`).
  Apply formatting with `uvx ruff@0.13.1 format .`.
- After an automated fix, bulk replace, or rename, review `git diff --stat` and
  removed lines. Search the affected code and entry points for retired names and run affected tests.
- See [Testing](README.md#testing) for the phase suite and brief and reviewer checks.
  See [frontend instructions](dashboard/frontend/AGENTS.md) for dashboard UI work.
- See [Cursor Cloud setup](dashboard/frontend/README.md#cursor-cloud) for cloud development.

## Git

- Use short, imperative Conventional Commit subjects.
- Push a branch and open a PR. Never push to protected `main`.
- Wait for all CI checks to pass and obtain human approval before a squash merge
  with `gh pr merge --squash` to keep `main` linear. This applies to admins too.
