---
{
  "id": "rec-c977cced-bbda-45c6-9885-96be02f18b5a",
  "lifecycle_state": "done",
  "payload": {
    "assignee": "cursor",
    "decisions": [],
    "effort": "composer",
    "estimate_minutes": 4,
    "executor": "inline",
    "kind": "deliver",
    "phase": "idea-triage",
    "requirements": [
      "R1"
    ],
    "size": "XS",
    "title": "Unit test the idea slug logic"
  },
  "record_type": "score:work-item",
  "recorded_at": "2026-10-28T07:08:01+00:00",
  "relationships": {},
  "revision": "sha256:35fecb4f198fb11c84db024365e62178afa6d73412f776f5920cc46a122f29b3",
  "subject": "fix-idea-slug-tests"
}
---

## Description

R1: `orchestra idea "<title>"` creates an open `composer:idea` whose subject is the slugified title.

## Approach

Add tests/test_idea_slug.py covering lowercase and hyphen runs, the 60-character cap with trailing-hyphen trimming, non-ASCII handling by NFKD, and IdeaError for a title with no usable characters.
