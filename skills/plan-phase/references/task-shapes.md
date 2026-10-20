# Task shapes (work-item + acceptance)

Use from plan-phase steps 5–7. List the phase specification first:

```bash
adaptive-artifacts list --type project:specification --where payload.phase=<current-phase-slug> --state active
```

For every `deliver` / `repair` task, payloads include `requirements`
(atomic ids this task implements) and each acceptance's `requirement`
(exactly one of those ids). When a `project:specification` exists,
take id texts from it and set `decisions` to the decision subjects the
task follows. When none exists, write the id'd list in `## Description`
and still stamp `requirements` / `requirement`. Omit `criterion` (or
`""`) — thin acceptances. Several acceptances use
`<task-slug>-<short suffix>`. `incidental` may omit `requirements`,
`decisions`, and `requirement`.

## Independent task (bundle)

Bodies inline since `capture` takes JSON, not a file flag; use plain
`create --body-file` if Description needs more than a few lines.

```bash
adaptive-artifacts capture --bundle project:specified-work --records "$(cat <<'EOF'
[
  {
    "type": "project:work-item",
    "subject": "<task-slug>",
    "payload": {
      "title": "<short title>",
      "phase": "<current-phase-slug>",
      "kind": "deliver",
      "assignee": "",
      "effort": "<effort-slug>",
      "executor": "subagent",
      "size": "M",
      "estimate_minutes": 10,
      "requirements": "R1,R2",
      "decisions": "<decision-a>,<decision-b>"
    },
    "body": "## Description\n\nR1: <observable behavior>\nR2: <observable behavior>\n\n## Approach\n\n<implementation recipe>"
  },
  {
    "type": "project:acceptance",
    "subject": "<task-slug>",
    "payload": {
      "method": "tdd",
      "phase": "<current-phase-slug>",
      "effort": "<effort-slug>",
      "verify_command": "<command that proves R1>",
      "requirement": "R1"
    }
  },
  {
    "type": "project:acceptance",
    "subject": "<task-slug>-perf",
    "payload": {
      "method": "check",
      "phase": "<current-phase-slug>",
      "effort": "<effort-slug>",
      "verify_command": "<command that proves R2>",
      "requirement": "R2"
    }
  }
]
EOF
)"
```

Drop the second acceptance when there is only one requirement — the
bundle needs at least one `work-item` and one `acceptance`.

Set `kind` and `phase` from the effort (`phase` is `""` when
incidental). Set `executor` to `inline` or `subagent` (same within a
wave). Every new work-item includes `size` and `estimate_minutes`.
`method` is `tdd`, `check`, or `manual`; `verify_command` is the
literal command (empty string for `manual` with no script).

- `repair` — `verify_command` proves repro-gone plus a regression
  check, not "we investigated." Diagnose happens at execute/verify.
- `evaluate` — the campaign is the binary gate when there is one
  (`method=check`). Comparative / inconclusive lives in a finding at
  verify, not in `method`.
- `incidental` — one observable done-check; usually `check` or
  `manual`; exempt from atomic requirement ids.

## Dependent task (create + --rel)

Needs another same-phase task done first — create outside the bundle
so the dependency edge can be set at creation:

```bash
adaptive-artifacts create --type project:work-item \
  --subject "<task-slug>" \
  --payload '{"title":"<short title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":"R1,R2","decisions":"<decision-a>,<decision-b>"}' \
  --body "## Description

R1: <observable behavior>
R2: <observable behavior>

## Approach

<implementation recipe>" \
  --rel depends_on:<prerequisite-work-item-id>

adaptive-artifacts create --type project:acceptance \
  --subject "<task-slug>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R1"}'
```

## Verification task

For a `deliver` or `repair` phase, create last, with one
`--rel depends_on:` per other work-item. One thin acceptance per exit
criterion (suffixed subjects), each naming exactly one requirement id.
Acceptances come from phase exit criteria; at least one is an
integration check through the real entry point. A `verify_command`
that runs the whole `tests` tree, or `tests/test_dashboard_app.py`
without a `-k` filter for this phase, is not a verification
acceptance.

```bash
adaptive-artifacts create --type project:work-item \
  --subject "verify-<phase-slug>" \
  --payload '{"title":"Verify <phase title>","phase":"<current-phase-slug>","kind":"deliver","assignee":"","effort":"<effort-slug>","executor":"subagent","size":"M","estimate_minutes":10,"requirements":"R1,R2","decisions":"<decision-a>,<decision-b>"}' \
  --body "## Description

Prove the phase exit criteria hold together: run the integration
check through the real entry point, then every other phase check.

## Approach

<implementation recipe>" \
  --rel depends_on:<work-item-id-1> \
  --rel depends_on:<work-item-id-2>

adaptive-artifacts create --type project:acceptance \
  --subject "verify-<phase-slug>" \
  --payload '{"method":"tdd","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<integration test command>","requirement":"R1"}'

adaptive-artifacts create --type project:acceptance \
  --subject "verify-<phase-slug>-<criterion-suffix>" \
  --payload '{"method":"check","phase":"<current-phase-slug>","effort":"<effort-slug>","verify_command":"<command>","requirement":"R2"}'
```

A task that later joins the phase gets a `depends_on` edge on the
verification task (`update --rel`) so the gate still waits for it.
