---
{
  "id": "rec-34ac288b-d802-4b5c-b66a-8a086999faea",
  "lifecycle_state": "in_progress",
  "payload": {
    "assignee": "inline",
    "decisions": [
      "packaging-scope-aa-first",
      "pypi-publish-deferred"
    ],
    "effort": "packaging",
    "estimate_minutes": 5,
    "executor": "inline",
    "kind": "deliver",
    "phase": "pyproject-pypi",
    "requirements": [
      "R6",
      "R7"
    ],
    "size": "XS",
    "title": "Document AA git+ uv tool install"
  },
  "record_type": "plan:work-item",
  "recorded_at": "2026-10-15T20:58:52+00:00",
  "relationships": {},
  "revision": "sha256:3f6c56fbd217d491be6fefc6adda6c8dca2dd4eccadc4f0b474ea3754ac47648",
  "subject": "affidavit-readme-git-tool"
}
---

## Description

Update affidavit README Install to document `uv tool install` from the adaptive-artifacts git URL and state that PyPI publish is deferred. Do not add an affidavit pyproject.toml.

## Approach

1. Add a short Install subsection for the AA git+ tool path using the documented URL shape (`git+https://github.com/andrewy1n/adaptive-artifacts.git@<ref>`).
2. State explicitly that PyPI publish for adaptive-artifacts is deferred.
3. Leave plugin/checkout install paths in place; do not introduce affidavit packaging files.
