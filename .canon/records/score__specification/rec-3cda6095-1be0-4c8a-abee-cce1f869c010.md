---
{
  "id": "rec-3cda6095-1be0-4c8a-abee-cce1f869c010",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "phase": "remove-textual",
    "requirements": [
      "R1",
      "R2",
      "R3",
      "R4",
      "R5",
      "R6",
      "R7",
      "R8",
      "R9",
      "R10",
      "R11",
      "R12",
      "R13"
    ],
    "weight": "full"
  },
  "record_type": "score:specification",
  "recorded_at": "2026-10-29T09:02:04+00:00",
  "relationships": {},
  "revision": "sha256:62fdab11af5c7c616be72ba77153d1601516776ce4e26324a29b4fea34138329",
  "subject": "remove-textual"
}
---

## Requirements

R1: No Python file under `dashboard/` or `orchestra/` imports `textual`.
R2: `pyproject.toml` does not list `textual` as a dependency.
R3: `pyproject.toml` lists `rich` only if a surviving module imports it.
R4: `orchestra.tmux`, `dashboard/bin/dashboard`, and `dashboard/bin/dashboard-status` do not exist.
R5: The CI file has no tmux job, and `pytest.ini` has no `tmux` marker.
R6: No Python module remains directly under `dashboard/` except `__init__.py`.
R7: The surviving Python modules live under `dashboard/backend/`, and the web server lives under `dashboard/backend/server/`.
R8: The server serves the built UI from `dashboard/web/ui/dist`.
R9: `orchestra status` prints one line per effort with its running, ready, and needs-you counts.
R10: `orchestra status --count` prints the needs-you count.
R11: The README has no tmux dashboard section.
R12: `uv run basedpyright` passes, and its baseline has no entry for a deleted file.
R13: The web API tests pass.

## Acceptance criteria

- R1, R2, R3, R4, R5, R6, R7, R11: a test checks the tree, `pyproject.toml`, the CI file, and the README.
- R8, R13: `tests/test_web_dashboard.py` and `tests/test_web_dashboard_launch.py::test_r30_serves_build` pass.
- R9, R10: an integration test runs `orchestra status` against a seeded store.
- R12: `uv run basedpyright` exits 0.

## Constraints

- The Python modules move with `git mv` and no content change, except imports and the deleted Textual code.
- `dashboard/web/ui` stays where it is until phase `ui-structure`.
- The Textual-free parts of `journal.py`, `gates.py`, and `landing.py` survive. The Textual screens in them go.

## Non-goals

- Splitting `model.py`. That is phase `data-layer`.
- Removing the stdlib server. That is phase `data-layer`.
- Any UI change.

## Invariants

- The web server starts and serves the snapshot after every task in this phase.
- No test writes to a real `.canon/` store.

## Assumptions

- The web server needs nothing from the deleted Textual modules except what the move extracts.
- `rich` may be used outside the deleted code. Plan-phase checks with a grep.
