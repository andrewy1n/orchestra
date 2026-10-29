# orchestra

One product for a software-engineering loop run by agents:
classify the ask, plan only the focused effort, execute independent
tasks with parallel subagents, verify with TDD, checks, or findings.
Install this repo as a plugin. It is not a template you copy into
other projects.

## Components

| Package | Namespace | Role |
|---|---|---|
| `orchestra` | — | CLI, views, sessions, store access |
| `orchestra.canon` | — | Record store and the `canon` CLI |
| `orchestra.score` | `score` | Work planning record types |
| `orchestra.conductor` | `conductor` | Dispatch: check, close-batch, suite, reviewer |
| `orchestra.tuner` | `tuner` | Evidence: verdict, claims, audit, binding (`orchestra verify`) |
| `orchestra.stage` | — | Session hooks and the install bridge |

Each schema module registers in the `canon.schemas` entry point group.
canon validates every store against snapshots of these modules.

The plan is a derived view over records. Only the **focused effort**
is written; for delivery-shaped work, only the **current phase** is
materialized as `work-item` + `acceptance`.

## Quick start

1. Install **canon** and the **orchestra** plugin (see Install).
2. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). It runs the web dashboard.
3. In your project, run the `init` skill once. It runs `canon init --schemas score,conductor,tuner` and creates the store the dashboard reads.
4. Run `dashboard/bin/web` from inside your repo to open the web dashboard.

Run acceptance checks with `orchestra check --acceptance <id>` (see
[Install with the CLI](#install-with-the-cli)).

## Kinds

`kind` is data on the goal and each work-item, not a new skill:

| Kind | Use |
|---|---|
| `deliver` | Specified change; done is a binary check |
| `repair` | Something is wrong; diagnose, then fix |
| `evaluate` | The work is a campaign or comparison |
| `incidental` | One-off; no records if it fits this chat |

Focus is a subject string (which effort this chat is on). An effort
is a product area; new work in it is a new phase. Optional
`score:milestone` records group phases under a time-bounded
outcome; focus stays the effort. Other live goals stay live; a
finished effort closes with `status: closed`. A merged effort lists
the old slugs in `merged_from`. Each running phase keeps its own
position, so chats on different phases of one effort do not collide.
Handoff groups by `effort`. See [skills/kinds-and-focus.md](skills/kinds-and-focus.md).

## Install

The orchestra plugin is not in Anthropic's official marketplace.

### uv tool install

Install the package first. It provides the `orchestra` and `canon`
commands:

```bash
uv tool install --editable ~/orchestra
```

### Claude Code

Install canon (above), then add the orchestra marketplace and plugin:

```bash
claude plugin marketplace add andrewy1n/orchestra
claude plugin install orchestra@orchestra -y
```

Install id is `orchestra@orchestra`. If a marketplace with that name
already points elsewhere: `claude plugin marketplace remove orchestra`
then add again.

### Cursor

Install canon with `uv tool install` (above), then clone and sync
orchestra:

```bash
git clone https://github.com/andrewy1n/orchestra.git
./scripts/sync-plugin.sh
```

Then reload Cursor so it picks up `~/.cursor/plugins/local/orchestra`.
Or install from the repository URL in the Cursor plugin flow.

#### Codex / other Agent Skills hosts

Use the installer's skills profile when one exists: `npx skills add -a codex`
(or `-a gemini-cli`, `-a github-copilot`, `-a cline`, `-a windsurf`), as listed
under [Install with the CLI](#install-with-the-cli). The installer runs that
tail for a `kind: skills` row and records the profile in the registration.

To install by hand, copy or symlink each generated skill directory into the
host's skills directory: `engage`, `init`, `settle-phase`, `plan-phase`,
`execute-phase`, `verify-work`, `triage-ideas`, and `analyze-sessions`. Every directory is
self-contained: its `SKILL.md` and its `references/` folder travel together.
The generated `references/` copies already contain `kinds-and-focus.md`,
`ensure-store.md`, and `se-reviewer.md`, so no shared file needs to sit two
levels above a `SKILL.md`. Install canon with `uv tool install` (above)
so `canon` is on PATH.

## Install with the CLI

The installer writes one host payload per provider. Native hosts get
`skills/` and their host-shaped files; `kind: skills` hosts
delegate to `npx skills add`. It is idempotent: one registration per host
per install scope, and a second run changes nothing.

With no host flags on an interactive terminal, `install` opens a
host-selection wizard. It lists every provider with project and global
detection, defaults to the detected hosts, and asks for scope and mode
before printing the plan and asking for confirmation. In a script or CI
run it selects the detected hosts instead. If no host is detected, it
exits 2 and asks for `--all`, `--only`, or `--interactive`.

### CLI install

Put the `orchestra` console script on PATH:

```bash
uv tool install "git+https://github.com/andrewy1n/orchestra.git@<ref>"
```

Replace `<ref>` with a branch, tag, or commit. The console script serves the
subcommands listed under [CLI](#cli). Host installs run from a checkout as
`./bin/orchestra install`, because the installer reads `skills/`,
`agents/`, and `hosts/` from that tree.

### Host matrix

This table matches `installer/providers.json`. `Provider id` is the `--only`
value. A native host installs at the project root by default and at the
global root with `--global` or `--scope global`. A `kind: skills` host
delegates to the `npx skills add` profile in the last column; native hosts
have no profile. Run `./bin/orchestra install --list` to print the same
matrix with current project and global detection.

| Host | Provider id | Kind | Project root | Global root | Skills profile |
|---|---|---|---|---|---|
| Claude Code | `claude` | native | `.claude` | `.claude` | — |
| Cursor | `cursor` | native | `.cursor` | `.cursor` | — |
| OpenCode | `opencode` | native | `.opencode` | `.config/opencode` | — |
| Codex | `codex` | skills | `.codex` | `.codex` | `codex` |
| Gemini CLI | `gemini` | skills | `.gemini` | `.gemini` | `gemini-cli` |
| GitHub Copilot | `copilot` | skills | `.github` | `.copilot` | `github-copilot` |
| Cline | `cline` | skills | `.cline` | `.cline` | `cline` |
| Windsurf | `windsurf` | skills | `.windsurf` | `.codeium/windsurf` | `windsurf` |

### Hooks

Native hosts get optional session hooks when their payload declares them.
Claude merges `SessionStart` and `Stop` hooks into `.claude/settings.json`
(or `~/.claude/settings.json` with `--global`), which is where Claude reads
project and user hooks. Cursor writes `.cursor/hooks.json`, and OpenCode
writes `plugins/plugin.js` under its root (`.opencode/plugins/plugin.js` for
a project install, `~/.config/opencode/plugins/plugin.js` with `--global`).
`orchestra hook-start` injects the handoff, and `orchestra hook-stop`
validates the store and blocks only on new errors. A host payload that
omits hooks still installs cleanly: the skills call `orchestra handoff`
themselves when the handoff was not injected.

### Detect and choose

`--list` prints every provider with its project and global detection status
and writes nothing:

```bash
./bin/orchestra install --list
```

`install` with no host flags on a TTY launches the host-selection wizard. It
accepts provider numbers, ids, ranges, comma- or space-separated values,
`all`, or `quit`; a blank answer selects the detected hosts. It then asks
for project or global scope (default project) and symlink or copy mode
(default symlink), prints the full plan, and asks before writing.
`--interactive` forces the wizard without a TTY, and
`--non-interactive`/`--yes` suppresses prompts. With no host flags and no
TTY, the installer uses detected hosts; if none are detected it exits 2
with guidance and writes nothing.

```bash
./bin/orchestra install --interactive
./bin/orchestra install --yes --only claude
```

### Dry run first

Run a dry run before touching a host. It prints the plan and writes nothing:

```bash
./bin/orchestra install --all --dry-run
```

Then install one host, or every host with `--all`:

```bash
./bin/orchestra install --only claude
./bin/orchestra install --only cursor
./bin/orchestra install --only opencode
./bin/orchestra install --only codex
./bin/orchestra install --only gemini
./bin/orchestra install --only copilot
./bin/orchestra install --only cline
./bin/orchestra install --only windsurf
```

A `kind: skills` row runs its `npx skills add` tail instead:

```bash
npx skills add -a codex
npx skills add -a gemini-cli
npx skills add -a github-copilot
npx skills add -a cline
npx skills add -a windsurf
```

If `npx` is unavailable or exits non-zero, the adapter falls back to a plain
skills-directory install and says so. The registration records the profile;
`--uninstall` removes the registration and leaves the profile managed by
`npx skills`.

### Scope and flags

| Flag | Effect |
|---|---|
| `--only <id>` | Install one provider; repeat for more. Default is the detected hosts. |
| `--all` | Select every provider in the matrix. |
| `--list` | Print the matrix with project/global detection and write nothing. |
| `--scope <scope>` | Install into `project` (default) or `global` user directories. |
| `--global` | Alias for `--scope global`; cannot be combined with `--scope`. |
| `--interactive` | Force the wizard even when standard input is not a TTY. |
| `--non-interactive`, `--yes` | Never prompt; use explicit flags or detected hosts. |
| `--dry-run` | Print the plan and write nothing. |
| `--copy` | Copy the payload instead of symlinking to the checkout. |
| `--uninstall` | Remove exactly what the adapter registered. |
| `--home <dir>` | Redirect the whole install under DIR (tests, throwaway homes). |

The default is a project install with symlinks, so keep the checkout. Use
`--copy` for a standalone snapshot, `--scope global` or `--global` for the
user directories in the matrix, and `--uninstall` to remove what the
registration recorded:

```bash
./bin/orchestra install --only claude --copy
./bin/orchestra install --only claude --global
./bin/orchestra install --only claude --uninstall
```

## Use

In whatever repo you are building:

| Skill | When |
|---|---|
| `engage` | Classify kind + focus, then hand off |
| `triage-ideas` | Assign a product area, create an area, or dismiss open ideas with no area |
| `init` | First time on a repo, or a new effort subject |
| `settle-phase` | Settle the approach for a phase (spec + design when structured) before planning |
| `plan-phase` | Approach settled; write tasks, then wait for plan review |
| `execute-phase` | Dispatch ready work in waves to subagents |
| `verify-work` | Show a task is done (check-run and/or finding) |

On first use, `init`, `plan-phase`, or `engage` runs
`canon init --schemas score,conductor,tuner` in that repo. The store is marked
by `.canon/config.json`. Skills stay in the plugin. After a tool
upgrade, run `canon schemas sync`.

`init` writes goal, kind, and a `score:phase` record for every phase
it can currently name (all `planned`) — not work-items. `plan-phase`
materializes this focus's tasks and promotes the current phase to
`in_progress` with its real plan in the body.

Task state is the work-item's lifecycle (`planned -> in_progress ->
done`, plus `withdrawn`/`superseded`), not a payload flag. Dependencies
are `depends_on` edges between work-items; readiness and wave are
derived by the engine at read time (`derived.ready`, `derived.wave`) —
nothing writes them.

`plan-phase` sets each work-item's `executor` to `inline` or `subagent`.
Every task in a wave uses the same executor. Missing `executor` means
`subagent`. It records the implementation recipe and the phase run facts
(size as `one sitting` or `more than one`, the human stops, and the areas
parallel tasks share) before plan review.

The phase body includes a `## Landing` section with branch
`phase/<phase-slug>`, worktree
`<repo>/.worktrees/<phase-slug>`, base `main`, and these
close actions: commit code on the phase branch, merge that branch
into `main`, then commit the store on the primary checkout. Push
appears only when it is one of the human stops. Incidental work has
no Landing section. A phase body that omits Landing is not ready
for plan review.

A one-shot that fits in one chat and is not an interrupt gets no
records. An interrupt or a chore that may span chats gets
`kind=incidental` on its **own** subject. Subagents must not call
`canon` (single-writer store).

## Lifecycle

Decision two-modes is the rule. Structured work is a phase with a
specification. It runs specify, design, plan, execute, integrate when a
wave is parallel, verify, assess, and release `ready`. Simple work is
incidental, or a phase with no specification. It runs execute, then
verify as pass or fail. `settle-phase` writes a specification and a
design only for structured work; simple work skips both. A phase with
no specification, and incidental work, skip assessment and release and
keep pass/fail check-runs. `kind` `incidental` stays on that path even
when a specification exists for some other phase.

Verify and assess are two steps. Verify asks what happened. A check-run
records what happened and which requirement it bears on. It has no
`level` and no `next`. When the acceptance has `requirement`, the
check-run includes that requirement; simple work omits it. Assess asks
what that evidence means and which stage is next. An assessment records
what that evidence means and which stage is next. A failing test does
not itself choose the stage. A failing concurrency test does not itself
claim the design is wrong. Do not send every failure to execute.

The routes are implementation to execute, design to design, plan to
plan, specification to specify, integration to integrate or execute,
and insufficient evidence to verify.

| Evidence | Next |
|---|---|
| implementation: the cause is the task's code | `execute` |
| design: the design cannot satisfy the requirement | `design` |
| plan: no task covers the requirement | `plan` |
| specification: the requirement is ambiguous or contradicted | `specify` |
| integration: an integration-report `fail`, and a task must change | `execute` |
| integration: an integration-report `fail`, otherwise | `integrate` |
| insufficient evidence: the criterion was not exercised | `verify` |

Decision evidence-escalation. The same level repeats only when evidence
increased or the cause was resolved. Evidence increased means a new
`evidence_kind`, a narrower failing case, or a cause that was unnamed
and is now named. Otherwise the ladder is implementation, then design,
then specification. Do not use a failure count. `plan` and `integration`
are direct diagnoses. They are chosen only when the evidence says so.
They are not inserted under a repeated implementation failure.

Decision release-ready. Release state `ready` means every requirement
is verified. `ready` means the evidence is sufficient. It does not mean
merged or deployed. Do not write `merged`, `deployed`, or any other
state. Do not deploy.

A `composer:idea` parks deferred work on an effort until it is
promoted or dismissed. `engage` lists open ideas with an effort after
naming focus. Park = create; promote = supersede to `promoted` then
`settle-phase` with a new phase (or an incidental work-item when that
kind fits); dismiss = supersede to `dismissed`.

```bash
canon create --type composer:idea \
  --subject "<item-slug>" \
  --payload '{"effort":"<effort-slug>","status":"open","source":"<optional>"}' \
  --body "<parked description>"

canon list --type composer:idea \
  --where payload.effort=<focus> --where payload.status=open --state active

canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"promoted","phase":"<phase-slug-or-empty>","effort":"<effort-slug>"}'

canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"dismissed","effort":"<effort-slug>"}'
```

A git merge is not integration success. A clean git merge does not by
itself write `pass`. Write `pass` only after interfaces, shared
assumptions, cross-task invariants, and integration behavior hold.
Skip the integration report when incidental, or when no implementation
wave has more than one task. That multi-task wave is the parallel case
the structured path integrates.

## Skills in this pack

- `engage`
- `triage-ideas`
- `init`
- `settle-phase`
- `plan-phase`
- `execute-phase`
- `verify-work`
- `analyze-sessions`

Shared rules: [skills/kinds-and-focus.md](skills/kinds-and-focus.md).
Shared first-run steps: [skills/ensure-store.md](skills/ensure-store.md).
The installer ships a byte-identical copy of each shared file inside every
skill's `references/` directory, so an installed skill is self-contained.

## CLI

The `orchestra` console script (and `bin/orchestra` in a checkout) dispatches
subcommands and shells to `canon` for store reads/writes:

| Command | Effect |
|---|---|
| `check` | Run an acceptance's `verify_command` and write an `tuner:check-run`. |
| `close-batch` | Build the NDJSON apply batch that closes a work-item. |
| `install` | Install the payload for one or more agent hosts. |
| `handoff` | Print the handoff markdown. Writes no file. |
| `view` | Print the `plan`, `status`, or `verification` view. Writes no file. |
| `brief` | Print one work-item's brief. Writes no file. |
| `status` | Print one line per effort with running, ready, and needs-you counts; `--count` prints the needs-you count. Writes no file. |
| `hook-start` | SessionStart hook: inject the handoff. |
| `hook-stop` | Stop hook: validate, and block only on errors new to the session. |
| `sessions` | Summarize Claude Code session transcripts. |
| `analyze` | Check a phase's specification, work-items, and acceptances for consistency; exits 1 on errors. |
| `review-brief` | Build the phase-end reviewer brief from records and a diff. |
| `suite` | Read, run, collect, and record the configured phase suite. |
| `store` | Resolve the bound store and run `canon` through it. |

`orchestra verify` runs tuner, the evidence CLI. Flags live in each
subcommand's `--help`:

| Command | Role |
|---|---|
| `verdict` | Re-execute frozen oracle tests at two revisions |
| `runner-template` | Print a shipped runner template argv as JSON |
| `attest` | Emit or verify a signed verdict attestation |
| `lint` | Report no-assert witnesses, new skips, or claim wording |
| `claim` | Author manifest claims |
| `freeze` | Record oracle file hashes into the manifest |
| `audit` | Advisory: label diff blocks; optional mutants and probes |
| `trail` | List evidence-observations from the store |
| `bind` | Attach an observation to a claim under pinned revisions |
| `unbind` | Retire a binding |
| `recheck` | Re-judge a claim under its active binding pins |
| `assertion-red` | Classify check-run JSON as assertion-level red (exit 0/1) |

`verdict` does not read a workflow store for its gate answer.
`trail`, `bind`, `unbind` and `recheck` use the work repo's `.canon/`
store when present.

```bash
# From a clone or a console-script install, inside the project with the store:
orchestra check --acceptance <acceptance-id>
orchestra check --acceptance <id> --cwd /path/to/phase-worktree
orchestra check --acceptance <id> --allow-dirty   # pass on dirty tree
```

`check` runs the acceptance's `verify_command` (methods `tdd` / `check`
only), writes an `tuner:check-run` with revision and runner metadata,
and refuses `method=manual` (use human `signed_by` sign-off instead).

## Web dashboard

`dashboard/bin/web` runs the web dashboard through `uv` for the repo of the
current directory. It serves the snapshot of the store on a loopback port.
Pass `--port N` to pick the port.

The web launcher (and `orchestra store`) pick **one** store for the git
toplevel — local (`<toplevel>/.canon`) or global
(`~/.canon/<toplevel name>`), never both.

Resolution order:

1. `$SE_WORKFLOW_STORE` (`local` or `global`).
2. `<toplevel>/.canon/store-binding.local.json` (gitignored override).
3. `<toplevel>/.canon/store-binding.json` (committed default).
4. Default: local if it has `config.json`, else global if it has
   `config.json`, else none.

Binding files are JSON: `{"store":"local"}` or `{"store":"global"}`.
A set binding that points at a path without `config.json` fails; it does
not fall through to the other store. This repository pins local in
`.canon/store-binding.json`.

If a personal shell function wraps `canon` and forces
`--store ~/.canon/<name>`, it bypasses this binding for bare CLI
calls. Prefer `command canon`, or pass `--store` from the resolved
target.

Dismissing an unsigned manual check signs it with `$SE_WORKFLOW_SIGNED_BY`,
else `$USER` / `$USERNAME`, else `dashboard`.

The launcher finds `uv` in this order:

1. `$SE_WORKFLOW_UV`.
2. `uv` on `PATH`.
3. `~/.local/bin/uv`.

If the launcher finds no store or no `uv`, it prints the reason and exits.

## Testing

Run the full suite as four pytest processes:

```bash
uv run pytest -q -n auto --confcutdir=tests/canon tests/canon
uv run pytest -q -n auto --confcutdir=tests/tuner tests/tuner
uv run pytest -q -n auto tests --ignore=tests/canon --ignore=tests/tuner
uv run pytest -q tests --ignore=tests/canon --ignore=tests/tuner -m tmux
```

Each tree has its own `conftest.py`, so `tests/canon` and `tests/tuner`
run apart from the orchestra tests. The tmux tests run last and serially,
because parallel load makes them flaky. CI runs the same four commands as
parallel jobs and adds `--reruns 2` to the tmux pass. When the configured
suite `command` is empty, the suite falls back to
`uv run pytest tests -q -n 4 -m "not tmux"` then
`uv run pytest tests -q -m tmux`.

These four commands are the **phase-level suite** (`phase_gate.suite`).
Per-task `verify_command` values stay narrowly scoped (specific files
and `-k` filters). Do not put this whole-suite command on a work-item
acceptance. After closing verification and the phase-end reviewer
pass, `execute-phase` honors the configured suite policy — agents must
not waive it; a human changes `settings.conductor.phase_gate` in
`.canon/config.json` instead.

`phase_gate.suite` fields:

| Field | Values | Behavior |
|---|---|---|
| `mode` | `none`, `smoke`, `full`, `external` | `none` skips; `smoke`/`full` run the configured `command` in a detached tmux window in the phase worktree; `external` does not run locally |
| `gate` | `required`, `advisory`, `deferred` | `required` blocks Landing merge on missing/failing suite@head; `advisory` records the check-run (and a finding on fail) without blocking; `deferred` is a Landing human stop with no local run |

`phase_gate` lives in `.canon/config.json` under
`settings.conductor.phase_gate`. A new store defaults to `mode=none` (skip).
When a suite is configured (`mode` not `none` and `command` set) and
`gate` is omitted, gate defaults to `required`. This repo's live
`.canon/config.json` sets `mode=full` and `gate=advisory` with
the four commands chained with `&&`. The suite check-run
uses `subject` `<phase>-suite` (`evidence_kind: integration`) at the
phase head SHA.

The test conftest sets `CANON_SCHEMA_PATH` to the three in-repo module
files, so test stores load `score`, `conductor` and `tuner` without an
install.

Every test drives `canon`'s public CLI against a fresh, disposable,
git-backed store created with `canon init --schemas score,conductor,tuner` —
nothing here touches a real store. The schema modules under
`orchestra/score/schemas/`, `orchestra/conductor/schemas/` and
`orchestra/tuner/schemas/` are the type reference. `test_skill_contract_consistency.py`
extracts every `canon` invocation documented under `skills/` and asserts
the schema modules actually permit it — a red result there names a skill
instructing an operation (a record type, field, or transition) the
schemas do not allow.

### Type check

Run `uv run basedpyright` to type-check `orchestra`, `dashboard` and
`installer`. CI runs the same command in the `types` job.
