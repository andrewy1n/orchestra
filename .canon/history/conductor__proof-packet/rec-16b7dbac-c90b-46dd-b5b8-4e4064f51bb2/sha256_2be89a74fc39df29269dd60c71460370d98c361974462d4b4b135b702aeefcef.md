---
{
  "id": "rec-16b7dbac-c90b-46dd-b5b8-4e4064f51bb2",
  "lifecycle_state": "recorded",
  "payload": {
    "base": "74926baccf843423dd6b942cc6d4f8e8129efc63",
    "effort": "dashboard",
    "kind": "commands",
    "phase": "areas-and-ideas",
    "revision": "c63972ccaeb7aa183f573289196241789851ec9b"
  },
  "record_type": "conductor:proof-packet",
  "recorded_at": "2026-10-29T22:40:46+00:00",
  "relationships": {},
  "revision": "sha256:2be89a74fc39df29269dd60c71460370d98c361974462d4b4b135b702aeefcef",
  "subject": "areas-and-ideas"
}
---

## Look

kind: commands. Run `dashboard/bin/web` against this repo's store, open the Home screen, find the Areas section (dashboard, architecture, agent-slop-standards) and open one area screen. Run `curl localhost:<port>/api/areas`.

## Machine

- Acceptances: every active areas-and-ideas acceptance passes at c63972ccaeb7aa183f573289196241789851ec9b (orchestra check).
- Review: PASS at c63972ccaeb7aa183f573289196241789851ec9b (subject areas-and-ideas-review). Integration-report: pass.
- Suite: 268, 134, 1254 tests pass per leg at c63972ccaeb7aa183f573289196241789851ec9b; the last leg (pytest -m tmux) exits 5. Advisory gate.

## Attention

- A human must look at the Areas section on Home and one area screen in the running UI (jsdom tests cannot check layout).
- Home renders only when an effort exists, so the Areas section stays hidden in a store with areas but no efforts; areas stay reachable by the #/area/<subject> deep link.
- An effort-only idea links to #/ and selects the effort in a click handler because the router has no single-effort route.
- A human must drop the tmux pass from the suite command in .canon/config.json (finding suite-command-tmux-pass).
- The shared-helpers phase edits dashboard files on unmerged branches; its merge needs hand resolution across the moves.

## Diff

 tests/dashboard/fixtures/areas-minimal.json        |   4 +
 tests/dashboard/fixtures/areas-rich.json           |  61 ++++++
 tests/dashboard/test_endpoint_shapes.py            |  47 ++++-
 23 files changed, 899 insertions(+), 8 deletions(-)
