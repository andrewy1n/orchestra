---
{
  "base_kind": "observation",
  "id": "rec-5b5b5aa3-42a4-4fc4-b8cd-c102bef4f137",
  "identity": "unknown",
  "lifecycle_state": "recorded",
  "payload": {
    "effort": "dashboard",
    "environment": "phase/web-write-body@29fec4bceaa72b8880b50dc8ceda560810cdfb09",
    "observed_time": "2026-10-20T08:42:00+00:00",
    "source": "uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py -q",
    "what_was_observed": "Before the edit, backlog and needs posts returned 422 for a missing request query parameter and openapi returned 500. After the edit the three tests passed."
  },
  "provenance": {
    "sources": [
      "uv run --with textual --with pytest --with fastapi --with httpx python -m pytest tests/test_web_fastapi_writes.py -q"
    ]
  },
  "record_type": "project:investigation-observation",
  "recorded_at": "2026-10-20T08:43:50+00:00",
  "relationships": {},
  "revision": "sha256:54446d8fda1545174ecec29743498b140ac96951be0d7a1fa555deaaa84e82fd",
  "subject": "web-write-annotations",
  "time": {
    "observed": "2026-10-20T08:42:00+00:00",
    "recorded": "2026-10-20T08:43:50+00:00"
  }
}
---

