---
{
  "base_kind": "observation",
  "id": "rec-9cfd1ed4-c8aa-4f71-b72b-392d87e8a9f3",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "workflow-loop",
    "phase": "dashboard-approvals",
    "result": "fail",
    "revision": "a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d"
  },
  "provenance": {
    "sources": [
      "dashboard-approvals"
    ]
  },
  "record_type": "project:integration-report",
  "recorded_at": "2026-10-14T07:57:26+00:00",
  "relationships": {},
  "revision": "sha256:4b811f51ce9925a833829276a8f19c5dfd22d99463defb090d245996d8f508bc",
  "subject": "dashboard-approvals",
  "time": {
    "observed": "2026-10-14T07:57:26+00:00",
    "recorded": "2026-10-14T07:57:26+00:00"
  }
}
---

## Interfaces

Contract optional fields `answer` / `signed_note` / `resolution_note` in `contract/project-design.json`; `NeedsYouItem.revision` from model; `dashboard/dismiss.py` approve/reject/sign/accept argv (displayed `--expected-revision`, never `@current`; reject=`create` finding); `dashboard/approval.py` evidence + confirm helpers; `dashboard/app.py` list-`d`→detail, detail `a`/`x`/`s`/`d`→`NeedsConfirmModal`→dismiss; README key table; approval pilots in `tests/test_dashboard_app.py` / model / contract self-consistency

## Assumptions

Brief work-item/spec/design/diff only (ignored execution-report/check-run/assessment/assignment text); constraint records read from primary store (store commits not on phase branch); CLI `update`/`correct` merge payload patches; `correct` has no `--expected-revision` (pre-`get` guard as designed)

## Invariants

No write without detail+confirm — held for Needs-you path; stale never silently `@current` — held for update/accept, sign/reject pre-get guard; Reject never answers continuity-question — held; exclusive human-gate write-set invariant — not held vs backlog writes (finding above)

## Conflicts

New exclusive human-gate constraint wording vs preserved backlog promote/dismiss writes; phase “don’t change backlog” vs “writes only for this human-gate set”
