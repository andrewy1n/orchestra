---
name: triage-ideas
description: >-
  Lists open composer ideas that have no product area, presents each with
  assign-area, create-area, dismiss, or leave options, and records the
  user's choice. Use when the backlog needs area placement before engage
  promotes an idea into work.
---

# Triage ideas

Requires `canon` and `orchestra` on PATH and a live orchestra store. If
missing, follow [ensure-store.md](references/ensure-store.md). Follow
[kinds-and-focus.md](references/kinds-and-focus.md). Parent session writes
records. Subagents return text only.

Promotion into an effort is `engage`. This skill never sets status
`promoted`.

## Steps

1. Run `orchestra handoff` if the handoff was not injected.
2. List open ideas and keep those with no `area` in the payload:

```bash
canon list --type composer:idea --where payload.status=open --state active --full
```

   When none remain, say so and stop.
3. List active areas:

```bash
canon list --type composer:area --state active --full
```

4. For each untriaged idea, show its subject, body, and source if any.
   Present four options: assign an existing area, create a new area,
   dismiss, or leave for later. Mark one option as recommended and say
   why. The user decides. Use a question tool with one option per choice
   when one is available.
5. When the user assigns an area, supersede the idea with that area slug:

```bash
canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"area":"<area-slug>"}'
```

6. When no area fits, create one, then assign it. The body must include
   `## Scope`:

```bash
canon create --type composer:area \
  --subject "<area-slug>" \
  --payload '{"title":"<area-title>"}' \
  --body-file "<area-body.md>"

canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"area":"<area-slug>"}'
```

7. When the user dismisses, supersede to `dismissed`:

```bash
canon supersede --type composer:idea --id <id> \
  --expected-revision <revision> \
  --payload '{"status":"dismissed"}'
```

8. When the user leaves an idea, make no write for it. Continue with the
   next untriaged idea.
9. Run `canon validate`. Remind the user that starting work on a triaged
   idea is `engage` (promote there, not here).

## Do not

- Set status `promoted` or supersede to `promoted`
- Start `settle-phase`, `plan-phase`, or `execute-phase` from this skill
- Let subagents write records
- Assign an area the user did not choose
