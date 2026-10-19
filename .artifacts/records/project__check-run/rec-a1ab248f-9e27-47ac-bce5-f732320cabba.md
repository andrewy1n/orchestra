---
{
  "base_kind": "event",
  "id": "rec-a1ab248f-9e27-47ac-bce5-f732320cabba",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "dashboard-approvals-review",
    "effort": "workflow-loop",
    "evidence_kind": "review",
    "method": "review",
    "result": "pass",
    "revision": "a27e7b9c4852347de20f4ce2ca3b6fae8ff58d3d",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "dashboard-approvals-review"
    ]
  },
  "record_type": "project:check-run",
  "recorded_at": "2026-10-14T08:01:24+00:00",
  "relationships": {},
  "revision": "sha256:118e79293f22b8a8a9ec4fcc925073af442312a36d13f64e9752fa7172f8d313",
  "subject": "dashboard-approvals-review",
  "time": {
    "observed": "2026-10-14T08:01:24+00:00",
    "recorded": "2026-10-14T08:01:24+00:00"
  }
}
---

verdict: PASS
findings: []
integration:
  interfaces: Contract optional fields `answer` / `signed_note` / `resolution_note`; `NeedsYouItem.revision`; `dismiss.py` approve/reject/sign/accept (displayed `--expected-revision`, never `@current`; reject=`create` finding; sign/reject pre-`get` guard); `approval.py` evidence + confirm helpers; `app.py` list-`d`→detail, detail `a`/`x`/`s`/`d`→`NeedsConfirmModal`; README keys; approval pilots; active `dashboard-human-gate-writes` covers Needs-you + backlog promote/dismiss (`applies_to` includes `backlog.py`)
  assumptions: Brief + phase diff + active store constraint (prior exclusive-wording finding superseded); `correct` has no `--expected-revision` (pre-`get` as designed); backlog path unchanged (`@current`) and explicitly in-policy
  invariants: No Needs-you write without detail+confirm — held; stale never silently `@current` — held; Reject never answers continuity-question — held; allowed write set matches active constraint (Needs-you gates + backlog promote/dismiss) — held
  conflicts: none (prior exclusive human-gate vs backlog conflict resolved by superseding constraint statement)
