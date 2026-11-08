---
name: run
description: >-
  Preview and compose a built-in phase workflow or one selected step. Use when
  the user asks to run a phase, prepare, deliver, or a direct step.
---

# Run a workflow

Requires `orchestra` on PATH and a live store. The playbook composes the
separate `spec`, `design`, `tasks`, `execute`, and `verify` skills.
Use [retry-loop.md](references/retry-loop.md) and
[execute-mechanics.md](references/execute-mechanics.md) during execution.
Use [phase-end.md](references/phase-end.md) during verification, land, and close.
When `[land] adapter` is `github-pr`, also use
[land-github-pr.md](references/land-github-pr.md) for the CI repair loop and close.

## Built-in operations

- `phase`: spec, design, tasks, execute, verify
- `prepare`: spec, then design for all selected phases
- `deliver`: tasks, execute, verify
- `spec`, `design`, `tasks`, `execute`, or `verify`: one step only

Do not accept custom playbook names. A run does not grant merge approval.

## Steps

1. Resolve the effort, phase selection, and requested operation. Do not infer
   dependencies from phase ordinals. Keep external prerequisites outside the
   selected scope.
2. Preview before writing run intent:

```bash
orchestra workflow preview <effort> <selection> <operation> --json
```

3. Show the resolved phases, requested steps, prerequisites, external
   dependencies, and snapshot to the user. Refuse invalid or ambiguous scope.
   Start only from this preview's snapshot token:

```bash
orchestra workflow start <effort> <selection> <operation> \
  --snapshot-token <snapshot-token> --json
```

4. Resume stored progress with `orchestra workflow status <run>` and inspect
   safe actions with `orchestra workflow next <run>`. Recheck prerequisites
   before each action. Never run shell text from an action response.
5. Invoke the skill for each returned step. Respect its approval, autonomy,
   scope, and verification gates. Prepare completes every selected spec
   before it starts any selected design. Deliver follows dependency order.
6. A direct step request stops after that step. Continue into another step
   only when the user authorizes a longer sequence or selected playbook.
7. Continue independent selected phases when another phase blocks. Hold
   dependent phases. Report incomplete status while any required selected
   step remains unfinished.

## Do not

- Start without showing the previewed scope and steps
- Expand the selection to satisfy a missing external prerequisite
- Turn invocation into approval, delegation, or merge permission
- Treat a required read or check failure as empty success
- Report complete while a required selected step remains unfinished
