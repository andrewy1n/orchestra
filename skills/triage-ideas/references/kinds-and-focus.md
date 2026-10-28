# Kinds and focus

Shared rules for every orchestra skill. Do not invent extra skills for
bugs, one-offs, or evals.

## Kinds

`kind` is `deliver` | `repair` | `evaluate` | `incidental`. Put it on
`score:effort` and each `work-item`. Missing `kind` means
`deliver`.

| Kind | Unknown | Done | Records |
|---|---|---|---|
| `deliver` | how | change + binary check | work-item + acceptance + check-run |
| `repair` | what is wrong | cause + repro gone | those, plus observation / finding |
| `evaluate` | whether it holds / which is better | campaign result | check-run if binary; finding if comparative or inconclusive |
| `incidental` | usually nothing | change landed | none, or one work-item (see below) |

`acceptance.method` stays `tdd` | `check` | `manual`; `verify_command`
holds the literal command that backs it (empty string for a `manual`
check with no script). Do not stuff a metric delta into
`check-run.result`. Use `tuner:finding` (`claim`, `basis`,
`invalidated_when`, `needs`).

`executor` on a work-item is `inline` or `subagent`. Every task in a
wave uses the same executor. Missing `executor` means `subagent`.

The phase body includes a `## Landing` section with branch
`phase/<phase-slug>`, worktree
`<repo>/.worktrees/<phase-slug>`, base `main`, and these
close actions: commit code on the phase branch, merge that branch
into `main`, then commit the store on the primary checkout. Push
appears only when it is one of the human stops. Incidental work has
no Landing section. A phase body that omits Landing is not ready
for plan review.

## Focus

A **live** goal is a `score:effort` in lifecycle `active` whose
`payload.status` is not `closed` (missing means open).

### Closing and reopening

`status` (`open` | `closed`) on `score:effort` and `score:position`
says whether an effort is live. It is a payload field, not the
lifecycle. Closing and reopening both `supersede` the effort's goal and
position with the new `status`; `supersede` merges the payload, so the
other fields carry over.

- **Close** only when the user says no more phases follow.
  `execute-phase` asks when an effort's last phase is done. An effort
  whose phases and tasks are all done is "finished" on the dashboard,
  but it stays open until the user closes it.
- **Reopen** when work returns to a closed effort: supersede its goal
  and position with `status: open`, then add the phase. Never create a
  second goal with a closed effort's subject.

Closed goals do not show in views. Find them with:

```bash
canon list --type score:effort --state active --where payload.status=closed

canon supersede --type score:effort --id <goal-id> \
  --expected-revision <revision> --payload '{"status":"open"}'

canon supersede --type score:position --id <position-id> \
  --expected-revision <revision> --payload '{"status":"open"}'
```

Focus is a **subject string**, not a record. Name it (from `engage`, the
user, or the only live `score:effort` subject). Then:

- Read `orchestra handoff --effort <focus>` and the focus's phases in
  `orchestra view plan --effort <focus>`.
- Ignore other live goals. Do not supersede `score:effort` or
  `score:position` that belongs to another effort.
- Task-scoped records (`work-item`, `acceptance`, `check-run`,
  `decision`, `failed-attempt`, `investigation-observation`, `finding`,
  `assignment`, `assignment-amendment`, `execution-report`) use
  `subject` = task slug and `payload.effort` = focus.
- Goal, the effort position, and continuity-question use `subject` =
  focus. A running phase also has its own position: `subject` = phase
  slug, `scope` = `phase`, `payload.effort` = focus. Each chat writes
  only its own phase's position; the effort position changes when a
  phase closes.

An effort is a product area or objective, not one ask. New work in
an area a live goal already covers is a new phase of that effort. A
new effort is a new subject only when no live goal covers the area.
Create its goal/position. Leave the others active.

Hierarchy inside an effort:

- **milestone** (`score:milestone`) — optional time-bounded outcome
  that groups phases (e.g. cutover, harden). Payload: `title`,
  `ordinal`, `effort`. Not a focus subject; focus stays the effort.
- **phase** (`score:phase`) — one settle → plan → execute → verify
  loop. Optional payload `milestone` references a milestone subject.
  Phase `ordinal` is effort-scoped (not reset per milestone).

Skills stay phase-scoped. A milestone is a grouping and done-gate for
its phases, not a second chat focus.

## Incidental

- Fits this chat and is not an interrupt of another live effort: **no
  records**. Do the work in this session.
- May span chats, or it interrupts a live phase: one `work-item` +
  `acceptance`, `kind=incidental`, `phase=""` (no phase record exists
  for incidental work; canon checks a non-empty `phase` against
  real `score:phase` subjects and skips an empty string), `effort` = a **new** subject (not the interrupted effort).
  Work-item `subject` may equal that effort slug when there is only one
  task. Do not supersede the main goal.

## Needs-you clears

Human-dismissible Needs-you kinds are `blocking-question`,
`open-question`, `needs-human`, and `unsigned-check` only (not
loop-route, integration, or merge-branch). When the user settles one
in an agent session, the parent session clears that source at the
event — the same CLI outcomes the dashboard dismiss uses. Do not keep
a separate dismiss cache.

| Kind | Source | Clear at the event |
|---|---|---|
| `blocking-question` / `open-question` | `score:continuity-question` still open | `update --transition answered` |
| `needs-human` | active `tuner:finding` with `needs` `human` | `update` with `needs` `none` |
| `unsigned-check` | latest `method=manual` `tuner:check-run` with empty `signed_by` | `correct` setting `signed_by` |

```bash
canon update --type score:continuity-question --id <question-id> \
  --transition answered --expected-revision <revision>

canon update --type tuner:finding --id <finding-id> \
  --expected-revision <revision> \
  --payload '{"needs":"none"}'

canon correct --type tuner:check-run --id <check-run-id> \
  --payload '{"signed_by":"<signer>"}'
```

Findings advertise a supersedes relationship but have no superseded
lifecycle state, so clear with `update` (same as dashboard dismiss).
Signer identity comes from config, env, or a short prompt.

## Writing rules

- **Capture at the event.** Write the record when the decision,
  observation, or commitment happens. Do not batch writes for session
  end or write them from memory.
- **One writer per store.** Only the parent session calls `canon` in
  any form that writes. Subagents return evidence in their response
  text and never call `canon` or edit `.canon/`. This holds for
  every executor mode, including a read-only one: that mode names what
  an executor may read, it does not make the store multi-writer.
- **Views are derived.** Records are the authority. Render views with
  `orchestra handoff`, `orchestra view plan|status|verification`, and
  `orchestra brief <work-item>`. They print to stdout and write no
  files. A view may lag a record; read the record before you act on a
  claim.
- **Validate before finishing.** Run `canon validate` and fix every
  error. The Stop hook runs the same check and blocks on new errors.
- **Follow the lifecycle.** `supersede` a `current` record (new id);
  never `update` it to `superseded`. Event records stay `recorded`;
  `correct` writes a successor. A stale `--expected-revision` is a
  rejected write: re-read, then retry. Never hand-edit a record file.
- **Read by relevance.** Route by focus, then phase. Never bulk-read
  the store.
