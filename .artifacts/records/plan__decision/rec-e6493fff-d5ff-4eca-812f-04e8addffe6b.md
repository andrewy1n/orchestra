---
{
  "id": "rec-e6493fff-d5ff-4eca-812f-04e8addffe6b",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "pip install --user textual, pyproject.toml",
    "choice": "PEP 723 inline-dependency script run with uv run --script",
    "effort": "dashboard",
    "phase": "readable-layout"
  },
  "record_type": "plan:decision",
  "recorded_at": "2026-10-02T03:16:31+00:00",
  "relationships": {},
  "revision": "sha256:f6556a483084297c949e1427a864147ff796643d5147fabdf63d7db4ae1cc667",
  "subject": "dashboard-deps",
  "time": {
    "as_of": "2026-09-30T18:49:40+00:00"
  }
}
---

## Rationale

`uv` is already installed. An inline-dependency script pulls in Textual on first run with no global install and no project packaging.

## Counter-argument

The launcher then requires `uv`. The other scripts run on plain `python3`.
