---
{
  "id": "rec-9ef3e36f-3de3-40cd-b31e-81742dee49ef",
  "lifecycle_state": "active",
  "payload": {
    "effort": "package-layout",
    "method": "tdd",
    "oracle_hashes": [
      "tests/test_wheel_contents.py:sha256:27870adc050644f052b4d272c41b4693ee9e2b52966bbdb94cd4ff7f16d260fd"
    ],
    "phase": "wheel-contents",
    "requirement": "R8",
    "test_ids": [
      "tests/test_wheel_contents.py::test_r8_uvicorn"
    ],
    "verify_command": "uv run python -m pytest tests/test_wheel_contents.py::test_r8_uvicorn -q"
  },
  "record_type": "score:acceptance",
  "recorded_at": "2026-10-28T07:45:00+00:00",
  "relationships": {},
  "revision": "sha256:3409bddb3f827d88085819b7a17d9592910f4f29e59fdd5b11cfa7bcd02edceb",
  "subject": "declare-wheel-uvicorn"
}
---

