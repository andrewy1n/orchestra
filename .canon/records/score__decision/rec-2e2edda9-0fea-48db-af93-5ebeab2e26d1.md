---
{
  "id": "rec-2e2edda9-0fea-48db-af93-5ebeab2e26d1",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "Promote the vanilla JS spike, Retire Textual and make the browser the only dashboard",
    "choice": "Frontend toolchain beside Textual, sharing dashboard.model",
    "effort": "dashboard",
    "phase": "web-dashboard"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-19T05:51:50+00:00",
  "relationships": {},
  "revision": "sha256:9c64d9f1465d26f055151df1d5ca5dc246f6c0d0a37543e3eab224ce4a01937b",
  "subject": "web-dashboard-shape",
  "time": {
    "as_of": "2026-10-19T05:51:50+00:00"
  }
}
---

## Rationale

The browser dashboard sits beside the Textual app. It reads the same `dashboard.model` snapshot the terminal uses, and the terminal keeps tmux, keyboard control, and store writes. The spike already proved that split, but its UI is hand-built DOM strings in two diverging files. A frontend toolchain is how that UI stays one codebase as screens grow. The installed `orchestra` package stays free of this UI; the dashboard remains a tool in this repo.

## Counter-argument

The live spike already serves the store with the Python standard library and a single JavaScript file that polls a change token. Promoting those files avoids Node, a build, and a second dev server in a repo whose dashboard script depends only on Textual. The page is a localhost viewer, and the plain script is enough until the screen set outgrows it.
