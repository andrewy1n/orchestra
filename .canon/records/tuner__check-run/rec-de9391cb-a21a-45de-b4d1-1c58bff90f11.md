---
{
  "id": "rec-de9391cb-a21a-45de-b4d1-1c58bff90f11",
  "lifecycle_state": "recorded",
  "payload": {
    "criterion_id": "rec-d0a726bc-62cc-4cb2-a95c-f4dd36e50532",
    "duration_s": 15.64593,
    "effort": "evidence-layer",
    "exit_code": 0,
    "informed_by": [
      "rec-d0a726bc-62cc-4cb2-a95c-f4dd36e50532"
    ],
    "method": "check",
    "output_sha256": "6e1d9c47dba5a56234a25d81f3a8c3dffd1647e30376ef7dfaebbf92ce24145b",
    "requirement": "R3",
    "result": "pass",
    "revision": "2f2054aeccef9db20ac96d84d3c7f09d2647adfd",
    "runner": "aff",
    "signed_by": ""
  },
  "provenance": {
    "sources": [
      "move-store-client"
    ]
  },
  "record_type": "tuner:check-run",
  "recorded_at": "2026-10-17T23:14:16+00:00",
  "relationships": {},
  "revision": "sha256:6d9a7aa59c70297ba681af05bfce3c20ba232709e55184d65326ada9e3b50e34",
  "subject": "move-store-client",
  "time": {
    "observed": "2026-10-17T23:14:16+00:00",
    "recorded": "2026-10-17T23:14:16+00:00"
  }
}
---

usage: orchestra check [-h] --acceptance ACCEPTANCE [--cwd CWD]
                       [--allow-dirty] [--execution-report EXECUTION_REPORT]
                       [--timeout TIMEOUT]

options:
  -h, --help            show this help message and exit
  --acceptance ACCEPTANCE
                        Acceptance record id
  --cwd CWD             Directory for git revision and verify_command
                        (default: process cwd)
  --allow-dirty         Allow recording a pass on a dirty tree (revision=dirty
                        + diff_sha256)
  --execution-report EXECUTION_REPORT
                        Optional execution-report id to link via informed_by
  --timeout TIMEOUT     verify_command timeout in seconds (default: 600)
usage: orchestra close-batch [-h] [--input INPUT] [--out OUT] [--cwd CWD]

options:
  -h, --help     show this help message and exit
  --input INPUT  close-request JSON path, or '-' for stdin (default)
  --out OUT      NDJSON output path, or '-' for stdout (default)
  --cwd CWD      git cwd for red-first ancestry checks (default: process cwd)
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 14.95s
