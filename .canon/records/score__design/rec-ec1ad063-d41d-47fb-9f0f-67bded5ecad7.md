---
{
  "id": "rec-ec1ad063-d41d-47fb-9f0f-67bded5ecad7",
  "lifecycle_state": "active",
  "payload": {
    "decisions": [
      "brief-storage",
      "brief-enforcement"
    ],
    "effort": "workflow-loop",
    "phase": "effort-brief"
  },
  "record_type": "score:design",
  "recorded_at": "2026-10-29T16:57:46+00:00",
  "relationships": {},
  "revision": "sha256:f35ca6934ebeedd3d79411a81352dada8316c1b5d07e0856dd4423af92c77e21",
  "subject": "effort-brief"
}
---

## Architecture

Add a `brief` type to `orchestra/score/schemas/score.json` and bump the module to `1.1.0`. The type has lifecycle `current`, one field `effort` (`{"ref": "score:effort"}`), and the sections `Problem`, `Users`, `Success measure`, `Non-goals`. Two skills change: init creates the brief for a new `deliver` effort, and settle-phase reads it in its context step. `orchestra/score/AGENTS.md` lists the type. At Landing the parent runs `canon schemas sync` on the live store so its snapshot and pin move to `1.1.0`.

## Interfaces

- Type: `score:brief`, subject = effort slug, payload `{"effort": "<effort-slug>"}`, body with `## Problem`, `## Users`, `## Success measure`, `## Non-goals`.
- Create (init, step 6, after the effort): `canon create --type score:brief --subject "<effort-slug>" --payload '{"effort":"<effort-slug>"}' --body-file "<brief-body.md>"`.
- Read (settle-phase, step 2): `canon list --type score:brief --subject <focus> --exact-subject --state active --full`.
- Sync: `canon schemas sync` after the module file changes.

## Decisions

- `brief-storage`: a new `score:brief` type, one record per effort.
- `brief-enforcement`: skills only; `orchestra analyze` does not check for a brief.

## Invariants

- No existing type, field, or section changes.
- Existing efforts stay valid.
- One active brief per effort subject.
- `orchestra/score/` imports only `canon`.

## Assumptions

- Sections are all-or-nothing per type.
- A minor bump needs no migration step.
- `init` is the only creator of efforts.

## Tradeoffs

- A separate record means two reads and two writes where one record would do.
- Old efforts have no brief, and nothing prompts the user to add one.
- The skill rule can be skipped, since no command checks it.

## Risks

- The live store keeps `score` at `1.0.0` until `canon schemas sync` runs, so `init` would fail on `score:brief` with an unknown type. The Landing step runs the sync and the proof packet names it.
- Other worktrees and checkouts that share the store need the new module before they use `init`.
- A test that enumerates score types or versions may need an update. The oracle author sees the requirement text only; the executor fixes any such test.
