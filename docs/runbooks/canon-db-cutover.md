# Canon SQLite cutover evidence

The cutover retained the pre-switch export outside the repository at
`~/.canon/orchestra/backups/pre-cutover.jsonl` (27 MB). The baseline count
snapshot is `~/.canon/orchestra/backups/pre-cutover-counts.json`. Neither file
is tracked by Git.

## Source verification

The source snapshot was checked with:

```text
python scripts/verify_import.py /tmp/cutover-live-source-store
```

The passing check recorded at phase commit
`7e981910a99600112c4838708e919f131ae151b2` reported:

```text
8770 retained history revisions checked
9983 records, 0 mismatches
```

## Post-switch database

The pre-switch baseline contained 9,983 records across 28 record types. The
live SQLite store was checked with the per-type count comparison against
`pre-cutover-counts.json`: 10,197 current records across 28 types, baseline
9,983 across 28 types, and every baseline type count was met.

`canon validate` returned:

```json
{
  "status": "valid",
  "errors": [],
  "records": 10197
}
```

## Pushed-branch CI

The full CI workflow passed for `phase/cutover` at commit
`02c3b89cd734e6a935b4fcd528a1add39ab8ba8a`. All jobs passed, including
`test-canon`, `test-tuner`, `test-orchestra`, `types`, `checks`, `wheel`,
`e2e`, and `web`.

[GitHub Actions run 41163301107](https://github.com/andrewy1n/orchestra/actions/runs/41163301107)

The tuner-verdict workflow also passed at that commit:

[GitHub Actions run 41163301113](https://github.com/andrewy1n/orchestra/actions/runs/41163301113)
