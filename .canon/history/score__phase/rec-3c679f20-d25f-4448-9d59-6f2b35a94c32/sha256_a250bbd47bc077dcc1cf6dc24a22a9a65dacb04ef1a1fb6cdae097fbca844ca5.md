---
{
  "id": "rec-3c679f20-d25f-4448-9d59-6f2b35a94c32",
  "lifecycle_state": "planned",
  "payload": {
    "effort": "dashboard",
    "ordinal": 31,
    "title": "Web dashboard"
  },
  "record_type": "score:phase",
  "recorded_at": "2026-10-19T05:58:25+00:00",
  "relationships": {},
  "revision": "sha256:a250bbd47bc077dcc1cf6dc24a22a9a65dacb04ef1a1fb6cdae097fbca844ca5",
  "subject": "web-dashboard"
}
---

## Problem

The store is visible as a product only through the Textual dashboard in tmux. The browser spike under `spikes/web-dashboard` already reads `dashboard.model`, but it is a stdlib server and hand-built DOM, and it cannot change the store.

## Approach

Ship a localhost web dashboard beside the Textual app. FastAPI serves the spike's JSON API and a Vite production build of a Svelte app styled with Tailwind. The page polls the change token. Needs you approve, reject, sign, and accept, and backlog dismiss and promote, call the same Python functions as the terminal. Decisions: `web-dashboard-shape`, `web-dashboard-toolchain`, `web-dashboard-writes`, `web-dashboard-server`, `web-dashboard-freshness`, `web-dashboard-styling`.

## Exit criteria

- `dashboard/bin/web` serves the built app on 127.0.0.1 for the store the Textual launcher would open (launcher test against this repo).
- TestClient tests pass for the snapshot, the token, each write, a stale Needs you revision, and a refused kind.
- `npm run build` in `dashboard/web/ui` succeeds, and GET / returns that build.

## Proof

kind: mixed

A human opens the page, picks an effort, opens a phase, and confirms a Needs you action. Commands cover the API, the write refusals, and the production build.
