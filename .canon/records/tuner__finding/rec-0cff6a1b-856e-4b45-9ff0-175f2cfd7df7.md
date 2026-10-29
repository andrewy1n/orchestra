---
{
  "id": "rec-0cff6a1b-856e-4b45-9ff0-175f2cfd7df7",
  "lifecycle_state": "asserted",
  "payload": {
    "basis": "check-run rec-479343cb-a231-486e-8e4b-5ec2b13e4803 failed because gh found no pull_request run at 30de2366246662831be14e046fdb4dff9c660816",
    "claim": "R22 needs a human: the wheel job cannot be observed until phase/wheel-smoke is pushed and a pull request exists",
    "effort": "ci",
    "invalidated_when": "a pull_request ci.yml run for that SHA shows the wheel job conclusion success",
    "needs": "human"
  },
  "record_type": "tuner:finding",
  "recorded_at": "2026-10-29T09:36:00+00:00",
  "relationships": {},
  "revision": "sha256:5b59a95f9ea1551c95d0f6d006e674b0d86870d56a14a00f1357c4435fa029f6",
  "subject": "wheel-smoke-R22"
}
---

## Evidence

Check-run rec-479343cb-a231-486e-8e4b-5ec2b13e4803 result=fail at 30de2366246662831be14e046fdb4dff9c660816. phase/wheel-smoke is not on origin. The local smoke, the missing-providers check, and the checkout-unchanged check passed.

## Consequence

verify-wheel-smoke stays in progress. The phase does not close and does not merge to main.

## Follow-up

Push phase/wheel-smoke and open the pull request. Then re-run the R22 check.
