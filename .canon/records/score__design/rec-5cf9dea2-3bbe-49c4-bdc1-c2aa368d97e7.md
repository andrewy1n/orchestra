---
{
  "id": "rec-5cf9dea2-3bbe-49c4-bdc1-c2aa368d97e7",
  "lifecycle_state": "active",
  "payload": {
    "decisions": [
      "observation-ledger-home",
      "aff-observation-seam",
      "observation-record-optional"
    ],
    "effort": "evidence-layer",
    "phase": "evidence-interface"
  },
  "record_type": "score:design",
  "recorded_at": "2026-10-18T08:52:42+00:00",
  "relationships": {},
  "revision": "sha256:217650af4ae9cc26df58a0232a3dcd2cb92ddf761b6589990dda4c0f17b93d94",
  "subject": "evidence-interface",
  "time": {
    "as_of": "2026-10-18T08:52:42+00:00"
  }
}
---

## Architecture

Claims stay committed under `.affidavit/`. The evidence *trail* is store-backed: `project:evidence-observation` records in the subject repo's `.artifacts/` store.

`aff verdict` judges as today, prints JSON, then optionally records. `aff trail` reads via `adaptive-artifacts list`. No runtime import.

```
manifest.json (claims/witnesses)
        ^
        | freeze / amend
aff verdict --> judge --> stdout JSON
                 \
                  +--> adaptive-artifacts create (evidence-observation)
aff trail ------> adaptive-artifacts list/get
```

## Interfaces

- Contract: `project:evidence-observation` with payload fields at least: `technique`, `effort` (optional), `claim_ids` (comma-separated or equivalent), `base_rev`, `head_rev`, `result`, plus body or payload for outcomes/replay JSON.
- CLI: `aff trail [--cwd DIR] [--claim ID] [--technique NAME]` → JSON list.
- Recorder helper inside `affidavit/` that shells out to `adaptive-artifacts` with `--root` = subject repo when a store is detected.

## Decisions

- `observation-ledger-home`
- `aff-observation-seam`
- `observation-record-optional`

## Invariants

- Judge path does not require a store.
- Observation records are append-only occurrences (no hand-edited store files).

## Assumptions

- `adaptive-artifacts` is on PATH in environments that record.
- Tests may build a disposable store from this contract (existing suite pattern).

## Tradeoffs

- Store coupling vs queryable multi-agent trail: chose trail in store.
- Optional record vs always-on: chose optional for fixture compatibility.

## Risks

- Contract drift with `~/orchestra` if skills later depend on the type before a contract copy.
- Agents forget to init a store and see no trail — mitigate with clear stderr when recording is skipped.
