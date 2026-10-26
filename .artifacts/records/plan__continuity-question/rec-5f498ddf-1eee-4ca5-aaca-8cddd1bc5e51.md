---
{
  "id": "rec-5f498ddf-1eee-4ca5-aaca-8cddd1bc5e51",
  "lifecycle_state": "answered",
  "payload": {
    "answer": "okay",
    "blocking": true,
    "owner": "user",
    "scope": "retry:web-write-api"
  },
  "record_type": "plan:continuity-question",
  "recorded_at": "2026-10-19T07:40:41+00:00",
  "relationships": {},
  "revision": "sha256:23ce34fa545d0b5243c6af4237d8c131186433f97f42663c99e5b1c41afa6210",
  "subject": "dashboard"
}
---

## Question

Approve an oracle amendment for `tests/test_web_dashboard.py::test_r24_signer`?

After `dashboard.dismiss.dismiss_item(..., action=\"sign\")`, `adaptive-artifacts correct` writes `signed_by` on a **correction successor**. `get --id <original>` still shows `signed_by=\"\"` and `derived.corrected=true`. The frozen oracle asserts the predecessor's `signed_by == default_signer()`, so R24 cannot pass without changing the oracle (or redesigning sign away from `correct`).

The write API itself ignores a client `signer` and calls dismiss with `default_signer` — spy asserts for that already pass (8/9 write tests green).

Proposed change: assert `signed_by` on the correction tip (list by subject / follow `corrects`), not on the predecessor id.

## Why it matters

`web-write-api` stays blocked; later write UI tasks that depend on it cannot close.

## Options

1. Approve amending the frozen oracle as above (parent will land the amendment and re-dispatch).
2. Keep the oracle; redesign `dismiss` sign (out of this phase's write-API territory).
3. Withdraw R24 / the task.
