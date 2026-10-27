---
{
  "id": "rec-d3f09ea9-dc6c-4e0d-aaf6-ee085494f97f",
  "lifecycle_state": "active",
  "payload": {
    "acceptance": "web-write-api-r24",
    "effort": "dashboard",
    "new_hashes": [
      "tests/test_web_dashboard.py:sha256:d03ce17adb1ecb7599812c6a71c4672d57d33352cac2ca1a11d37d0a576639a1"
    ],
    "old_hashes": [
      "tests/test_web_dashboard.py:sha256:d06a1bb5cd28b12fc30f00f4dfdd0132141c8b11cebde9607bfbb2ff37dee102"
    ],
    "phase": "web-dashboard",
    "status": "approved"
  },
  "record_type": "tuner:oracle-amendment",
  "recorded_at": "2026-10-19T08:07:40+00:00",
  "relationships": {
    "supersedes": [
      "rec-87169cf2-293c-40f4-b060-f4747aa43fab"
    ]
  },
  "revision": "sha256:826f4e5c19a0cd987ddf298d902e01f2a18b6d8993eeac39611a738c21a1fcd7",
  "subject": "web-write-api-r24",
  "time": {
    "as_of": "2026-10-19T08:07:40+00:00"
  }
}
---

## Reason

Human approved option 1: R24 must assert signed_by on the correction successor after adaptive-artifacts correct, not on the predecessor id. Same oracle file is shared by all web-write-api acceptances, so the freeze hash updates for each.

## Change

test_r24_signer lists the check-run tip that corrects the original id and asserts payload.signed_by == default_signer() on that tip.
