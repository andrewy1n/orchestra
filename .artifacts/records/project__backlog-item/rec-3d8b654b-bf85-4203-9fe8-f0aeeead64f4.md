---
{
  "base_kind": "claim",
  "epistemic_status": "asserted",
  "id": "rec-3d8b654b-bf85-4203-9fe8-f0aeeead64f4",
  "identity": "unknown",
  "lifecycle_state": "active",
  "payload": {
    "effort": "dashboard",
    "source": "session",
    "status": "open"
  },
  "record_type": "project:backlog-item",
  "recorded_at": "2026-10-15T04:02:46+00:00",
  "relationships": {},
  "revision": "sha256:7167452bbcbd991396a5b71b9ac255c82248e648e86c3a5d682d640ebcd53869",
  "stewardship": {
    "steward": "agent"
  },
  "subject": "journal-detail-xdist-flake",
  "time": {
    "as_of": "2026-10-15T04:02:46+00:00"
  }
}
---

# Journal RecordDetailScreen flake under tier-2 xdist

## Symptom

`tests/test_dashboard_journal.py::test_journal_detail_pager_pages_record_with_stub` fails under the full parallel suite (tier-2 / xdist): after Enter on a journal row, `RecordDetailScreen.loaded` never becomes true within 20–40s. Solo run of the same test usually passes in a few seconds.

## What happens

1. JournalScreen opens and loads items.
2. Test selects a row and presses Enter → `on_data_table_row_selected` pushes `RecordDetailScreen`.
3. Detail screen starts `@work(thread=True)` `load()` → `load_record` → async `apply()`.
4. Under suite load the wait on `isinstance(app.screen, RecordDetailScreen) and app.screen.loaded` times out — either the screen never mounts, the worker never finishes, or `apply` never sets `loaded`.

Raising the pilot `_until` timeout to 40s did not fix it (still full timeout). Unrelated to packaging plugin-root / close-batch work; waived for plugin-root-and-cli Landing.

## Likely directions

- Harden journal pilots: wait for workers after Enter; retry Enter; or open detail via a deterministic helper.
- Fix RecordDetailScreen load/`apply` races under CPU contention (exclusive work groups, call_from_thread + async apply).
- Or isolate this pilot from xdist (serial mark) if the flake is load-only.

## Evidence

- Finding: tier2-journal-pager-flake
- Tier-2 fails at 269ab7b, 8109e9a, 3379fcf — same node id only after import fix
