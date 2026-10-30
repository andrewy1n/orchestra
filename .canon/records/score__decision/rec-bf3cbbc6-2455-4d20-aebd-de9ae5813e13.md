---
{
  "id": "rec-bf3cbbc6-2455-4d20-aebd-de9ae5813e13",
  "lifecycle_state": "active",
  "payload": {
    "alternatives": "ops in a hidden git ref, Dolt, untrack only derived files",
    "choice": "SQLite in WAL mode as the store engine",
    "effort": "canon-db-store",
    "phase": "db-backend"
  },
  "record_type": "score:decision",
  "recorded_at": "2026-10-30T08:12:59+00:00",
  "relationships": {},
  "revision": "sha256:3b5c61e08ba0eb43d42891ae31514d4feb02b942ec3ad7bd221f492ccc8a5b1d",
  "subject": "canon-store-engine"
}
---

## Rationale

SQLite in WAL mode gives atomic multi-record writes, fast queries and one writer at a time with short transactions. That fits parallel agents on one machine. It adds no server and no service dependency.

## Counter-argument

Ops in a hidden git ref keep git as transport, give sync and CI access without a new dependency, and remove the diff noise too. Dolt gives cell-level merge for multiple store copies. Both avoid a new storage format, but both cost more code or a heavier dependency than one store on one machine needs.
